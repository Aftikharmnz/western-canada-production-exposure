"""Validate map infrastructure GeoJSON files and report known coverage caveats.

Run after rebuilding the railway, terminal, pipeline, scheme, or refinery layers:

    python scripts/validate_infrastructure_layers.py

Hard schema/geometry/provenance failures return a non-zero exit code. Coverage
differences that require a source reconciliation are printed as warnings so they
remain visible without pretending two differently scoped datasets are identical.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


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


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    rail = load_geojson("railways.geojson")
    pipeline = load_geojson("market_access_pipelines.geojson")
    schemes = load_geojson("aer_scheme_approvals.geojson")
    refineries = load_geojson("refineries.geojson")

    for name, data in [
        ("railways.geojson", rail),
        ("market_access_pipelines.geojson", pipeline),
        ("aer_scheme_approvals.geojson", schemes),
        ("refineries.geojson", refineries),
    ]:
        errors.extend(validate_geometries(name, data))

    rail_lines = [f for f in rail["features"] if f.get("properties", {}).get("feature_kind") == "rail_line"]
    terminals = [f for f in rail["features"] if f.get("properties", {}).get("feature_kind") == "terminal"]
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
        errors.append(f"railways.geojson: only {canadian_terminal_count} reviewed Canadian terminal records (expected at least 70)")
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
        "us-crude-trunk-reference",
        "us-products-reference",
        "us-hgl-reference",
    }
    missing_routes = sorted(required_routes - set(route_ids))
    if missing_routes:
        errors.append(f"market_access_pipelines.geojson: missing required routes {missing_routes}")
    for feature in route_features:
        props = feature.get("properties", {})
        if props.get("route_id", "").endswith("-reference") and props.get("default_visible") is not False:
            errors.append(f"market_access_pipelines.geojson: national reference {props.get('route_id')} must default hidden")

    statuses = Counter(f.get("properties", {}).get("plant_status_desc") or "Unknown" for f in refineries["features"])
    us_refineries = [f for f in refineries["features"] if f.get("properties", {}).get("country_name") == "U.S.A."]
    canada_refineries = [f for f in refineries["features"] if f.get("properties", {}).get("country_name") == "Canada"]
    if len(us_refineries) != 130:
        warnings.append(f"refineries.geojson: {len(us_refineries)} U.S. records; EIA 2026 reports 130 operable facilities")
    if statuses.get("Idle", 0) == 0:
        warnings.append("refineries.geojson: no idle plants are labelled; EIA 2026 reports two idle U.S. facilities")
    source_blob = json.dumps(refineries.get("source", {}), ensure_ascii=False)
    if ":/Users/" in source_blob or ":\\Users\\" in source_blob:
        errors.append("refineries.geojson: source metadata exposes a local user path")

    print(
        "Infrastructure QA: "
        f"{raw_segments:,} rail source segments -> {len(rail_lines):,} render features; "
        f"{len(terminals):,} terminals ({canadian_terminal_count} Canada); "
        f"terminal categories {dict(category_counts)}; "
        f"{len(route_features)} pipeline routes; "
        f"{len(canada_refineries)} Canada / {len(us_refineries)} U.S. refinery records."
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
