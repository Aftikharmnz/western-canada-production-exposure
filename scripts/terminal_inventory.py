"""Reproducible reviewed terminal observations, with separate identity and location provenance.

Source snapshots are committed public facts, not a claim of live operating status.
Only explicit facility identity replacements deduplicate the older Canadian list.
Historical EIA observations remain separate from operator-map observations.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "terminal_sources"
REVIEWS = ROOT / "data" / "terminal_facility_reviews.json"
REVIEW_DATE = "2026-10-10"
BUCKEYE_MAP = "https://www.buckeye.com/what-we-do/asset-map"
NPRI_URL = "https://maps-cartes.ec.gc.ca/arcgis/rest/services/STB_DGST/NPRI/MapServer/0"
US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR VI".split())
CATEGORY_LABELS = {
    "crude-storage": "Crude oil storage", "product-storage": "Refined product storage",
    "ngl-storage": "NGL / LPG storage", "crude-terminal": "Crude oil terminals",
    "product-terminal": "Petroleum product terminals", "crude-rail-terminal": "Crude-by-rail terminals",
    "inactive-terminal": "Inactive / decommissioned terminals",
}


def snapshot(name: str) -> dict[str, Any]:
    data = json.loads((SOURCES / f"{name}.json").read_text(encoding="utf-8"))
    collection = data["data"]
    if collection.get("error") or collection.get("exceededTransferLimit"):
        raise ValueError(f"Incomplete terminal source snapshot: {name}")
    expected_counts = {"buckeye_terminals": 128, "buckeye_propane_terminals": 2,
                       "npri_2024": 41, "eia_products_archive": 1476, "eia_crude_rail_archive": 99}
    if len(collection["features"]) != expected_counts[name]:
        raise ValueError(f"Terminal snapshot record count changed without review: {name}")
    ids = [f["properties"].get("NpriID") if name == "npri_2024" else f.get("id") for f in collection["features"]]
    if None in ids or len(set(ids)) != len(ids):
        raise ValueError(f"Missing or duplicate source identifiers: {name}")
    return data


def valid_point(coordinates: Any) -> bool:
    return (isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in coordinates[:2])
            and -180 <= coordinates[0] <= 180 and -90 <= coordinates[1] <= 90
            and list(coordinates[:2]) != [0, 0])


def feature(props: dict[str, Any], coordinates: list[float]) -> dict[str, Any]:
    if not valid_point(coordinates):
        raise ValueError(f"Invalid reviewed terminal coordinates: {props.get('facility_id')}")
    properties = {k: v for k, v in props.items() if v not in (None, "", [])}
    properties.update(feature_kind="terminal", category_label=CATEGORY_LABELS[props["category"]])
    return {"type": "Feature", "properties": properties,
            "geometry": {"type": "Point", "coordinates": [round(v, 5) for v in coordinates[:2]]}}


def legacy_id(name: str) -> str:
    return "ca-legacy:" + hashlib.sha256(name.encode()).hexdigest()[:16]


def archive_properties(kind: str, raw: dict[str, Any]) -> dict[str, Any]:
    """A copied GIS edit date cannot establish current ownership or operating status."""
    product = kind == "products"
    canonical = ("https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/"
                 + ("PetroleumProduct_Terminals_US_EIA/FeatureServer/36" if product else "CrudeOil_RailTerminals_US_EIA/FeatureServer"))
    return {
        "facility_id": f"eia-{kind}-archive:{raw['FID']}",
        "reported_name": raw.get("Site") if product else raw.get("Site_Name"),
        "reported_operator": raw.get("Company") if product else None,
        "review_status": "inventory_only" if product else "historical_unverified",
        "status": "Unknown — historical inventory; current operation not verified",
        "source_as_of": "2020-01" if product else None,
        "source_date_note": "EIA-815 inventory as of January 2020" if product else "Underlying inventory date unavailable; copy edits do not establish facility currency",
        "reviewed_at": REVIEW_DATE,
        "canonical_source_url": canonical,
        "coordinate_source_id": f"FID {raw['FID']}",
        "location_confidence": "unknown",
        "location_accuracy": "Historical inventory facility point; accuracy unspecified",
        "location_note": "Archived EIA observation hosted by a university account; may overlap a separately named operator-map observation. Not a current ownership or operating-status claim.",
        "source": "EIA-815 January 2020 inventory (UC Merced copy)" if product else "EIA crude-by-rail inventory (University of Minnesota copy)",
    }


def buckeye_features() -> tuple[list[dict[str, Any]], int]:
    result, excluded = [], 0
    overrides = json.loads(REVIEWS.read_text(encoding="utf-8"))["buckeye_overrides"]
    for layer, source_name in [(1, "buckeye_terminals"), (4, "buckeye_propane_terminals")]:
        data = snapshot(source_name)
        edited = datetime.fromtimestamp(data["metadata"]["editingInfo"]["lastEditDate"] / 1000, timezone.utc).date().isoformat()
        for row in data["data"]["features"]:
            p = row["properties"]
            if p.get("state") not in US_STATES:
                excluded += 1
                continue
            result.append(feature({
                "facility_id": f"buckeye-map:{layer}:{p['objectid']}", "name": f"Buckeye {p['name']}",
                "reported_name": p["name"], "operator": "Buckeye", "reported_operator": "Buckeye",
                "country": "US", "city": p.get("city"), "state": p["state"],
                "address": p.get("address"), "postal_code": p.get("zipcode"),
                "category": "product-terminal", "commodity": p.get("products"), "modes": p.get("modality"),
                "facility_type": "Operator-listed petroleum terminal" if layer == 1 else "Operator-listed propane terminal",
                "facility_scope": "Operator-map facility point; storage units and boundaries not mapped",
                "status": "Unknown — listed on operator map; operation not independently verified",
                "review_status": "operator_verified", "reviewed_at": REVIEW_DATE,
                "source_as_of": edited, "coordinate_as_of": edited,
                "source": "Buckeye public asset map", "source_url": BUCKEYE_MAP,
                "coordinate_source_url": data["source_url"], "coordinate_source_id": f"objectid {p['objectid']}",
                "location_confidence": "medium",
                "location_accuracy": "Operator-published facility point; accuracy unspecified",
                "location_note": "Named facility point from the operator's public map, with published street address. GIS layer last edited in 2023; review date is not a new site survey or current operating-status certification.",
                **(overrides.get(str(p["objectid"]), {}) if layer == 1 else {}),
            }, row["geometry"]["coordinates"]))
    return result, excluded


def reviewed_canadian_features(legacy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))
    npri = {str(f["properties"]["NpriID"]): f["properties"] for f in snapshot("npri_2024")["data"]["features"]}
    replacements = {r["replace_name"]: r for r in reviews["canadian"] if r.get("replace_name")}
    unknown_replacements = set(replacements) - {f["properties"]["name"] for f in legacy}
    if unknown_replacements:
        raise ValueError(f"Unmatched reviewed Canadian replacements: {sorted(unknown_replacements)}")
    reviewed_ids = [r["npri_id"] for r in reviews["canadian"]]
    if len(set(reviewed_ids)) != len(reviewed_ids):
        raise ValueError("Duplicate Canadian NPRI facility review")
    result = []
    for old in legacy:
        p = dict(old["properties"])
        if p["name"] in replacements:
            continue
        p.update(facility_id=legacy_id(p["name"]), reported_name=p["name"], reported_operator=p.get("operator"),
                 review_status="historical_unverified", reviewed_at=REVIEW_DATE,
                 source_date_note="Legacy curated point; underlying source date and current identity not independently reviewed",
                 location_note="Legacy curated location. See published coordinate confidence; a prior review date does not establish survey accuracy or current operating status.")
        p["location_accuracy"] = p.get("location_confidence", "Coordinate basis unknown")
        p["location_confidence"] = "low" if "approximate" in p["location_accuracy"].lower() else "unknown"
        if not p.get("coordinate_source_url"):
            p["coordinate_source_url"] = p["source_url"]
            p["location_note"] += " Coordinate basis unverified; linked coordinate reference is the prior identity source, not a verified point dataset."
        if "decommission" not in str(p.get("status", "")).lower():
            p["status"] = "Unknown — legacy curated identity; current operation not verified"
        p.pop("last_verified", None)
        result.append(feature(p, old["geometry"]["coordinates"]))
    for r in reviews["canadian"]:
        p = npri[str(r["npri_id"])]
        # Published coordinate columns identify the reported facility point; do
        # not substitute city centres, mailing addresses, or projected estimates.
        coords = [p["Longitude"], p["Latitude"]]
        if str(r["npri_id"]) == "6907":
            raise ValueError("NPRI Edmonton-terminal longitude anomaly must remain excluded")
        props = {k: v for k, v in r.items() if k not in {"replace_name", "npri_id"}}
        props.update(facility_id=f"npri:{r['npri_id']}", country="CA", city=p["City"], state=p["ProvinceCode"],
                     reported_name=p["FacilityName"], reported_operator=p["CompanyName"],
                     reviewed_at=REVIEW_DATE, coordinate_as_of="2024", coordinate_source_url=NPRI_URL,
                     coordinate_source_id=f"NPRI {r['npri_id']}, report year {p['ReportYear']}",
                     location_confidence="medium", location_accuracy="Regulator-reported facility point; accuracy unspecified",
                     location_note=r.get("location_note", "Published 2024 NPRI facility coordinates; representative point, not a surveyed tank, cavern, loading rack, or facility boundary."),
                     status="Unknown — source-listed facility; current operation not independently verified")
        if not props.get("review_status"):
            props.update(review_status="inventory_only", source="ECCC NPRI 2024 facility inventory", source_url=NPRI_URL, source_as_of="2024")
        result.append(feature(props, coords))
    return result


def colonial_features() -> list[dict[str, Any]]:
    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))
    census = json.loads((SOURCES / "colonial_census.json").read_text(encoding="utf-8"))
    matches = {record["address"]: record["response"]["result"]["addressMatches"] for record in census["records"]}
    for row in reviews["colonial"]:
        address = f"{row['address']}, {row['city']}, {row['state']} {row['postal_code']}"
        match = matches.get(address, [])
        if len(match) != 1 or [match[0]["coordinates"]["x"], match[0]["coordinates"]["y"]] != row["coordinates"] or not match[0]["matchedAddress"].endswith(row["postal_code"]):
            raise ValueError(f"Colonial point does not match reviewed Census address evidence: {row['name']}")
    return [feature({**{k: v for k, v in r.items() if k != "coordinates"}, "country": "US", "operator": "Colonial Pipeline", "reported_operator": "Colonial Pipeline",
                     "category": "product-storage", "status": "Unknown — operator-listed facility; current operation not independently verified",
                     "review_status": "operator_verified", "reviewed_at": REVIEW_DATE,
                     "coordinate_as_of": REVIEW_DATE, "source": "Colonial Pipeline terminals page; Census street-address geocoder",
                     "source_url": "https://www.colpipe.com/our-operations/terminals/",
                     "location_confidence": "low", "location_accuracy": "Government street-address interpolation; not a surveyed facility point",
                     "location_note": "Government street-address interpolation; not an operator-published tank location or surveyed facility boundary.",
                     "storage_capacity_note": "Operator-published site capacity in barrels; page undated, reviewed 2026-10-10. Not current available capacity."},
                    r["coordinates"]) for r in reviews["colonial"]]


def us_storage_features() -> list[dict[str, Any]]:
    rows = json.loads(REVIEWS.read_text(encoding="utf-8"))["us_storage"]
    return [feature({k: v for k, v in row.items() if k != "coordinates"}, row["coordinates"]) for row in rows]


def inventory_metadata(canadian: list[dict[str, Any]], buckeye: list[dict[str, Any]], colonial: list[dict[str, Any]], excluded: int) -> dict[str, Any]:
    return {
        "terminal_review_date": REVIEW_DATE,
        "operator_map_buckeye_terminal_count": len(buckeye),
        "omitted_out_of_scope_buckeye_terminal_count": excluded,
        "colonial_address_interpolated_storage_count": len(colonial),
        "curated_canadian_terminal_count": len(canadian),
        "curated_canadian_terminal_categories": {category: sum(f["properties"]["category"] == category for f in canadian) for category in CATEGORY_LABELS},
        "terminal_inventory_note": "Source observations, not unique-site totals. Archived EIA and current operator identities are not merged on city or operator alone. Source/review dates and coordinate provenance are separate; no claim of complete national storage coverage.",
    }
