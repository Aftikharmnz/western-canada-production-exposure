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
    "enbridge_cer_596": {
        "document_name": "Enbridge Canadian Mainline / Lakehead International Joint Rate Tariff - CER No. 596 / FERC No. 45.46.0",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/CDMN-CER-596-FERC-45460-LKH.pdf?hash=A73AABCEBA8269DC7209365E9328BD81&rev=bb5e943279d6455fb0f5b6740422751e",
        "issued": "2026-03-11",
        "effective": "2026-04-01",
        "status": "current",
    },
    "enbridge_cer_599": {
        "document_name": "Enbridge Canadian Mainline / Lakehead / Spearhead International Joint Rate Tariff - CER No. 599 / FERC No. 46.1.0",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/CCPS-FERC-4610-CER-599-EPI-LKHD.pdf?hash=1A6430E0745AAC7081BE45B74887793E&rev=733a6970af6842aa95f92efcda2a8ebc",
        "issued": "2026-05-01",
        "effective": "2026-06-01",
        "status": "pending-effective-forward-use",
    },
    "enbridge_cer_597": {
        "document_name": "Enbridge Canadian Mainline / Lakehead / Flanagan South International Joint Rate Tariff - CER No. 597 / FERC No. 3.57.0",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/FSP-CER-597-CDMN.pdf?hash=5348806DC6D9DB27A3A6B028E5DE2F0C&rev=d287406a0f2a42828230f93e6507a80d",
        "issued": "2026-03-26",
        "effective": "2026-04-01",
        "status": "current",
    },
    "keystone_cer_71": {
        "document_name": "Keystone International Joint Rate Tariff - CER No. 71 / FERC No. 7.37.0",
        "url": "https://www.tcenergy.com/siteassets/pdfs/oils-and-liquids/keystone-shipper-info/ferc/tce-Keystone-FERC-7.37.0-IJT-Rate-Schedule.pdf",
        "issued": "2024-09-25",
        "effective": "2024-10-01",
        "status": "current",
    },
    "express_cer_204": {
        "document_name": "Express Canada Uncommitted Local Rates Tariff - CER No. 204",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-CAN-CER-204.pdf?hash=54D97272C347AB02AB423EDCB300E261&rev=56bb61598fba47fc91ac2b4cf18368d1",
        "issued": "2026-02-27",
        "effective": "2026-04-01",
        "status": "current",
    },
    "express_cer_202": {
        "document_name": "Express Canada Term Rate Tariff - CER No. 202",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-CAN-CER-202.pdf?hash=9B87497D240D726795F1B1E352572D66&rev=745f1f59de64488cbad4c82ff1910f13",
        "issued": "2025-12-01",
        "effective": "2026-01-01",
        "status": "current",
    },
    "express_cer_203": {
        "document_name": "Express Canada / Express US / Platte Committed International Joint Rates - CER No. 203 / FERC No. 167.32.0",
        "url": "https://www.enbridge.com/~/media/Enb/Documents/Tariffs/2026/EXP-US-CER-203-EXP-CAN-FERC-16732-PLT.pdf?hash=12063B8A253AAC8B16786250D5DC4141&rev=abcd00be578f4717b8fae1d51adc05ae",
        "issued": "2025-12-01",
        "effective": "2026-01-01",
        "status": "current",
    },
    "trans_mountain_123": {
        "document_name": "Trans Mountain Interim Tariff No. 123",
        "url": "https://docs.transmountain.com/Tolls-and-Tariffs/Interim-Tariff-No.-123.pdf",
        "issued": "2026-03-31",
        "effective": "2026-05-01",
        "status": "current",
    },
    "trans_mountain_puget_415": {
        "document_name": "Trans Mountain Pipeline (Puget Sound) LLC Local Tariff - FERC No. 4.15.0",
        "url": "https://docs.transmountain.com/Tolls-and-Tariffs/FERC-No.-4.15.0.pdf",
        "issued": "2025-05-29",
        "effective": "2025-07-01",
        "status": "current",
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


def add_enbridge_596(rows: list[dict[str, Any]]) -> None:
    total_specs = [
        (
            "Condensate",
            11,
            [
                ("edmonton", [("clearbrook", 13.3299), ("superior", 15.5801), ("rapid_river", 22.4237), ("lockport", 23.0315), ("mokena", 25.8174), ("flanagan", 25.2493), ("griffith", 26.5338), ("stockbridge", 26.9504), ("marysville", 28.7327), ("sarnia", 28.4349), ("westover", 28.7668), ("nanticoke", 29.4847)]),
                ("hardisty", [("clearbrook", 13.0279), ("superior", 15.2781), ("rapid_river", 22.1217), ("lockport", 22.7295), ("mokena", 25.5154), ("flanagan", 24.9473), ("griffith", 26.2318), ("stockbridge", 26.6484), ("marysville", 28.4307), ("sarnia", 28.1329), ("westover", 28.4648), ("nanticoke", 29.1827)]),
                ("kerrobert", [("clearbrook", 12.4627), ("superior", 14.7129), ("rapid_river", 21.5565), ("lockport", 22.1643), ("mokena", 24.9502), ("flanagan", 24.3821), ("griffith", 25.6666), ("stockbridge", 26.0832), ("marysville", 27.8655), ("sarnia", 27.5677), ("westover", 27.8996), ("nanticoke", 28.6175)]),
                ("regina", [("clearbrook", 11.8898), ("superior", 14.1400), ("rapid_river", 20.9836), ("lockport", 21.5914), ("mokena", 24.3773), ("flanagan", 23.8092), ("griffith", 25.0937), ("stockbridge", 25.5103), ("marysville", 27.2926), ("sarnia", 26.9948), ("westover", 27.3267), ("nanticoke", 28.0446)]),
                ("cromer", [("clearbrook", 11.6220), ("superior", 13.8722), ("rapid_river", 20.7158), ("lockport", 21.3236), ("mokena", 24.1095), ("flanagan", 23.5414), ("griffith", 24.8259), ("stockbridge", 25.2425), ("marysville", 27.0248), ("sarnia", 26.7270), ("westover", 27.0589), ("nanticoke", 27.7768)]),
            ],
        ),
        (
            "Light crude",
            12,
            [
                ("edmonton", [("clearbrook", 12.3162), ("superior", 14.4729), ("rapid_river", 21.3165), ("lockport", 21.9243), ("mokena", 24.7102), ("flanagan", 24.1421), ("griffith", 25.4266), ("stockbridge", 25.8432), ("marysville", 27.6255), ("sarnia", 27.3277), ("westover", 27.6596), ("nanticoke", 28.3775)]),
                ("hardisty", [("clearbrook", 12.0040), ("superior", 14.1608), ("rapid_river", 21.0044), ("lockport", 21.6122), ("mokena", 24.3981), ("flanagan", 23.8300), ("griffith", 25.1145), ("stockbridge", 25.5311), ("marysville", 27.3134), ("sarnia", 27.0156), ("westover", 27.3475), ("nanticoke", 28.0654)]),
                ("cromer", [("clearbrook", 10.6393), ("superior", 12.7960), ("rapid_river", 19.6396), ("lockport", 20.2474), ("mokena", 23.0333), ("flanagan", 22.4652), ("griffith", 23.7497), ("stockbridge", 24.1663), ("marysville", 25.9486), ("sarnia", 25.6508), ("westover", 25.9827), ("nanticoke", 26.7006)]),
            ],
        ),
        (
            "Medium crude",
            13,
            [
                ("edmonton", [("clearbrook", 13.3299), ("superior", 15.5801), ("rapid_river", 22.4237), ("lockport", 23.0315), ("mokena", 25.8174), ("flanagan", 25.2493), ("griffith", 26.5338), ("stockbridge", 26.9504), ("marysville", 28.7327), ("sarnia", 28.4349), ("westover", 28.7668), ("nanticoke", 29.4847)]),
                ("hardisty", [("clearbrook", 13.0279), ("superior", 15.2781), ("rapid_river", 22.1217), ("lockport", 22.7295), ("mokena", 25.5154), ("flanagan", 24.9473), ("griffith", 26.2318), ("stockbridge", 26.6484), ("marysville", 28.4307), ("sarnia", 28.1329), ("westover", 28.4648), ("nanticoke", 29.1827)]),
                ("kerrobert", [("clearbrook", 12.4627), ("superior", 14.7129), ("rapid_river", 21.5565), ("lockport", 22.1643), ("mokena", 24.9502), ("flanagan", 24.3821), ("griffith", 25.6666), ("stockbridge", 26.0832), ("marysville", 27.8655), ("sarnia", 27.5677), ("westover", 27.8996), ("nanticoke", 28.6175)]),
                ("regina", [("clearbrook", 11.8898), ("superior", 14.1400), ("rapid_river", 20.9836), ("lockport", 21.5914), ("mokena", 24.3773), ("flanagan", 23.8092), ("griffith", 25.0937), ("stockbridge", 25.5103), ("marysville", 27.2926), ("sarnia", 26.9948), ("westover", 27.3267), ("nanticoke", 28.0446)]),
                ("cromer", [("clearbrook", 11.6220), ("superior", 13.8722), ("rapid_river", 20.7158), ("lockport", 21.3236), ("mokena", 24.1095), ("flanagan", 23.5414), ("griffith", 24.8259), ("stockbridge", 25.2425), ("marysville", 27.0248), ("sarnia", 26.7270), ("westover", 27.0589), ("nanticoke", 27.7768)]),
            ],
        ),
    ]

    for product, pdf_page, origin_groups in total_specs:
        for origin, destinations in origin_groups:
            for destination, total in destinations:
                add_rate(
                    rows,
                    pipeline="Enbridge Mainline / Lakehead",
                    route_id="enbridge-mainline-lakehead",
                    origin=origin,
                    destination=destination,
                    product=product,
                    service="International joint rate",
                    rate_type="total",
                    currency="USD",
                    unit="m3",
                    total=total,
                    doc_id="enbridge_cer_596",
                    pdf_page=pdf_page,
                    table="Appendix A - Total IJT per CER 596 / FERC 45.46.0",
                    notes="Appendix A converts the Canadian and Lakehead components to a total U.S.-dollar tariff using the tariff's stated FX convention.",
                )

    heavy_groups = [
        ("edmonton", [("clearbrook", 11.5825, 8.4824), ("superior", 11.5825, 10.7326), ("rapid_river", 11.5825, 17.5763), ("lockport", 11.5825, 18.1840), ("mokena", 11.5825, 20.9699), ("flanagan", 11.5825, 20.4018), ("griffith", 11.5825, 21.6863), ("stockbridge", 12.2256, 21.6438), ("marysville", 12.2256, 23.4261), ("sarnia", 12.2256, 23.1283), ("westover", 12.2256, 23.4602), ("nanticoke", 12.2256, 24.1781)]),
        ("hardisty", [("clearbrook", 10.1051, 8.1439), ("superior", 10.1051, 10.3941), ("rapid_river", 10.1051, 17.2378), ("lockport", 10.1051, 17.8455), ("mokena", 10.1051, 20.6314), ("flanagan", 10.1051, 20.0633), ("griffith", 10.1051, 21.3478), ("stockbridge", 10.7483, 21.3053), ("marysville", 10.7483, 23.0876), ("sarnia", 10.7483, 22.7898), ("westover", 10.7483, 23.1217), ("nanticoke", 10.7483, 23.8396)]),
        ("kerrobert", [("clearbrook", 8.6194, 7.5519), ("superior", 8.6194, 9.8021), ("rapid_river", 8.6194, 16.6458), ("lockport", 8.6194, 17.2535), ("mokena", 8.6194, 20.0394), ("flanagan", 8.6194, 19.4713), ("griffith", 8.6194, 20.7558), ("stockbridge", 9.2626, 20.7133), ("marysville", 9.2626, 22.4956), ("sarnia", 9.2626, 22.1978), ("westover", 9.2626, 22.5297), ("nanticoke", 9.2626, 23.2476)]),
        ("regina", [("clearbrook", 5.6393, 6.8691), ("superior", 5.6393, 9.1193), ("rapid_river", 5.6393, 15.9630), ("lockport", 5.6393, 16.5708), ("mokena", 5.6393, 19.3567), ("flanagan", 5.6393, 18.7886), ("griffith", 5.6393, 20.0731), ("stockbridge", 6.2825, 20.0305), ("marysville", 6.2825, 21.8128), ("sarnia", 6.2825, 21.5150), ("westover", 6.2825, 21.8469), ("nanticoke", 6.2825, 22.5648)]),
        ("cromer", [("clearbrook", 3.4864, 6.3759), ("superior", 3.4864, 8.6261), ("rapid_river", 3.4864, 15.4698), ("lockport", 3.4864, 16.0776), ("mokena", 3.4864, 18.8635), ("flanagan", 3.4864, 18.2954), ("griffith", 3.4864, 19.5799), ("stockbridge", 4.1295, 19.5373), ("marysville", 4.1295, 21.3196), ("sarnia", 4.1295, 21.0218), ("westover", 4.1295, 21.3537), ("nanticoke", 4.1295, 22.0716)]),
    ]
    for origin, destinations in heavy_groups:
        for destination, cad_component, usd_component in destinations:
            add_rate(
                rows,
                pipeline="Enbridge Mainline / Lakehead",
                route_id="enbridge-mainline-lakehead",
                origin=origin,
                destination=destination,
                product="Heavy crude",
                service="International joint rate",
                rate_type="component",
                currency="mixed",
                unit="m3",
                cad_component_m3=cad_component,
                usd_component_m3=usd_component,
                doc_id="enbridge_cer_596",
                pdf_page=19 if origin in {"edmonton", "hardisty"} else 20,
                table="Appendix B - EPI and Lakehead components",
                notes="Heavy crude is published as Canadian-dollar EPI component plus U.S.-dollar Lakehead component.",
            )


def add_enbridge_local_gretna(rows: list[dict[str, Any]]) -> None:
    for origin, light, medium, heavy in [
        ("edmonton", 21.5427, 22.8669, 25.1839),
        ("hardisty", 20.8133, 22.1194, 24.4047),
        ("regina", 18.2615, None, 21.7018),
        ("cromer", 17.1988, 18.4233, 20.5662),
    ]:
        for product, value in [("Light crude", light), ("Medium crude", medium), ("Heavy crude", heavy)]:
            if value is None:
                continue
            add_rate(
                rows,
                pipeline="Enbridge Canadian Mainline",
                route_id="enbridge-mainline-lakehead",
                origin=origin,
                destination="gretna",
                product=product,
                service="Local toll to International Boundary near Gretna",
                rate_type="local total",
                currency="CAD",
                unit="m3",
                total=value,
                doc_id="enbridge_cer_599",
                pdf_page=8,
                table="Appendix A - CER 595 local toll component to Gretna",
                issued_override="2026-03-26",
                effective_override="2026-04-01",
                status_override="current",
                notes="CER 599 Appendix A reproduces Enbridge Pipelines Inc. local tolls contained in CER No. 595 and converts them to per-bbl values.",
            )


def add_enbridge_599(rows: list[dict[str, Any]]) -> None:
    shared_notes = [
        "Receipt and delivery terminalling services are included in the tariff rates.",
        "Loss allowance is deducted under Enbridge Pipelines Inc., Lakehead, and CCPS rules; Enbridge Pipelines Inc. states 1/20th of 1% on receipts.",
        "Committed shippers electing CCPS Cushing tankage pay the Cushing Terminal tankage charge under CCPS FERC No. 38.26.0 or successor tariff.",
    ]
    uncommitted_adders = {
        "edmonton": (0.0286, -0.0001, 0.0534),
        "hardisty": (0.0246, -0.0001, 0.0534),
        "regina": (0.0126, 0.0000, 0.0534),
        "cromer": (0.0068, 0.0000, 0.0534),
    }
    tables = [
        (
            "Committed TSA - 2 year term, 5,000-45,000 bbl/d",
            "committed total",
            4,
            [
                ("edmonton", 6.7000, 6.9500, 7.4000),
                ("hardisty", 6.5000, 6.7500, 7.1500),
                ("regina", 5.9000, None, 6.4600),
                ("cromer", 5.6500, 5.8000, 6.1000),
            ],
        ),
        (
            "Firm service committed TSA - 2 year term, 5,000-45,000 bbl/d",
            "firm committed total",
            4,
            [
                ("edmonton", 7.5500, 7.8000, 8.2500),
                ("hardisty", 7.3500, 7.6000, 8.0000),
                ("regina", 6.7500, None, 7.3100),
                ("cromer", 6.5000, 6.6500, 6.9500),
            ],
        ),
        (
            "Committed throughput and deficiency - 7 year term, 5,000-44,999 bbl/d",
            "committed total",
            5,
            [
                ("edmonton", 7.3000, 7.6000, 8.0500),
                ("hardisty", 7.1500, 7.4000, 7.8000),
                ("cromer", 6.2500, 6.4500, 6.7500),
            ],
        ),
        (
            "Volume incentive committed - 7 year term, 45,000-59,999 bbl/d",
            "committed incentive total",
            5,
            [
                ("edmonton", 6.8000, 7.1000, 7.5500),
                ("hardisty", 6.6500, 6.9000, 7.3000),
                ("cromer", 5.7500, 5.9500, 6.2500),
            ],
        ),
        (
            "High volume incentive committed - 7 year term, 60,000 bbl/d",
            "committed incentive total",
            6,
            [
                ("edmonton", 6.5500, 6.8500, 7.3000),
                ("hardisty", 6.4000, 6.6500, 7.0500),
                ("cromer", 5.5500, 5.7000, 6.0000),
            ],
        ),
        (
            "Uncommitted international joint rate",
            "uncommitted total",
            6,
            [
                ("edmonton", 7.5400, 7.7900, 8.2400),
                ("hardisty", 7.3400, 7.5900, 7.9900),
                ("regina", 6.7400, None, 7.3000),
                ("cromer", 6.4900, 6.6400, 6.9400),
            ],
        ),
    ]
    for service, rate_type, pdf_page, origin_rows in tables:
        for origin, light, medium, heavy in origin_rows:
            for product, value in [("Light crude", light), ("Medium crude", medium), ("Heavy crude", heavy)]:
                if value is None:
                    continue
                additional_costs = None
                pdf_for_source = pdf_page
                notes = "Pending tariff effective June 1, 2026; used as the forward tariff because it replaces the older Spearhead filing."
                if rate_type == "uncommitted total":
                    abandonment, credit, mpuc = uncommitted_adders[origin]
                    additional_costs = [
                        cost_item("enbridge_cer_599", 10, "Abandonment surcharge", abandonment, "USD", "bbl", default_additive=True),
                        cost_item("enbridge_cer_599", 10, "Non-performance penalty credit", credit, "USD", "bbl", default_additive=True),
                        cost_item("enbridge_cer_599", 10, "MPUC surcharge", mpuc, "USD", "bbl", default_additive=True),
                    ]
                    notes = "Uncommitted table rate plus Appendix B adders gives the all-in uncommitted rate shown in the worksheet."
                    pdf_for_source = 6
                add_rate(
                    rows,
                    pipeline="Enbridge Mainline / Lakehead / Spearhead",
                    route_id="enbridge-us-downstream",
                    origin=origin,
                    destination="cushing",
                    product=product,
                    service=service,
                    rate_type=rate_type,
                    currency="USD",
                    unit="bbl",
                    total=value,
                    doc_id="enbridge_cer_599",
                    pdf_page=pdf_for_source,
                    table="International joint rates to Cushing",
                    notes=notes,
                    additional_costs=additional_costs,
                    conditional_charges=shared_notes,
                    loss_allowance_percent=0.05,
                )


def add_enbridge_597(rows: list[dict[str, Any]]) -> None:
    destinations = ["seaway_freeport", "sweeny", "echo", "beaumont_port_arthur"]
    origins = ["edmonton", "hardisty", "kerrobert", "regina", "cromer"]
    products = ["Light crude", "Medium crude", "Heavy crude"]
    power_charge = cost_item(
        "enbridge_cer_597",
        8,
        "Flanagan South power charge",
        0.5200,
        "USD",
        "bbl",
        text="Separate power charge assessed in addition to all CER 597 rates; recalculated annually.",
        default_additive=True,
    )
    common_conditions = [
        "Delivery points covered by the table are ECHO, Seaway Freeport, Phillips 66 Sweeny, and Beaumont/Port Arthur.",
        "Enbridge Pipelines Inc. deducts 1/20th of 1% loss allowance on receipts; Lakehead and Flanagan South deduct loss allowance under their rules.",
        "For 3rd Open Season committed and uncommitted service, applicable tankage charges are not included and are referenced to CER 595, CER RT 25-2, and Lakehead FERC 43.54.0 or successors.",
    ]
    committed_included = [
        "Rates include abandonment surcharges and Minnesota abandonment surcharge.",
        "Tankage charges incurred on Enbridge Pipelines Inc. or Lakehead are included in 1st and 2nd Open Season committed rates.",
    ]
    fsp_597_committed = [
        ("1st Open Season committed - 10 years, 99,999 bbl/d or less", 4, "committed total", "Light crude", [7.8083, 7.5186, 7.3902, 7.1342, 6.8178]),
        ("1st Open Season committed - 15 years, 49,999 bbl/d or less", 4, "committed total", "Light crude", [7.4979, 7.2080, 7.0798, 6.8236, 6.5072]),
        ("1st Open Season committed - 15 years, 50,000 bbl/d or more", 4, "committed total", "Light crude", [7.2494, 6.9598, 6.8315, 6.5750, 6.2588]),
        ("1st Open Season committed - 10 years, 99,999 bbl/d or less", 4, "committed total", "Medium crude", [8.6850, 8.3722, None, None, 7.4966]),
        ("1st Open Season committed - 15 years, 49,999 bbl/d or less", 4, "committed total", "Medium crude", [8.3743, 8.0617, None, None, 7.1862]),
        ("1st Open Season committed - 15 years, 50,000 bbl/d or more", 4, "committed total", "Medium crude", [8.1259, 7.8133, None, None, 6.9377]),
        ("1st Open Season committed - 10 years, 99,999 bbl/d or less", 5, "committed total", "Heavy crude", [9.1624, 8.8105, 8.7071, 8.1651, 7.6376]),
        ("1st Open Season committed - 15 years, 49,999 bbl/d or less", 5, "committed total", "Heavy crude", [8.8518, 8.5001, 8.3967, 7.8546, 7.3272]),
        ("1st Open Season committed - 15 years, 50,000 bbl/d or more", 5, "committed total", "Heavy crude", [8.6032, 8.2514, 8.1482, 7.6062, 7.0786]),
        ("2nd Open Season committed - 10 years, 49,999 bbl/d or less", 5, "committed total", "Light crude", [8.5412, 8.2514, 8.1231, 7.8669, 7.5506]),
        ("2nd Open Season committed - 10 years, 50,000-99,999 bbl/d", 5, "committed total", "Light crude", [8.3300, 8.0402, 7.9120, 7.6558, 7.3394]),
        ("2nd Open Season committed - 15 years, 49,999 bbl/d or less", 5, "committed total", "Light crude", [8.0940, 7.8043, 7.6762, 7.4199, 7.1034]),
        ("2nd Open Season committed - 15 years, 50,000-99,999 bbl/d", 5, "committed total", "Light crude", [7.7213, 7.4318, 7.3036, 7.0470, 6.7308]),
        ("2nd Open Season committed - 20 years, 50,000-99,999 bbl/d", 5, "committed total", "Light crude", [7.4110, 7.1211, 6.9929, 6.7366, 6.4202]),
        ("2nd Open Season committed - 10 years, 49,999 bbl/d or less", 6, "committed total", "Medium crude", [9.4594, 9.1400, None, None, 8.1345]),
        ("2nd Open Season committed - 10 years, 50,000-99,999 bbl/d", 6, "committed total", "Medium crude", [9.2418, 8.9260, None, None, 7.9203]),
        ("2nd Open Season committed - 15 years, 49,999 bbl/d or less", 6, "committed total", "Medium crude", [9.0025, 8.6867, None, None, 7.6810]),
        ("2nd Open Season committed - 15 years, 50,000-99,999 bbl/d", 6, "committed total", "Medium crude", [8.5868, 8.2711, None, None, 7.2781]),
        ("2nd Open Season committed - 20 years, 50,000-99,999 bbl/d", 6, "committed total", "Medium crude", [8.3098, 7.9940, None, None, 6.9884]),
        ("2nd Open Season committed - 10 years, 49,999 bbl/d or less", 6, "committed total", "Heavy crude", [10.0315, 9.6746, 9.5701, 9.0205, 8.4856]),
        ("2nd Open Season committed - 10 years, 50,000-99,999 bbl/d", 6, "committed total", "Heavy crude", [9.8172, 9.4609, 9.3560, 8.8064, 8.2717]),
        ("2nd Open Season committed - 15 years, 49,999 bbl/d or less", 6, "committed total", "Heavy crude", [9.5781, 9.2213, 9.1168, 8.5672, 8.0323]),
        ("2nd Open Season committed - 15 years, 50,000-99,999 bbl/d", 6, "committed total", "Heavy crude", [9.1625, 8.8057, 8.7010, 8.1514, 7.6293]),
        ("2nd Open Season committed - 20 years, 50,000-99,999 bbl/d", 6, "committed total", "Heavy crude", [8.8853, 8.5287, 8.4240, 7.8745, 7.3396]),
        ("3rd Open Season committed - 11 years, >=55,000 bbl/d to June 30, 2030", 7, "committed total", "Heavy crude", [8.8877, 8.5413, None, None, None]),
    ]
    for service, pdf_page, rate_type, product, values in fsp_597_committed:
        for origin, value in zip(origins, values):
            if value is None:
                continue
            included_text = committed_included if service.startswith(("1st", "2nd")) else [committed_included[0]]
            for destination in destinations:
                add_rate(
                    rows,
                    pipeline="Enbridge Mainline / Lakehead / Flanagan South",
                    route_id="enbridge-us-downstream",
                    origin=origin,
                    destination=destination,
                    product=product,
                    service=service,
                    rate_type=rate_type,
                    currency="USD",
                    unit="bbl",
                    total=value,
                    doc_id="enbridge_cer_597",
                    pdf_page=pdf_page,
                    table="Committed international joint rates to all Texas delivery points",
                    additional_costs=[power_charge],
                    conditional_charges=included_text + common_conditions,
                    loss_allowance_percent=0.05,
                )

    appendix_b = {
        "edmonton": {
            "base": {"Light crude": 10.4725, "Medium crude": 10.7168, "Heavy crude": 11.1442},
            "published": {"Light crude": 10.5544, "Medium crude": 10.7987, "Heavy crude": 10.0415},
            "adders": (0.0286, -0.0001, 0.0534),
            "heavy_discount": -1.1846,
        },
        "hardisty": {
            "base": {"Light crude": 10.2843, "Medium crude": 10.5179, "Heavy crude": 10.9265},
            "published": {"Light crude": 10.3622, "Medium crude": 10.5958, "Heavy crude": 9.6846},
            "adders": (0.0246, -0.0001, 0.0534),
            "heavy_discount": -1.3198,
        },
        "kerrobert": {
            "base": {"Light crude": 10.0550, "Heavy crude": 10.6675},
            "published": {"Light crude": 10.1289, "Heavy crude": 9.5801},
            "adders": (0.0206, -0.0001, 0.0534),
            "heavy_discount": -1.1613,
        },
        "regina": {
            "base": {"Light crude": 9.6755, "Heavy crude": 10.2283},
            "published": {"Light crude": 9.7415, "Heavy crude": 9.0305},
            "adders": (0.0126, 0.0000, 0.0534),
            "heavy_discount": -1.2638,
        },
        "cromer": {
            "base": {"Light crude": 9.4012, "Medium crude": 9.5866, "Heavy crude": 9.9110},
            "published": {"Light crude": 9.4614, "Medium crude": 9.6468, "Heavy crude": 8.4956},
            "adders": (0.0068, 0.0000, 0.0534),
            "heavy_discount": -1.4756,
        },
    }
    for origin, data in appendix_b.items():
        abandonment, credit, mpuc = data["adders"]
        for destination in destinations:
            for product, value in data["published"].items():
                included_costs = [
                    cost_item("enbridge_cer_597", 12, "Abandonment surcharge", abandonment, "USD", "bbl", included_in_total=True),
                    cost_item("enbridge_cer_597", 12, "Non-performance penalty credit", credit, "USD", "bbl", included_in_total=True),
                    cost_item("enbridge_cer_597", 12, "MPUC surcharge", mpuc, "USD", "bbl", included_in_total=True),
                ]
                if product == "Heavy crude":
                    included_costs.append(cost_item("enbridge_cer_597", 12, "Heavy crude discount", data["heavy_discount"], "USD", "bbl", included_in_total=True))
                add_rate(
                    rows,
                    pipeline="Enbridge Mainline / Lakehead / Flanagan South",
                    route_id="enbridge-us-downstream",
                    origin=origin,
                    destination=destination,
                    product=product,
                    service="Uncommitted international joint rate",
                    rate_type="uncommitted total",
                    currency="USD",
                    unit="bbl",
                    total=value,
                    base_before_included_costs=data["base"][product],
                    doc_id="enbridge_cer_597",
                    pdf_page=8,
                    table="Uncommitted international joint rates to all Texas delivery points",
                    notes="Published uncommitted table rate includes Appendix B abandonment, non-performance credit, MPUC surcharge, and heavy discount where applicable; FSP power is assessed in addition.",
                    included_costs=included_costs,
                    additional_costs=[power_charge],
                    conditional_charges=common_conditions,
                    loss_allowance_percent=0.05,
                )


def add_keystone(rows: list[dict[str, Any]]) -> None:
    keystone_adders = [
        cost_item(
            "keystone_cer_71",
            2,
            "Abandonment surcharge",
            0.059,
            "CAD",
            "bbl",
            text="Applies to all shippers; tariff also states CAD 0.368/m3.",
            default_additive=True,
        )
    ]
    sour_lake = "Sour Lake interconnect deliveries are charged an additional USD 0.8976/m3 (USD 0.1427/bbl)."
    for destination in ["port_arthur", "houston"]:
        for product, value in [("Light crude", 7.958), ("Heavy crude", 8.650)]:
            add_rate(
                rows,
                pipeline="Keystone",
                route_id="keystone",
                origin="hardisty",
                destination=destination,
                product=product,
                service="International joint rate",
                rate_type="uncommitted total",
                currency="USD",
                unit="bbl",
                total=value,
                doc_id="keystone_cer_71",
                pdf_page=2,
                table="International joint rates from Hardisty to Texas delivery points",
                notes="International joint uncommitted rate from Hardisty to Port Arthur or Houston.",
                additional_costs=keystone_adders,
                conditional_charges=[sour_lake],
            )


def add_express(rows: list[dict[str, Any]]) -> None:
    abandonment = [
        cost_item(
            "express_cer_204",
            2,
            "Abandonment surcharge",
            0.0500,
            "USD",
            "m3",
            text="Applies to each toll under Express Canada local tariffs.",
            default_additive=True,
        )
    ]
    for product, value in [
        ("Light crude", 5.0384),
        ("Medium crude", 5.4414),
        ("Heavy crude", 6.1467),
        ("Super-heavy crude", 6.3986),
    ]:
        add_rate(
            rows,
            pipeline="Express Canada",
            route_id="express-platte",
            origin="hardisty",
            destination="hardisty",
            product=product,
            service="Uncommitted local rate",
            rate_type="uncommitted local total",
            currency="USD",
            unit="m3",
            total=0.3096,
            doc_id="express_cer_204",
            pdf_page=2,
            table="Uncommitted local rates at Hardisty and to the international boundary near Wild Horse",
            conditional_charges=["Petroleum classification is based on measured density and viscosity; higher charge applies when density and viscosity fall in different classes."],
        )
        add_rate(
            rows,
            pipeline="Express Canada",
            route_id="express-platte",
            origin="hardisty",
            destination="wild_horse",
            product=product,
            service="Uncommitted local rate",
            rate_type="uncommitted total",
            currency="USD",
            unit="m3",
            total=value,
            doc_id="express_cer_204",
            pdf_page=2,
            table="Uncommitted local rates to the international boundary near Wild Horse",
            additional_costs=abandonment,
            conditional_charges=["Petroleum classification is based on measured density and viscosity; higher charge applies when density and viscosity fall in different classes."],
        )

    add_rate(
        rows,
        pipeline="Express Canada",
        route_id="express-platte",
        origin="hardisty",
        destination="wild_horse",
        product="Petroleum",
        service="Committed local term rate",
        rate_type="committed local total",
        currency="USD",
        unit="m3",
        total=7.7143,
        doc_id="express_cer_202",
        pdf_page=2,
        table="Term rate tariff to the international boundary near Wild Horse",
        additional_costs=[
            cost_item("express_cer_202", 2, "Abandonment surcharge", 0.0500, "USD", "m3", default_additive=True)
        ],
    )

    express_common = [
        "Rates include product classification surcharge and re-origination fee where applicable.",
        "Petroleum is subject to percentage deduction for loss allowance under carrier rules.",
        "Buffalo Station and Wood River discount incentives may apply only where the tariff eligibility conditions are met.",
    ]
    express_203_adders = [
        cost_item("express_cer_203", 2, "Abandonment surcharge", 0.0500, "USD", "m3", default_additive=True),
    ]

    def add_express_matrix(service: str, pdf_page: int, table: str, matrix: list[tuple[str, float, float, float, float]]) -> None:
        for destination, light, medium, heavy, super_heavy in matrix:
            for product, value in [
                ("Light crude", light),
                ("Medium crude", medium),
                ("Heavy crude", heavy),
                ("Super-heavy crude", super_heavy),
            ]:
                add_rate(
                    rows,
                    pipeline="Express / Platte",
                    route_id="express-platte",
                    origin="hardisty",
                    destination=destination,
                    product=product,
                    service=service,
                    rate_type="committed term total",
                    currency="USD",
                    unit="m3",
                    total=value,
                    doc_id="express_cer_203",
                    pdf_page=pdf_page,
                    table=table,
                    additional_costs=express_203_adders,
                    conditional_charges=express_common,
                )

    add_express_matrix(
        "Committed international joint rate - 5 to 9 years",
        2,
        "5-9 year term committed international joint rates",
        [
            ("edgar_station", 18.3370, 19.8031, 22.3704, 23.2872),
            ("sinclair_casper", 19.3304, 20.8773, 23.5837, 24.5487),
            ("casper", 20.8549, 22.5248, 25.4411, 26.4866),
            ("guernsey", 25.7231, 27.3922, 30.3078, 31.3537),
            ("holdrege", 30.6958, 32.3658, 35.1983, 36.2445),
            ("wood_river", 39.4284, 41.0985, 44.0138, 45.0592),
        ],
    )
    add_express_matrix(
        "Committed international joint rate - 10 to 14 years",
        3,
        "10-14 year term committed international joint rates",
        [
            ("buffalo_station", 14.9587, 14.9587, 14.9587, 14.9587),
            ("edgar_station", 18.1880, 19.6418, 22.1873, 23.0966),
            ("sinclair_casper", 19.1719, 20.7058, 23.3910, 24.3485),
            ("casper", 20.6852, 22.3416, 25.2324, 26.2695),
            ("guernsey", 25.5126, 27.1685, 30.0598, 31.0975),
            ("holdrege", 30.1149, 32.0167, 34.9083, 35.9464),
            ("wood_river", 39.1063, 40.7621, 43.6537, 44.6910),
        ],
    )
    add_express_matrix(
        "Committed international joint rate - 15 to 19 years",
        4,
        "15-19 year term committed international joint rates",
        [
            ("buffalo_station", 14.9587, 14.9587, 14.9587, 14.9587),
            ("edgar_station", 18.0118, 19.4514, 21.9722, 22.8724),
            ("sinclair_casper", 18.9859, 20.5050, 23.1635, 24.1115),
            ("casper", 20.4869, 22.1275, 24.9901, 26.0171),
            ("guernsey", 25.2643, 26.9048, 29.7679, 30.7956),
            ("holdrege", 29.8239, 31.4646, 34.3276, 35.3553),
            ("wood_river", 38.7244, 40.3648, 43.2274, 44.2551),
        ],
    )
    add_express_matrix(
        "Committed international joint rate - 20 years or more",
        5,
        "20-year-or-more term committed international joint rates",
        [
            ("buffalo_station", 14.9587, 14.9587, 14.9587, 14.9587),
            ("edgar_station", 17.7060, 19.1210, 21.5979, 22.4828),
            ("sinclair_casper", 18.6633, 20.1563, 22.7689, 23.6998),
            ("casper", 20.1434, 21.7565, 24.5705, 25.5817),
            ("guernsey", 24.8349, 26.4480, 29.2627, 30.2743),
            ("holdrege", 29.3184, 30.9317, 33.7463, 34.7578),
            ("wood_river", 38.0194, 39.6323, 42.4468, 43.4583),
        ],
    )

    for service, pdf_page, rowspec in [
        (
            "Committed international joint rate - 2019 Open Season, 10 years",
            7,
            [("buffalo_station", 22.5311), ("edgar_station", 28.1638), ("casper", 30.0414)],
        ),
        (
            "Committed international joint rate - 2025 Open Season, 2 years",
            8,
            [("buffalo_station", 14.9587), ("edgar_station", 18.0118), ("sinclair_casper", 18.9859), ("casper", 20.4869)],
        ),
        (
            "Committed international joint rate - 2025 Open Season, 7 years",
            9,
            [("buffalo_station", 14.9587), ("edgar_station", 17.7060), ("sinclair_casper", 18.6633), ("casper", 20.1434)],
        ),
    ]:
        for destination, value in rowspec:
            add_rate(
                rows,
                pipeline="Express / Platte",
                route_id="express-platte",
                origin="hardisty",
                destination=destination,
                product="Petroleum",
                service=service,
                rate_type="committed term total",
                currency="USD",
                unit="m3",
                total=value,
                doc_id="express_cer_203",
                pdf_page=pdf_page,
                table=service,
                additional_costs=express_203_adders,
                conditional_charges=express_common,
            )

    for destination, light_medium, heavy_super in [
        ("buffalo_station", 24.4116, 25.9371),
        ("edgar_station", 25.9371, 27.5582),
        ("sinclair_casper", 30.5144, 32.4215),
        ("casper", 30.5144, 32.4215),
    ]:
        for product, value in [
            ("Light crude / medium crude", light_medium),
            ("Heavy crude / super-heavy crude", heavy_super),
        ]:
            add_rate(
                rows,
                pipeline="Express / Platte",
                route_id="express-platte",
                origin="hardisty",
                destination=destination,
                product=product,
                service="Committed international joint rate - 2024 Open Season, 5 years",
                rate_type="committed term total",
                currency="USD",
                unit="m3",
                total=value,
                doc_id="express_cer_203",
                pdf_page=8,
                table="2024 Open Season 5-year term committed international joint rates",
                additional_costs=express_203_adders,
                conditional_charges=express_common,
            )


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
            ("Enhanced response regime fee", 0.6181),
            ("First Nations consultation and accommodation", 0.0375),
            ("GHG offset costs", -0.6590),
            ("Revenue-sharing variable toll true-up", -0.1357),
        ]),
        ("sumas", "Light crude / refined petroleum"): tm_components([
            ("Power", 2.1603),
            ("Fiber optic leak detection", 0.4458),
            ("Pipeline reclamation surcharge", 0.4625),
            ("Enhanced response regime fee", 0.8268),
            ("First Nations consultation and accommodation", 0.0501),
            ("GHG offset costs", -0.8816),
            ("Revenue-sharing variable toll true-up", -0.1815),
        ]),
        ("sumas", "Heavy crude"): tm_components([
            ("Power", 2.5923),
            ("Fiber optic leak detection", 0.4458),
            ("Pipeline reclamation surcharge", 0.4625),
            ("Enhanced response regime fee", 0.8268),
            ("First Nations consultation and accommodation", 0.0501),
            ("GHG offset costs", -0.8816),
            ("Revenue-sharing variable toll true-up", -0.1815),
        ]),
        ("burnaby_westridge", "Light crude / refined petroleum to Burnaby"): tm_components([
            ("Power", 2.2653),
            ("Fiber optic leak detection", 0.4675),
            ("Pipeline reclamation surcharge", 0.4849),
            ("Enhanced response regime fee", 0.8670),
            ("First Nations consultation and accommodation", 0.0525),
            ("GHG offset costs", -0.9244),
            ("Revenue-sharing variable toll true-up", -0.1903),
        ]),
        ("burnaby_westridge", "Light crude to Westridge"): tm_components([
            ("Power", 2.2733),
            ("Fiber optic leak detection", 0.4692),
            ("Pipeline reclamation surcharge", 0.4866),
            ("Enhanced response regime fee", 1.6396),
            ("First Nations consultation and accommodation", 0.8701),
            ("GHG offset costs", 0.0527),
            ("Revenue-sharing variable toll true-up", -0.9277),
            ("Westridge dock bid premium sur-credit", -0.1910),
        ]),
        ("burnaby_westridge", "Heavy crude to Westridge"): tm_components([
            ("Power", 2.7280),
            ("Fiber optic leak detection", 0.4692),
            ("Pipeline reclamation surcharge", 0.4866),
            ("Enhanced response regime fee", 1.6396),
            ("First Nations consultation and accommodation", 0.8701),
            ("GHG offset costs", 0.0527),
            ("Revenue-sharing variable toll true-up", -0.9277),
            ("Westridge dock bid premium sur-credit", -0.1911),
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
            total=0.5648,
            doc_id="trans_mountain_puget_415",
            pdf_page=2,
            table="Transportation rate from Sumas to Anacortes and Ferndale",
            notes="Tariff publishes 56.48 U.S. cents per barrel.",
            additional_costs=[
                cost_item(
                    "trans_mountain_puget_415",
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
    add_enbridge_local_gretna(rows)
    add_enbridge_596(rows)
    add_enbridge_599(rows)
    add_enbridge_597(rows)
    add_keystone(rows)
    add_express(rows)
    add_trans_mountain(rows)

    return {
        "metadata": {
            "name": "Market Access Tariffs",
            "description": "Current public tariff rows for crude, condensate, and published heavy/super-heavy crude products used by the market-access hub tooltips.",
            "generated_with": "scripts/build_market_access_tariffs.py",
            "generated_on": date.today().isoformat(),
            "unit_notes": [
                "m3 rates are also converted to per-bbl using 1 m3 = 6.28981077 bbl.",
                "Rows with mixed currency preserve the operator-published CAD and USD components instead of applying a live FX conversion.",
                "Pending-effective-forward-use rows are included when they replace an older tariff for forward-looking use.",
            ],
        },
        "documents": DOCS,
        "hubs": HUBS,
        "hub_aliases": HUB_ALIASES,
        "tariffs": rows,
    }


def main() -> int:
    data = build_tariffs()
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=True), encoding="utf-8")
    print(f"Wrote {len(data['tariffs'])} tariff rows to {DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
