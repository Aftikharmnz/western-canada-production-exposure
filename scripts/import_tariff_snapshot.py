"""Import the specifically reviewed September 2026 operator tariff PDFs.

This importer is deliberately versioned: a new filing requires review of tables,
units, footnotes and effective dates before adding it to the app. Install
pdfplumber, then run with --pdf-dir pointing to the eight named PDFs below.
The normal app builder reads the checked-in snapshot and needs no PDF packages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "market_access_tariff_snapshot.json"
VERIFIED = "2026-09-10"
DOCS = {
    "enbridge4": ("Enbridge Canadian Mainline Local Tolls - CER No. 4", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/CDMN-CER-4.pdf", "2026-07-02", "2026-07-02"),
    "enbridge5": ("Enbridge Canadian Mainline / Lakehead International Joint Rates - CER No. 5 / FERC No. 45.48.0", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/CDMN-CER-5-FERC-45480-LKH.pdf", "2026-07-02", "2026-07-02"),
    "enbridge6": ("Enbridge Mainline / Lakehead / Flanagan South - CER No. 6 / FERC No. 3.59.0", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/FSP-CER-6-FERC-3590.pdf", "2026-07-02", "2026-07-02"),
    "enbridge9": ("Enbridge Mainline / Lakehead / Spearhead - CER No. 9 / FERC No. 46.2.1", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/CCPS-FERC-4621-CER-9.pdf", "2026-07-30", "2026-08-01"),
    "keystone84": ("South Bow Keystone International Joint Rates - CER No. 84 / FERC No. 7.44.0", "https://www.southbow.com/wp-content/uploads/2026/07/CER-No.-84-South-Bow-IJT-Rates-Tariff.pdf", "2026-07-30", "2026-09-01"),
    "express205": ("Express Canada Term Rate Tariff - CER No. 205", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-CAN-CER-205.pdf", "2026-05-27", "2026-07-01"),
    "express207": ("Express / Platte International Joint Term Rates - CER No. 207 / FERC No. 167.33.1", "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-CAN-CER-207-FERC-167331.pdf", "2026-06-19", "2026-07-01"),
}
ORIGINS = ["edmonton", "hardisty", "kerrobert", "regina", "cromer"]
PRODUCTS = ["Light crude", "Medium crude", "Heavy crude"]
DESTINATIONS = {
    "Clearbrook": "clearbrook", "Superior": "superior", "Lockport": "lockport",
    "Mokena": "mokena", "Flanagan": "flanagan", "Griffith": "griffith",
    "Stockbridge": "stockbridge", "Rapid River": "rapid_river", "Marysville": "marysville",
    "Corunna": "sarnia", "Westover": "westover", "Nanticoke": "nanticoke",
    "Buffalo Station": "buffalo_station", "Edgar Station": "edgar_station",
    "Sinclair": "sinclair_casper", "Casper": "casper", "Guernsey": "guernsey",
    "Holdrege": "holdrege", "Key Station": "key_station", "Wood River": "wood_river",
}


def number(value):
    clean = re.sub(r"\[[A-Z]\]", "", str(value or "")).replace("$", "").replace("*", "")
    clean = re.sub(r"\s+", "", clean)
    if clean in ("", "-", "N/A"):
        return None
    if not re.fullmatch(r"-?\d+\.\d+", clean):
        raise ValueError(f"Unrecognized numeric tariff cell: {value!r}")
    return float(clean)


def destination(value):
    clean = " ".join(str(value or "").split())
    return next((key for prefix, key in DESTINATIONS.items() if clean.startswith(prefix)), None)


def import_snapshot(pdf_dir: Path):
    import pdfplumber

    docs = {}
    pdfs = {}
    for key, (name, url, issued, effective) in DOCS.items():
        path = pdf_dir / f"{key}.pdf"
        docs[key] = dict(document_name=name, url=url, issued=issued, effective=effective,
                         status="current", last_verified=VERIFIED,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        pdfs[key] = pdfplumber.open(path)
    rows = []

    def charge(doc, page, name, value, currency="USD", unit="bbl", included=False):
        item = dict(name=name, value=value, currency=currency, unit=unit,
                    source_url=docs[doc]["url"] + f"#page={page}",
                    source_label=f"PDF p. {page} - {docs[doc]['document_name']}")
        item["included_in_total" if included else "default_additive"] = True
        item["value_per_bbl"] = round(value / 6.28981077, 4) if unit == "m3" else value
        return item

    def add(doc, page, pipeline, route, origin, dest, product, service, value=None, **kw):
        spec = dict(doc_id=doc, pdf_page=page, pipeline=pipeline, route_id=route,
                    origin=origin, destination=dest, product=product, service=service,
                    rate_type="total", currency="USD", unit="bbl", table=service)
        if value is not None:
            spec["total"] = value
        spec.update(kw)
        rows.append(spec)

    # Mainline direct Canadian local tolls. Column order is the original PDF's
    # FROM header, not the left-hand TO column (both are present in this tariff).
    for page, index, product, origins in [
        (3, 0, "Light crude", ORIGINS),
        (3, 1, "Medium crude", ["edmonton", "hardisty", "cromer"]),
        (4, 0, "Heavy crude", ORIGINS),
    ]:
        table = pdfs["enbridge4"].pages[page-1].extract_tables()[index]
        row = next(r for r in table if str(r[0]).startswith("International Boundary near Gretna"))
        for origin, cell in zip(origins, row[1:]):
            add("enbridge4", page, "Enbridge Canadian Mainline", "enbridge-mainline-lakehead",
                origin, "gretna", product, "Local toll to International Boundary near Gretna", number(cell),
                currency="CAD", unit="m3", loss_allowance_percent=0.05)

    # CER 5 bills separate Canadian and U.S. dollar components. Do not recreate
    # the superseded April filing's illustrative USD total or assume a live FX.
    for page in range(3, 7):
        table = pdfs["enbridge5"].pages[page-1].extract_tables()[0]
        products = ["NGL", "Condensate", "Light crude"] if page in (3, 5) else PRODUCTS[1:]
        origin = None
        for row in table:
            dest = destination(row[1])
            if not dest:
                continue
            if row[0]:
                origin = next(o for o in ORIGINS if o in row[0].lower())
            for i, product in enumerate(products):
                cad, usd = number(row[2 + 2*i]), number(row[3 + 2*i])
                if cad is None and usd is None:
                    continue
                if cad is None or usd is None:
                    raise ValueError("Incomplete currency pair")
                add("enbridge5", page, "Enbridge Mainline / Lakehead", "enbridge-mainline-lakehead",
                    origin, dest, product, "International joint rate", currency="mixed", unit="m3",
                    rate_type="component", cad_component_m3=cad, usd_component_m3=usd,
                    notes="CAD and USD components are invoiced separately. Published components include the listed regulatory surcharges and credits; see PDF p. 7.")

    # Flanagan South committed tables, plus separately assessed power charge.
    gulf = ["seaway_freeport", "sweeny", "echo", "beaumont_port_arthur"]
    power = charge("enbridge6", 8, "Flanagan South power charge", 0.5200)
    for page in range(4, 8):
        for table in pdfs["enbridge6"].pages[page-1].extract_tables():
            header = table[0][0]
            product = next(p for p in PRODUCTS if p.split()[0].upper() + " CRUDE" in header)
            season = header[:3]
            for row in table[3:]:
                if not re.match(r"\d+ Years", str(row[0])):
                    continue
                service = f"{season} Open Season committed - {row[0]}, {row[1]} bbl/d"
                for origin, cell in zip(ORIGINS, row[2:]):
                    value = number(cell)
                    if value is None:
                        continue
                    for dest in gulf:
                        add("enbridge6", page, "Enbridge Mainline / Lakehead / Flanagan South", "enbridge-us-downstream",
                            origin, dest, product, service, value, additional_costs=[power],
                            conditional_charges=["Contract eligibility, tankage and loss allowances follow the tariff rules. Power is assessed separately; no second abandonment surcharge is added to this published total."])
    table = pdfs["enbridge6"].pages[7].extract_tables()[0]
    for row in table[3:]:
        for origin, cell in zip(ORIGINS, row[1:]):
            value = number(cell)
            if value is not None:
                for dest in gulf:
                    add("enbridge6", 8, "Enbridge Mainline / Lakehead / Flanagan South", "enbridge-us-downstream",
                        origin, dest, row[0].lower().capitalize(), "Uncommitted international joint rate", value,
                        additional_costs=[power], conditional_charges=["Applicable tankage and loss allowances follow tariff rules; power is assessed separately."])

    # Spearhead Appendix A includes the adders for every contract class, not just
    # uncommitted movements. Retain base and included costs without double adding.
    for table in pdfs["enbridge9"].pages[7].extract_tables():
        service = table[0][0].split("\n")[-1]
        columns = [str(c).split("\n") for c in table[4]]
        if not all(len(c) == 5 for c in columns):
            raise ValueError("Unexpected Spearhead worksheet layout")
        for i, origin in enumerate(ORIGINS):
            included = [charge("enbridge9", 8, name, number(columns[j][i]), included=True)
                        for j, name in [(4, "Abandonment surcharge"), (5, "Non-performance penalty credit"), (6, "MPUC surcharge")]]
            for j, product in enumerate(PRODUCTS, 1):
                base, total = number(columns[j][i]), number(columns[j+6][i])
                if base is None:
                    continue
                if abs(base + sum(c["value"] for c in included) - total) > 0.00011:
                    raise ValueError("Spearhead published total does not reconcile")
                add("enbridge9", 8, "Enbridge Mainline / Lakehead / Spearhead", "enbridge-us-downstream",
                    origin, "cushing", product, service, total, base_before_included_costs=base,
                    included_costs=included, notes="Published Appendix A total includes the three listed surcharges/credits.",
                    conditional_charges=["Committed rates require the relevant 2026 Re-Contracting Open Season agreement; firm service applies during prorationing. Cushing tankage may be assessed separately."])

    # Keystone PDF has two cover-letter pages ahead of tariff pages 1 and 2.
    for dest in ["wood_river", "patoka", "cushing", "port_arthur", "houston"]:
        for product, value in zip(["Light crude", "Heavy crude"], [8.096, 8.800] if dest in ("port_arthur", "houston") else [6.210, 6.750]):
            add("keystone84", 4, "Keystone", "keystone", "hardisty", dest, product,
                "International joint uncommitted rate", value,
                additional_costs=[charge("keystone84", 4, "Abandonment surcharge", 0.042, currency="CAD")],
                conditional_charges=["Sour Lake interconnect deliveries incur USD 0.9286/m3 (USD 0.1476/bbl) where applicable.",
                                     "The CAD abandonment charge is separate from the USD transportation rate; no FX conversion is assumed."])

    express_adders = [charge("express207", 10, "Abandonment surcharge", 0.05, unit="m3")]
    express_conditions = ["Contract term, volume and open-season eligibility follow the source tariff.",
                          "Buffalo and Wood River discounts apply only when their tariff conditions are met.",
                          "Re-origination may add USD 1.4626/m3. Loss allowances follow carrier rules."]
    add("express205", 2, "Express Canada", "express-platte", "hardisty", "wild_horse", "Petroleum",
        "Committed local term rate - 10 or more years", 7.9457, unit="m3",
        additional_costs=[charge("express205", 2, "Abandonment surcharge", 0.05, unit="m3")])
    # Page 2 explicitly cancels the former 5-9 year rate table; never import it.
    for page in range(3, 10):
        for table in pdfs["express207"].pages[page-1].extract_tables():
            if "TABLE" not in str(table[0][0]):
                continue
            header = " ".join(table[0][0].split())
            term = re.search(r"For (.+?) Year Term", header)
            years = term.group(1) if term else "10"
            season = "2019 Re-contracting" if page == 6 else "2019 Expansion" if page == 7 else "2024 Open Season" if page == 8 and len(table[1]) == 5 else "2025 Open Season" if page >= 8 else "2013/2016 Open Seasons"
            service = f"Committed international joint rate - {season}, {years} years"
            held_value = None
            for row in table[2:]:
                dest = destination(row[1]) if len(row) > 1 else None
                if not dest:
                    continue
                if page in (3, 4, 5):
                    products, cells = PRODUCTS + ["Super-heavy crude"], row[3:]
                elif page == 8 and len(row) == 5:
                    products, cells = ["Light crude / medium crude", "Heavy crude / super-heavy crude"], row[3:]
                else:
                    products, cells = ["Petroleum"], row[-1:]
                for product, cell in zip(products, cells):
                    value = number(cell)
                    if page == 6:  # one merged toll covers all four destinations
                        held_value = value if value is not None else held_value
                        value = held_value
                    if value is None:
                        raise ValueError(f"Missing Express rate: p.{page} {dest}")
                    add("express207", page, "Express / Platte", "express-platte", "hardisty", dest,
                        product, service, value, unit="m3", additional_costs=express_adders,
                        conditional_charges=express_conditions)

    for pdf in pdfs.values():
        pdf.close()
    from collections import Counter
    counts = Counter(r["doc_id"] for r in rows)
    expected = {"enbridge4": 13, "enbridge5": 163, "enbridge6": 476, "enbridge9": 78,
                "keystone84": 10, "express205": 1, "express207": 112}
    if dict(counts) != expected:
        raise ValueError(f"Tariff table cardinalities changed: {dict(counts)} != {expected}")
    print(f"Imported tariff table counts: {dict(counts)}")
    return dict(last_verified=VERIFIED, documents=docs, rates=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    snapshot = import_snapshot(args.pdf_dir)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
