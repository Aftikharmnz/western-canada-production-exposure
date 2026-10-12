"""Reproducible reviewed terminal observations, with separate identity and location provenance.

Source snapshots are committed public facts, not a claim of live operating status.
Only explicit facility identity replacements deduplicate the older Canadian list.
Historical EIA observations remain separate from operator-map observations.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "terminal_sources"
REVIEWS = ROOT / "data" / "terminal_facility_reviews.json"
TERMINAL_DETAIL_FILES = (ROOT / "data" / "terminal_details_canada.json", ROOT / "data" / "terminal_details_us.json")
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
FACILITY_ROLES = {"storage", "terminal", "both", "processing", "unknown"}
CAPACITY_UNITS = {"bbl", "m3", "tonnes", "gal", "L"}
CAPACITY_BASES = {"published_total", "working", "shell", "unspecified"}
DETAIL_FIELDS = {"facility_id", "identity_match_note", "facility_role", "facility_role_note", "stored_products",
                 "handled_products", "storage_capacities", "services", "modes", "pipeline_connections", "detail_sources"}


def valid_source_url(value: Any) -> bool:
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                and not parsed.username and not parsed.password and parsed.port != 0)
    except ValueError:
        return False


def valid_source_date(value: Any, *, complete: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if complete:
        return False
    if re.fullmatch(r"\d{4}", value):
        return 1 <= int(value) <= 9999
    if re.fullmatch(r"\d{4}-\d{2}", value):
        return 1 <= int(value[:4]) <= 9999 and 1 <= int(value[5:]) <= 12
    return False


def valid_capacity_value(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return value > 0 and math.isfinite(value)
    except OverflowError:
        return False


def terminal_detail_errors(record: Any, label: str, *, review_record: bool = False) -> list[str]:
    """Validate explicit detail facts; product/role/capacity values are never inferred."""
    if not isinstance(record, dict):
        return [f"{label}: detail record must be an object"]
    errors = []
    if review_record:
        if set(record) - DETAIL_FIELDS:
            errors.append(f"{label}: unsupported detail fields {sorted(set(record) - DETAIL_FIELDS)}")
        for key in ("facility_id", "identity_match_note"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                errors.append(f"{label}: {key} must be a nonempty string")
    if not isinstance(record.get("facility_role"), str) or record["facility_role"] not in FACILITY_ROLES:
        errors.append(f"{label}: missing or unsupported facility role")
    if not isinstance(record.get("facility_role_note"), str) or not record["facility_role_note"].strip():
        errors.append(f"{label}: facility role requires an evidence/limitation note")
    for key in ("stored_products", "handled_products"):
        values = record.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            errors.append(f"{label}: {key} must be an explicit list of product names (empty when unknown)")
        elif len(set(values)) != len(values):
            errors.append(f"{label}: {key} contains duplicate product names")
    for key in ("services", "modes", "pipeline_connections"):
        if key in record and (not isinstance(record[key], str) or not record[key].strip()):
            errors.append(f"{label}: {key} must be an explicit nonempty source statement")
    capacities = record.get("storage_capacities")
    if not isinstance(capacities, list):
        errors.append(f"{label}: storage_capacities must be a list (empty when unpublished)")
        capacities = []
    for index, capacity in enumerate(capacities):
        prefix = f"{label} capacity {index}"
        if not isinstance(capacity, dict):
            errors.append(f"{prefix}: capacity must be an object")
            continue
        allowed = {"value", "unit", "scope", "basis", "source_url", "source_as_of", "reviewed_at", "note"}
        if set(capacity) - allowed:
            errors.append(f"{prefix}: unsupported capacity fields {sorted(set(capacity) - allowed)}")
        value = capacity.get("value")
        if not valid_capacity_value(value):
            errors.append(f"{prefix}: value must be positive, finite and numeric; missing capacity is not zero")
        if (not isinstance(capacity.get("unit"), str) or capacity["unit"] not in CAPACITY_UNITS
                or not isinstance(capacity.get("basis"), str) or capacity["basis"] not in CAPACITY_BASES):
            errors.append(f"{prefix}: explicit supported unit and capacity basis required")
        for key in ("scope", "note"):
            if not isinstance(capacity.get(key), str) or not capacity[key].strip():
                errors.append(f"{prefix}: explicit {key} required")
        if not valid_source_url(capacity.get("source_url")):
            errors.append(f"{prefix}: safe public HTTP(S) source_url required")
        if not valid_source_date(capacity.get("reviewed_at"), complete=True):
            errors.append(f"{prefix}: reviewed_at requires a calendar date")
        if capacity.get("source_as_of") is not None and not valid_source_date(capacity["source_as_of"]):
            errors.append(f"{prefix}: source_as_of requires a published year, month or calendar date")
    sources = record.get("detail_sources")
    if not isinstance(sources, list):
        errors.append(f"{label}: detail_sources must be a list")
        sources = []
    if (review_record or record.get("facility_role") != "unknown") and not sources:
        errors.append(f"{label}: reviewed facility role requires detail source evidence")
    for index, source in enumerate(sources):
        prefix = f"{label} detail source {index}"
        if not isinstance(source, dict):
            errors.append(f"{prefix}: source must be an object")
            continue
        if set(source) - {"label", "url", "as_of"}:
            errors.append(f"{prefix}: unsupported source fields")
        if not isinstance(source.get("label"), str) or not source["label"].strip() or not valid_source_url(source.get("url")):
            errors.append(f"{prefix}: nonempty label and safe public HTTP(S) URL required")
        if source.get("as_of") is not None and not valid_source_date(source["as_of"]):
            errors.append(f"{prefix}: as_of requires a published year, month or calendar date")
    if record.get("details_reviewed_at") is not None and not valid_source_date(record["details_reviewed_at"], complete=True):
        errors.append(f"{label}: details_reviewed_at requires a calendar date")
    return errors


def baseline_terminal_details(props: dict[str, Any]) -> dict[str, Any]:
    details = {
        "facility_role": props.get("facility_role", "unknown"),
        "facility_role_note": props.get("facility_role_note", "Facility role has not been independently reviewed; an inventory category does not establish storage, handling or processing capabilities."),
        "stored_products": copy.deepcopy(props.get("stored_products", [])),
        "handled_products": copy.deepcopy(props.get("handled_products", [])),
        "storage_capacities": copy.deepcopy(props.get("storage_capacities", [])),
        "detail_sources": copy.deepcopy(props.get("detail_sources", [])),
    }
    if "storage_capacities" not in props and props.get("storage_capacity_bbl") is not None:
        # The legacy field explicitly declares barrels. Preserve its published
        # observation and unknown basis, rather than converting or summing it.
        capacity = {"value": props["storage_capacity_bbl"], "unit": "bbl", "basis": "unspecified",
                    "scope": f"Reported site storage capacity for {props.get('name', 'the named facility')}; not further subdivided in the retained source note",
                    "source_url": props.get("source_url"), "reviewed_at": props.get("reviewed_at"),
                    "note": props.get("storage_capacity_note")}
        if props.get("source_as_of") is not None:
            capacity["source_as_of"] = props["source_as_of"]
        details["storage_capacities"] = [capacity]
    return details


def load_terminal_details(paths: tuple[Path, ...] | None = None) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in TERMINAL_DETAIL_FILES if paths is None else paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(payload, dict) or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1
                or not valid_source_date(payload.get("reviewed_at"), complete=True) or not isinstance(payload.get("facilities"), list)):
            raise ValueError(f"{path.name}: invalid terminal details schema/version/review date")
        for index, record in enumerate(payload["facilities"]):
            label = f"{path.name} facility {index}"
            errors = terminal_detail_errors(record, label, review_record=True)
            if errors:
                raise ValueError("; ".join(errors))
            facility_id = record["facility_id"]
            if facility_id in records:
                raise ValueError(f"{label}: duplicate reviewed facility ID {facility_id}")
            records[facility_id] = {**copy.deepcopy(record), "details_reviewed_at": payload["reviewed_at"]}
    return records


def apply_terminal_details(features: list[dict[str, Any]], paths: tuple[Path, ...] | None = None) -> list[dict[str, Any]]:
    records = load_terminal_details(paths)
    terminals = [f for f in features if f.get("properties", {}).get("feature_kind") == "terminal"]
    ids = [f["properties"].get("facility_id") for f in terminals]
    if any(not isinstance(value, str) or not value.strip() for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Terminal detail join requires unique nonempty existing facility IDs")
    unmatched = set(records) - set(ids)
    if unmatched:
        raise ValueError(f"Unmatched reviewed terminal detail facility IDs: {sorted(unmatched)}")
    result = []
    for feature in features:
        if feature.get("properties", {}).get("feature_kind") != "terminal":
            result.append(feature)
            continue
        props = copy.deepcopy(feature["properties"])
        props.update(baseline_terminal_details(props))
        if props["facility_id"] in records:
            props.update(copy.deepcopy(records[props["facility_id"]]))
            # A normalized review is authoritative, including an empty list.
            props.pop("storage_capacity_bbl", None)
            props.pop("storage_capacity_note", None)
        errors = terminal_detail_errors(props, f"Terminal {props['facility_id']}")
        if errors:
            raise ValueError("; ".join(errors))
        result.append({**feature, "properties": props})
    return result


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
    properties.update(baseline_terminal_details(props))
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
        **baseline_terminal_details({}),
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
                "facility_role": "terminal",
                "facility_role_note": "The operator explicitly lists this as a terminal. Storage capabilities have not been confirmed by this baseline identity record; this does not establish the absence of tanks.",
                "detail_sources": [{"label": "Buckeye operator asset map identifies the named terminal", "url": BUCKEYE_MAP, "as_of": edited}],
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
