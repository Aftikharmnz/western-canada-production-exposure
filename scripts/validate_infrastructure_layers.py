"""Validate map infrastructure GeoJSON files and report known coverage caveats.

Run after rebuilding the railway, terminal, pipeline, scheme, or refinery layers:

    python scripts/validate_infrastructure_layers.py

Hard schema/geometry/provenance failures return a non-zero exit code. Coverage
differences that require a source reconciliation are printed as warnings so they
remain visible without pretending two differently scoped datasets are identical.
"""

from __future__ import annotations

import json
import argparse
import math
import sys
import urllib.parse
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from terminal_inventory import terminal_detail_errors, valid_capacity_value
from enbridge_lines import published_catalogue_errors


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"


def load_geojson(name: str) -> dict[str, Any]:
    path = DATA / name
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError(f"{name}: expected a GeoJSON FeatureCollection")
    return data


def positions(coords: Any) -> Iterable[list[Any]]:
    if (
        isinstance(coords, list)
        and len(coords) >= 2
        and isinstance(coords[0], (int, float))
        and isinstance(coords[1], (int, float))
    ):
        yield coords
        return
    if isinstance(coords, list):
        for child in coords:
            yield from positions(child)


def geometry_errors(geometry: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type not in {"Point", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}:
        return [f"{label}: unsupported/missing geometry type {geom_type!r}"]
    points = list(positions(coords))
    if not points:
        return [f"{label}: empty geometry"]
    for point in points:
        lon, lat = point[:2]
        if not math.isfinite(float(lon)) or not math.isfinite(float(lat)):
            errors.append(f"{label}: non-finite coordinate")
            break
        if not (-180 <= float(lon) <= 180 and -90 <= float(lat) <= 90):
            errors.append(f"{label}: out-of-range coordinate [{lon}, {lat}]")
            break
    if geom_type == "LineString" and len(coords or []) < 2:
        errors.append(f"{label}: LineString has fewer than two positions")
    if geom_type == "MultiLineString":
        for index, line in enumerate(coords or []):
            if len(line) < 2:
                errors.append(f"{label}: MultiLineString part {index} has fewer than two positions")
    polygons = [coords] if geom_type == "Polygon" else (coords if geom_type == "MultiPolygon" else [])
    for polygon_index, polygon in enumerate(polygons or []):
        for ring_index, ring in enumerate(polygon or []):
            if len(ring) < 4:
                errors.append(f"{label}: polygon {polygon_index} ring {ring_index} has fewer than four positions")
            elif ring[0][:2] != ring[-1][:2]:
                errors.append(f"{label}: polygon {polygon_index} ring {ring_index} is not closed")
    return errors


def validate_geometries(name: str, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, feature in enumerate(data["features"]):
        errors.extend(geometry_errors(feature.get("geometry") or {}, f"{name} feature {index}"))
    return errors


def validate_terminal_inventory(data: dict[str, Any]) -> list[str]:
    """Do not publish ambiguous IDs or unsupported location/identity claims."""
    errors: list[str] = []
    seen: set[str] = set()
    categories = {"crude-rail-terminal", "crude-terminal", "product-terminal", "inactive-terminal",
                  "crude-storage", "product-storage", "ngl-storage"}
    for index, feature in enumerate(data.get("features", [])):
        props = feature.get("properties") or {}
        if props.get("feature_kind") != "terminal":
            continue
        label = f"railways.geojson terminal {index} ({props.get('name', 'unnamed')})"
        facility_id = props.get("facility_id")
        if not isinstance(facility_id, str) or not facility_id.strip() or facility_id in seen:
            errors.append(f"{label}: missing or duplicate facility ID")
        else:
            seen.add(facility_id)
        if feature.get("geometry", {}).get("type") != "Point":
            errors.append(f"{label}: facility must have point geometry")
        if props.get("category") not in categories:
            errors.append(f"{label}: unsupported terminal/storage category")
        if props.get("review_status") not in {"operator_verified", "inventory_only", "historical_unverified"}:
            errors.append(f"{label}: missing or unsupported identity review status")
        for field in ("source_url", "coordinate_source_url"):
            value = props.get(field)
            try:
                parsed = urllib.parse.urlsplit(value) if isinstance(value, str) else None
            except ValueError:
                parsed = None
            if not parsed or parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                errors.append(f"{label}: {field} must identify a public HTTP(S) source")
        if not props.get("location_note") or props.get("location_confidence") not in {"exact", "high", "medium", "low", "unknown"}:
            errors.append(f"{label}: location evidence and accuracy label required")
        if props.get("source_as_of") is not None and not isinstance(props["source_as_of"], str):
            errors.append(f"{label}: source date must be a published string or null")
        if props.get("review_status") == "operator_verified":
            try:
                reviewed = props.get("reviewed_at") or ""
                if date.fromisoformat(reviewed).isoformat() != reviewed:
                    raise ValueError("Use YYYY-MM-DD")
            except (ValueError, TypeError):
                errors.append(f"{label}: operator review requires a calendar date")
            if not props.get("operator"):
                errors.append(f"{label}: operator review requires an identified operator")
        capacity = props.get("storage_capacity_bbl")
        if capacity is not None and not valid_capacity_value(capacity):
            errors.append(f"{label}: barrel storage capacity must be positive, finite and numeric; missing is not zero")
        if capacity is not None and not props.get("storage_capacity_note"):
            errors.append(f"{label}: storage capacity requires a source/basis note")
        errors.extend(terminal_detail_errors(props, label))
    return errors


def validate_product_networks(data: dict[str, Any]) -> list[str]:
    errors = []
    rows = [feature.get("properties", {}) for feature in data.get("features", [])
            if str(feature.get("properties", {}).get("route_id", "")).startswith("us-products-")]
    if any(row.get("route_id") == "us-products-reference" for row in rows):
        errors.append("market_access_pipelines.geojson: aggregate products reference must not be selectable")
    metadata = data.get("metadata", {}).get("product_networks") or {}
    expected = metadata.get("source_feature_count")
    if type(expected) is not int or expected <= 0:
        errors.append("market_access_pipelines.geojson: missing EIA product source count")
    if metadata.get("network_count") != len(rows):
        errors.append("market_access_pipelines.geojson: named product group count does not match metadata")
    source_ids = []
    for row in rows:
        label = row.get("route_id")
        ids = row.get("source_feature_ids")
        if not isinstance(ids, list) or not ids or any(type(value) is not int for value in ids):
            errors.append(f"market_access_pipelines.geojson: {label} requires source FIDs")
            continue
        source_ids.extend(ids)
        if row.get("source_feature_count") != len(ids):
            errors.append(f"market_access_pipelines.geojson: {label} source feature count mismatch")
        reviewed_menu = (row.get("pipeline_details") or {}).get("menu_section", "U.S. refined-product networks")
        if row.get("default_visible") is not False or row.get("menu_section") != reviewed_menu:
            errors.append(f"market_access_pipelines.geojson: {label} must be a separate optional product selection")
        for key in ("source_operator_names", "source_pipeline_names"):
            if not isinstance(row.get(key), list):
                errors.append(f"market_access_pipelines.geojson: {label} missing {key}")
        if not row.get("source_as_of") or not row.get("network_identity_basis") or not row.get("review_status"):
            errors.append(f"market_access_pipelines.geojson: {label} missing identity/date limitations")
    if len(source_ids) != len(set(source_ids)):
        errors.append("market_access_pipelines.geojson: EIA product FIDs assigned more than once")
    if len(source_ids) != expected:
        errors.append(f"market_access_pipelines.geojson: named product groups retain {len(source_ids)} source FIDs; expected {expected}")
    return errors


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    rail = load_geojson("railways.geojson")
    pipeline = load_geojson("market_access_pipelines.geojson")
    schemes = load_geojson("aer_scheme_approvals.geojson")
    refineries = load_geojson("refineries.geojson")
    feeders = load_geojson("aer_feeder_pipelines.geojson")
    installations = load_geojson("aer_pipeline_installations.geojson")

    for name, data in [
        ("railways.geojson", rail),
        ("market_access_pipelines.geojson", pipeline),
        ("aer_scheme_approvals.geojson", schemes),
        ("refineries.geojson", refineries),
        ("aer_feeder_pipelines.geojson", feeders),
        ("aer_pipeline_installations.geojson", installations),
    ]:
        errors.extend(validate_geometries(name, data))

    aer_index_path = DATA / "aer_pipeline_index.json"
    if aer_index_path.exists():
        aer_index = json.loads(aer_index_path.read_text(encoding="utf-8"))
        if aer_index.get("builder_version", 0):
            from build_aer_infrastructure import validate_outputs
            errors.extend(validate_outputs(DATA))

    rail_lines = [f for f in rail["features"] if f.get("properties", {}).get("feature_kind") == "rail_line"]
    terminals = [f for f in rail["features"] if f.get("properties", {}).get("feature_kind") == "terminal"]
    errors.extend(validate_terminal_inventory(rail))
    raw_segments = sum(int(f.get("properties", {}).get("segment_count") or 1) for f in rail_lines)
    metadata_raw = int(rail.get("metadata", {}).get("raw_rail_segment_count") or 0)
    if metadata_raw and raw_segments != metadata_raw:
        errors.append(f"railways.geojson: grouped segment total {raw_segments:,} != metadata {metadata_raw:,}")
    if len(rail_lines) > 5000:
        errors.append(f"railways.geojson: {len(rail_lines):,} rendered line features exceeds the 5,000 performance guardrail")
    missing_terminal_country = [f for f in terminals if not f.get("properties", {}).get("country")]
    if missing_terminal_country:
        errors.append(f"railways.geojson: {len(missing_terminal_country)} terminal records lack country")
    category_counts = Counter(f.get("properties", {}).get("category") for f in terminals)
    canadian_terminal_count = sum(f.get("properties", {}).get("country") == "CA" for f in terminals)
    if canadian_terminal_count < 70:
        errors.append(f"railways.geojson: only {canadian_terminal_count} Canadian inventory records (expected at least 70)")
    scope = str(rail.get("metadata", {}).get("scope") or "").lower()
    if "all canada and all u.s. rail lines" in scope:
        errors.append("railways.geojson: metadata still makes a literal all-rail-lines claim")

    route_features = [f for f in pipeline["features"] if f.get("properties", {}).get("feature_kind") == "pipeline"]
    route_ids = [f.get("properties", {}).get("route_id") for f in route_features]
    duplicate_route_ids = [key for key, count in Counter(route_ids).items() if key and count > 1]
    if duplicate_route_ids:
        errors.append(f"market_access_pipelines.geojson: duplicate route IDs {duplicate_route_ids}")
    required_routes = {
        "imperial-sarnia-products",
        "sun-canadian",
        "valero-pipeline-saint-laurent",
        "vantage",
        "norman-wells",
        "us-crude-trunk-reference",
        "us-products-buckeye",
        "us-products-colonial",
        "us-hgl-reference",
    }
    missing_routes = sorted(required_routes - set(route_ids))
    if missing_routes:
        errors.append(f"market_access_pipelines.geojson: missing required routes {missing_routes}")
    errors.extend(validate_product_networks(pipeline))
    errors.extend(published_catalogue_errors(DATA / "enbridge_liquids_lines.json",
                                            ROOT / "data" / "enbridge_liquids_lines.json",
                                            routes=DATA / "market_access_pipelines.geojson"))
    for feature in route_features:
        props = feature.get("properties", {})
        if props.get("route_id", "").endswith("-reference") and props.get("default_visible") is not False:
            errors.append(f"market_access_pipelines.geojson: national reference {props.get('route_id')} must default hidden")

    statuses = Counter(f.get("properties", {}).get("plant_status_desc") or "Unknown" for f in refineries["features"])
    us_refineries = [f for f in refineries["features"] if f.get("properties", {}).get("country_name") == "U.S.A."]
    canada_refineries = [f for f in refineries["features"] if f.get("properties", {}).get("country_name") == "Canada"]
    if len(us_refineries) != 130:
        warnings.append(f"refineries.geojson: {len(us_refineries)} U.S. records; EIA 2026 reports 130 operable facilities")
    us_idle_count = sum(str(f.get("properties", {}).get("plant_status_desc", "")).lower().startswith("idle") for f in us_refineries)
    if us_idle_count == 0:
        warnings.append("refineries.geojson: no idle plants are labelled; EIA 2026 reports two idle U.S. facilities")
    plant_ids = [f.get("properties", {}).get("plant_id") for f in refineries["features"]]
    if len(set(plant_ids)) != len(plant_ids) or None in plant_ids:
        errors.append("refineries.geojson: duplicate or missing plant IDs")
    source_blob = json.dumps(refineries.get("source", {}), ensure_ascii=False)
    if ":/Users/" in source_blob or ":\\Users\\" in source_blob:
        errors.append("refineries.geojson: source metadata exposes a local user path")

    print(
        "Infrastructure QA: "
        f"{raw_segments:,} rail source segments -> {len(rail_lines):,} render features; "
        f"{len(terminals):,} terminals ({canadian_terminal_count} Canada); "
        f"terminal categories {dict(category_counts)}; "
        f"{len(route_features)} pipeline routes; "
        f"{len(canada_refineries)} Canada / {len(us_refineries)} U.S. refinery records ({us_idle_count} dated idle)."
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    DATA = parser.parse_args().data_dir.resolve()
    raise SystemExit(main())
