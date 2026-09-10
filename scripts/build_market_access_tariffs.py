"""
Build current public crude-pipeline tariff data for the market-access hub layer.

The output is intentionally separate from market_access_pipelines.geojson so
tariff rows can be refreshed without rebuilding GIS linework.

Run:
    python scripts/build_market_access_tariffs.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "market_access_tariffs.json"
BBL_PER_M3 = 6.28981077


DOCS: dict[str, dict[str, Any]] = {
    "express_cer_204": {
        "document_name": "Express Canada Uncommitted Local Rates Tariff - CER No. 204",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-CAN-CER-204.pdf?hash=54D97272C347AB02AB423EDCB300E261&rev=56bb61598fba47fc91ac2b4cf18368d1",
        "issued": "2026-02-27", "effective": "2026-04-01", "status": "current",
    },
    "trans_mountain_123": {
        "document_name": "Trans Mountain Interim Tariff No. 123",
        "url": "https://docs.transmountain.com/Tolls-and-Tariffs/Interim-Tariff-No.-123.pdf",
        "issued": "2026-03-31", "effective": "2026-05-01", "status": "current",
    },
    "trans_mountain_puget_416": {
        "document_name": "Trans Mountain Pipeline (Puget Sound) LLC Local Tariff - FERC No. 4.16.0",
        "url": "https://docs.transmountain.com/Tolls-and-Tariffs/FERC-No.-4.16.0.pdf",
        "issued": "2026-05-29", "effective": "2026-07-01", "status": "current",
    },
}


HUBS: dict[str, dict[str, Any]] = {
    "edmonton": {"name": "Edmonton", "hub_type": "Origin / pipeline hub", "coordinates": [-113.49, 53.55]},
    "hardisty": {"name": "Hardisty", "hub_type": "Origin / terminal hub", "coordinates": [-111.31, 52.67]},
    "kerrobert": {"name": "Kerrobert", "hub_type": "Pipeline receipt point", "coordinates": [-109.13, 51.92]},
    "regina": {"name": "Regina", "hub_type": "Origin / refinery hub", "coordinates": [-104.62, 50.45]},
    "cromer": {"name": "Cromer", "hub_type": "Pipeline receipt point", "coordinates": [-101.24, 49.73]},
    "gretna": {"name": "Gretna", "hub_type": "Canada-U.S. border interconnect", "coordinates": [-97.56, 49.0]},
    "wild_horse": {"name": "Wild Horse", "hub_type": "Canada-U.S. border interconnect", "coordinates": [-110.0, 49.0]},
    "clearbrook": {"name": "Clearbrook", "hub_type": "Minnesota crude hub", "coordinates": [-95.43, 47.69]},
    "superior": {"name": "Superior", "hub_type": "Lakehead terminal / refinery market", "coordinates": [-92.10, 46.72]},
    "rapid_river": {"name": "Rapid River", "hub_type": "Lakehead delivery point", "coordinates": [-86.97, 45.93]},
    "lockport": {"name": "Lockport", "hub_type": "Chicago-area delivery point", "coordinates": [-88.05, 41.59]},
    "mokena": {"name": "Mokena", "hub_type": "Chicago-area delivery point", "coordinates": [-87.89, 41.53]},
    "flanagan": {"name": "Flanagan", "hub_type": "Midwest crude hub / interconnect", "coordinates": [-88.86, 40.88]},
    "griffith": {"name": "Griffith", "hub_type": "Indiana refinery market", "coordinates": [-87.43, 41.52]},
    "stockbridge": {"name": "Stockbridge", "hub_type": "Michigan delivery point", "coordinates": [-84.18, 42.45]},
    "marysville": {"name": "Marysville", "hub_type": "Michigan delivery point", "coordinates": [-82.49, 42.91]},
    "sarnia": {"name": "Sarnia / Corunna", "hub_type": "Ontario refinery / petrochemical market", "coordinates": [-82.39, 42.98]},
    "westover": {"name": "Westover", "hub_type": "Ontario pipeline hub", "coordinates": [-80.05, 43.32]},
    "nanticoke": {"name": "Nanticoke", "hub_type": "Ontario refinery market", "coordinates": [-80.08, 42.80]},
    "cushing": {"name": "Cushing", "hub_type": "U.S. crude hub", "coordinates": [-96.77, 35.99]},
    "seaway_freeport": {"name": "Seaway Freeport", "hub_type": "Gulf Coast crude terminal", "coordinates": [-95.35, 28.95]},
    "sweeny": {"name": "Sweeny", "hub_type": "Gulf Coast refinery market", "coordinates": [-95.70, 29.04]},
    "echo": {"name": "ECHO / Houston", "hub_type": "Gulf Coast crude hub", "coordinates": [-95.20, 29.72]},
    "beaumont_port_arthur": {"name": "Beaumont / Port Arthur", "hub_type": "Gulf Coast refinery market", "coordinates": [-93.94, 29.90]},
    "port_arthur": {"name": "Port Arthur", "hub_type": "Gulf Coast refinery market", "coordinates": [-93.94, 29.88]},
    "houston": {"name": "Houston", "hub_type": "Gulf Coast crude hub", "coordinates": [-95.37, 29.76]},
    "kamloops": {"name": "Kamloops", "hub_type": "Trans Mountain delivery point", "coordinates": [-120.33, 50.67]},
    "sumas": {"name": "Sumas", "hub_type": "Border / Puget Sound interconnect", "coordinates": [-122.27, 49.0]},
    "burnaby_westridge": {"name": "Burnaby / Westridge", "hub_type": "Marine terminal / refinery market", "coordinates": [-122.95, 49.25]},
    "ferndale_cherry_point": {"name": "Ferndale / Cherry Point", "hub_type": "Washington refinery market", "coordinates": [-122.69, 48.86]},
    "anacortes": {"name": "Anacortes", "hub_type": "Washington refinery market", "coordinates": [-122.61, 48.51]},
    "casper": {"name": "Casper", "hub_type": "Pipeline hub / refinery market", "coordinates": [-106.31, 42.85]},
    "guernsey": {"name": "Guernsey", "hub_type": "Pipeline hub", "coordinates": [-104.74, 42.27]},
    "buffalo_station": {"name": "Buffalo Station", "hub_type": "Express / Platte delivery point", "coordinates": [-108.67, 47.01]},
    "edgar_station": {"name": "Edgar Station", "hub_type": "Express delivery point", "coordinates": [-108.85, 45.46]},
    "sinclair_casper": {"name": "Sinclair Pipeline Casper", "hub_type": "Express delivery point", "coordinates": [-106.34, 42.83]},
    "holdrege": {"name": "Holdrege", "hub_type": "Platte delivery point", "coordinates": [-99.37, 40.44]},
    "key_station": {"name": "Key Station", "hub_type": "Platte delivery point", "coordinates": [-92.94, 39.43]},
    "wood_river": {"name": "Wood River", "hub_type": "Midwest refinery market", "coordinates": [-90.20, 38.86]},
    "patoka": {"name": "Patoka", "hub_type": "Midwest crude hub", "coordinates": [-89.09, 38.75]},
}


HUB_ALIASES = {
    "burnaby / westridge": "burnaby_westridge",
    "sarnia": "sarnia",
    "sarnia / corunna": "sarnia",
}


def per_bbl(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / BBL_PER_M3, 4)


def doc_link(doc_id: str, pdf_page: int) -> str:
    return f"{DOCS[doc_id]['url']}#page={pdf_page}"


def source_label(doc_id: str, pdf_page: int) -> str:
    return f"PDF p. {pdf_page} - {DOCS[doc_id]['document_name']}"


def cost_item(
    doc_id: str,
    pdf_page: int,
    name: str,
    value: float | None = None,
    currency: str | None = None,
    unit: str | None = None,
    *,
    text: str | None = None,
    included_in_total: bool = False,
    default_additive: bool = False,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": name,
        "source_url": doc_link(doc_id, pdf_page),
        "source_label": source_label(doc_id, pdf_page),
    }
    if value is not None:
        item["value"] = value
        item["currency"] = currency
        item["unit"] = unit
        item["value_per_bbl"] = per_bbl(value) if unit == "m3" else value
    if text:
        item["text"] = text
    if included_in_total:
        item["included_in_total"] = True
    if default_additive:
        item["default_additive"] = True
    return item


def add_default_adders_total(
    total: float | None,
    currency: str | None,
    unit: str,
    additional_costs: list[dict[str, Any]] | None,
) -> float | None:
    if not NumberLike.is_finite(total):
        return None
    amount = float(total)
    found = False
    for item in additional_costs or []:
        if (
            item.get("default_additive")
            and item.get("currency") == currency
            and item.get("unit") == unit
            and NumberLike.is_finite(item.get("value"))
        ):
            amount += float(item["value"])
            found = True
    return round(amount, 4) if found else None


class NumberLike:
    @staticmethod
    def is_finite(value: Any) -> bool:
        return isinstance(value, (int, float)) and value == value and value not in (float("inf"), float("-inf"))


def add_rate(
    rows: list[dict[str, Any]],
    *,
    pipeline: str,
    route_id: str,
    origin: str,
    destination: str,
    product: str,
    service: str,
    rate_type: str,
    doc_id: str,
    pdf_page: int,
    table: str,
    currency: str | None = None,
    unit: str = "m3",
    total: float | None = None,
    fixed: float | None = None,
    variable: float | None = None,
    cad_component_m3: float | None = None,
    usd_component_m3: float | None = None,
    issued_override: str | None = None,
    effective_override: str | None = None,
    status_override: str | None = None,
    notes: str | None = None,
    base_before_included_costs: float | None = None,
    included_costs: list[dict[str, Any]] | None = None,
    additional_costs: list[dict[str, Any]] | None = None,
    conditional_charges: list[str] | None = None,
    variable_components: list[dict[str, Any]] | None = None,
    loss_allowance_percent: float | None = None,
) -> None:
    doc = DOCS[doc_id]
    total_with_default_adders = add_default_adders_total(total, currency, unit, additional_costs)
    row: dict[str, Any] = {
        "pipeline": pipeline,
        "route_id": route_id,
        "origin_hub_id": origin,
        "destination_hub_id": destination,
        "origin": HUBS[origin]["name"],
        "destination": HUBS[destination]["name"],
        "product": product,
        "service": service,
        "rate_type": rate_type,
        "currency": currency,
        "unit": unit,
        "total": total,
        "fixed": fixed,
        "variable": variable,
        "total_per_bbl": per_bbl(total) if unit == "m3" else total,
        "fixed_per_bbl": per_bbl(fixed) if unit == "m3" else fixed,
        "variable_per_bbl": per_bbl(variable) if unit == "m3" else variable,
        "base_before_included_costs": base_before_included_costs,
        "base_before_included_costs_per_bbl": per_bbl(base_before_included_costs) if unit == "m3" else base_before_included_costs,
        "total_with_default_adders": total_with_default_adders,
        "total_with_default_adders_per_bbl": per_bbl(total_with_default_adders) if unit == "m3" else total_with_default_adders,
        "cad_component_m3": cad_component_m3,
        "usd_component_m3": usd_component_m3,
        "cad_component_per_bbl": per_bbl(cad_component_m3),
        "usd_component_per_bbl": per_bbl(usd_component_m3),
        "document_id": doc_id,
        "document_name": doc["document_name"],
        "document_page": f"PDF p. {pdf_page}",
        "source_label": source_label(doc_id, pdf_page),
        "table": table,
        "source_url": doc_link(doc_id, pdf_page),
        "issued": issued_override or doc["issued"],
        "effective": effective_override or doc["effective"],
        "status": status_override or doc["status"],
    }
    if notes:
        row["notes"] = notes
    if included_costs:
        row["included_costs"] = included_costs
    if additional_costs:
        row["additional_costs"] = additional_costs
    if conditional_charges:
        row["conditional_charges"] = conditional_charges
    if variable_components:
        row["variable_components"] = variable_components
    if loss_allowance_percent is not None:
        row["loss_allowance_percent"] = loss_allowance_percent
    rows.append(row)


def add_trans_mountain(rows: list[dict[str, Any]]) -> None:
    def tm_components(values: list[tuple[str, float]]) -> list[dict[str, Any]]:
        return [
            cost_item("trans_mountain_123", 9, name, value, "CAD", "m3", included_in_total=True)
            for name, value in values
        ]

    tm_variable_components = {
        ("kamloops", "Light crude / refined petroleum"): tm_components([
            ("Power", 1.6149),
            ("Fiber optic leak detection", 0.3333),
            ("Pipeline reclamation surcharge", 0.3457),
            ("First Nations consultation and accommodation", 0.6181),
            ("GHG offset costs", 0.0375),
            ("Revenue sharing", -0.6590),
            ("Variable toll true-up", -0.1357),
        ]),
        ("sumas", "Light crude / refined petroleum"): tm_components([
            ("Power", 2.1603),
            ("Fiber optic leak detection", 0.4458),
            ("Pipeline reclamation surcharge", 0.4625),
            ("First Nations consultation and accommodation", 0.8268),
            ("GHG offset costs", 0.0501),
            ("Revenue sharing", -0.8816),
            ("Variable toll true-up", -0.1815),
        ]),
        ("sumas", "Heavy crude"): tm_components([
            ("Power", 2.5923),
            ("Fiber optic leak detection", 0.4458),
            ("Pipeline reclamation surcharge", 0.4625),
            ("First Nations consultation and accommodation", 0.8268),
            ("GHG offset costs", 0.0501),
            ("Revenue sharing", -0.8816),
            ("Variable toll true-up", -0.1815),
        ]),
        ("burnaby_westridge", "Light crude / refined petroleum to Burnaby"): tm_components([
            ("Power", 2.2653),
            ("Fiber optic leak detection", 0.4675),
            ("Pipeline reclamation surcharge", 0.4849),
            ("First Nations consultation and accommodation", 0.8670),
            ("GHG offset costs", 0.0525),
            ("Revenue sharing", -0.9244),
            ("Variable toll true-up", -0.1903),
        ]),
        ("burnaby_westridge", "Light crude to Westridge"): tm_components([
            ("Power", 2.2733),
            ("Fiber optic leak detection", 0.4692),
            ("Pipeline reclamation surcharge", 0.4866),
            ("Enhanced response regime fee", 1.6396),
            ("First Nations consultation and accommodation", 0.8701),
            ("GHG offset costs", 0.0527),
            ("Revenue sharing", -0.9277),
            ("Variable toll true-up", -0.1910),
        ]),
        ("burnaby_westridge", "Heavy crude to Westridge"): tm_components([
            ("Power", 2.7280),
            ("Fiber optic leak detection", 0.4692),
            ("Pipeline reclamation surcharge", 0.4866),
            ("Enhanced response regime fee", 1.6396),
            ("First Nations consultation and accommodation", 0.8701),
            ("GHG offset costs", 0.0527),
            ("Revenue sharing", -0.9277),
            ("Variable toll true-up", -0.1910),
        ]),
    }
    tm_direct_injection = "Direct injection deliveries receive a CAD 0.8177/m3 toll adjustment where applicable.";
    tm_common_conditions = [
        tm_direct_injection,
        "Loss allowance is 0.00%.",
        "Westridge marine loadings are subject to separate charges such as dock bid premium during apportionment, WCMRC fees, VFPA Gateway Infrastructure Fee 2, and WCMRC capital asset and loan fees.",
    ]
    tm_services = [
        (
            "Uncommitted",
            2,
            {
                "kamloops": [("Light crude / refined petroleum", 58.5625, 56.4078, 2.1547)],
                "sumas": [("Light crude / refined petroleum", 78.4078, 75.5254, 2.8824), ("Heavy crude", 78.8399, 75.5254, 3.3144)],
                "burnaby_westridge": [("Light crude / refined petroleum to Burnaby", 82.1098, 79.0873, 3.0225), ("Light crude to Westridge", 87.9761, 83.3033, 4.6728), ("Heavy crude to Westridge", 88.4308, 83.3033, 5.1274)],
            },
        ),
        (
            "Committed firm - 15 years, <75,000 bbl/d",
            3,
            {
                "kamloops": [("Light crude / refined petroleum", 53.4346, 51.2799, 2.1547)],
                "sumas": [("Light crude / refined petroleum", 71.5419, 68.6595, 2.8824), ("Heavy crude", 71.9739, 68.6595, 3.3144)],
                "burnaby_westridge": [("Light crude / refined petroleum to Burnaby", 74.9200, 71.8975, 3.0225), ("Light crude to Westridge", 80.4031, 75.7303, 4.6728), ("Heavy crude to Westridge", 80.8577, 75.7303, 5.1274)],
            },
        ),
        (
            "Committed firm - 15 years, >=75,000 bbl/d",
            4,
            {
                "kamloops": [("Light crude / refined petroleum", 49.5886, 47.4339, 2.1547)],
                "sumas": [("Light crude / refined petroleum", 66.3924, 63.5100, 2.8824), ("Heavy crude", 66.8245, 63.5100, 3.3144)],
                "burnaby_westridge": [("Light crude / refined petroleum to Burnaby", 69.5277, 66.5052, 3.0225), ("Light crude to Westridge", 74.7233, 70.0505, 4.6728), ("Heavy crude to Westridge", 75.1780, 70.0505, 5.1274)],
            },
        ),
        (
            "Committed firm - 20 years, <75,000 bbl/d",
            5,
            {
                "kamloops": [("Light crude / refined petroleum", 48.3066, 46.1519, 2.1547)],
                "sumas": [("Light crude / refined petroleum", 64.6759, 61.7935, 2.8824), ("Heavy crude", 65.1080, 61.7935, 3.3144)],
                "burnaby_westridge": [("Light crude / refined petroleum to Burnaby", 67.7302, 64.7078, 3.0225), ("Light crude to Westridge", 72.8300, 68.1573, 4.6728), ("Heavy crude to Westridge", 73.2847, 68.1573, 5.1274)],
            },
        ),
        (
            "Committed firm - 20 years, >=75,000 bbl/d",
            6,
            {
                "kamloops": [("Light crude / refined petroleum", 44.8452, 42.6905, 2.1547)],
                "sumas": [("Light crude / refined petroleum", 60.0414, 57.1590, 2.8824), ("Heavy crude", 60.4735, 57.1590, 3.3144)],
                "burnaby_westridge": [("Light crude / refined petroleum to Burnaby", 62.8772, 59.8547, 3.0225), ("Light crude to Westridge", 67.7182, 63.0454, 4.6728), ("Heavy crude to Westridge", 68.1729, 63.0454, 5.1274)],
            },
        ),
    ]
    for service, pdf_page, by_destination in tm_services:
        for destination, product_rows in by_destination.items():
            for product, total, fixed, variable in product_rows:
                add_rate(
                    rows,
                    pipeline="Trans Mountain",
                    route_id="trans-mountain-puget",
                    origin="edmonton",
                    destination=destination,
                    product=product,
                    service=service,
                    rate_type="fixed + variable",
                    currency="CAD",
                    unit="m3",
                    total=total,
                    fixed=fixed,
                    variable=variable,
                    doc_id="trans_mountain_123",
                    pdf_page=pdf_page,
                    table="Total tolls, fixed tolls, and variable tolls",
                    notes="Total toll is the published fixed toll plus variable toll; variable component details are from Section III.",
                    included_costs=tm_variable_components.get((destination, product)),
                    conditional_charges=tm_common_conditions,
                    loss_allowance_percent=0.0,
                )

    for destination in ["anacortes", "ferndale_cherry_point"]:
        add_rate(
            rows,
            pipeline="Trans Mountain Puget Sound",
            route_id="trans-mountain-puget",
            origin="sumas",
            destination=destination,
            product="Petroleum / crude / condensate",
            service="Local rate",
            rate_type="local total",
            currency="USD",
            unit="bbl",
            total=0.5729,
            doc_id="trans_mountain_puget_416",
            pdf_page=2,
            table="Transportation rate from Sumas to Anacortes and Ferndale",
            notes="Tariff publishes 57.29 U.S. cents per barrel.",
            additional_costs=[
                cost_item(
                    "trans_mountain_puget_416",
                    2,
                    "Demurrage",
                    0.0042,
                    "USD",
                    "bbl",
                    text="0.42 U.S. cents/bbl for each 24 hours or part thereof where applicable.",
                )
            ],
        )


def build_tariffs() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    snapshot = json.loads((ROOT / "data" / "market_access_tariff_snapshot.json").read_text(encoding="utf-8"))
    DOCS.update(snapshot["documents"])
    for spec in snapshot["rates"]:
        add_rate(rows, **spec)
    add_express_local(rows)
    add_trans_mountain(rows)
    for doc in DOCS.values():
        doc["last_verified"] = snapshot["last_verified"]
    for row in rows:
        row["last_verified"] = snapshot["last_verified"]

    validate_tariffs(rows)

    return {
        "metadata": {
            "name": "Market Access Tariffs",
            "description": "Operator-published tariff snapshot, verified September 2026. Effective rates and currencies are preserved; contract eligibility and conditional charges still apply.",
            "generated_with": "scripts/build_market_access_tariffs.py",
            "generated_on": date.today().isoformat(),
            "last_verified": snapshot["last_verified"],
            "next_known_change": "2026-10-01",
            "freshness_note": "Enbridge has published October 1, 2026 replacements (CER 10, 11 and 12). These future rates are not used in this September snapshot. Rebuilding alone does not re-verify tariffs.",
            "unit_notes": [
                "m3 rates are also converted to per-bbl using 1 m3 = 6.28981077 bbl.",
                "Rows with mixed currency preserve the operator-published CAD and USD components instead of applying a live FX conversion.",
                "Only the filings effective on the September 2026 verification date are included. No cancelled Express 5-9 year table or future October Mainline rate is presented as current.",
            ],
        },
        "documents": DOCS,
        "hubs": HUBS,
        "hub_aliases": HUB_ALIASES,
        "tariffs": rows,
    }


def validate_tariffs(rows: list[dict[str, Any]]) -> None:
    """Reject broken source links, missing values and double-counted components."""
    ids: set[tuple] = set()
    for row in rows:
        key = tuple(row[k] for k in ("document_id", "origin_hub_id", "destination_hub_id", "product", "service"))
        if key in ids:
            raise ValueError(f"Duplicate tariff: {key}")
        ids.add(key)
        if row["origin_hub_id"] not in HUBS or row["destination_hub_id"] not in HUBS:
            raise ValueError(f"Unknown tariff hub: {key}")
        if row.get("currency") == "mixed":
            if not all(NumberLike.is_finite(row.get(key)) for key in ("cad_component_m3", "usd_component_m3")):
                raise ValueError(f"Missing currency component: {key}")
        elif not NumberLike.is_finite(row.get("total")):
            raise ValueError(f"Missing tariff total: {key}")
        if row.get("fixed") is not None and abs(row["fixed"] + row["variable"] - row["total"]) > 0.00011:
            raise ValueError(f"Fixed and variable toll do not reconcile: {key}")


def add_express_local(rows: list[dict[str, Any]]) -> None:
    for product, value in [("Light crude", 5.0384), ("Medium crude", 5.4414), ("Heavy crude", 6.1467), ("Super-heavy crude", 6.3986)]:
        for destination, total in [("hardisty", 0.3096), ("wild_horse", value)]:
            add_rate(rows, pipeline="Express Canada", route_id="express-platte", origin="hardisty",
                     destination=destination, product=product, service="Uncommitted local rate",
                     rate_type="uncommitted local total", currency="USD", unit="m3", total=total,
                     doc_id="express_cer_204", pdf_page=2, table="Uncommitted local rates",
                     additional_costs=[cost_item("express_cer_204", 2, "Abandonment surcharge", 0.05, "USD", "m3", default_additive=True)] if destination == "wild_horse" else None)


def main() -> int:
    data = build_tariffs()
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEFAULT_OUTPUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=True, allow_nan=False), encoding="utf-8")
    temporary.replace(DEFAULT_OUTPUT)
    print(f"Wrote {len(data['tariffs'])} tariff rows to {DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
