"""
Build the app-ready Major Market Access Pipelines GeoJSON.

The layer is route-level, not survey-grade. Canadian linework is pulled from the
public CER pipeline systems FeatureServer when available. U.S. continuations use
EIA Energy Atlas FeatureServers and selected county GIS where it fills a specific
gap, then each named pipeline is emitted as one map feature.

Run:
    python scripts/build_market_access_pipelines.py
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "market_access_pipelines.geojson"

CER_PIPELINES_URL = "https://services5.arcgis.com/vNzamREXvX2WcX6d/arcgis/rest/services/CER_Pipeline_Systems_WGS84_WM_v/FeatureServer/0"
EIA_CRUDE_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0"
EIA_PRODUCTS_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Petroleum_Products_Pipelines_1/FeatureServer/0"
EIA_HGL_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Hydrocarbon_Gas_Liquids_Pipelines_1/FeatureServer/0"
CAPP_MAP_URL = "https://www.capp.ca/wp-content/uploads/2024/03/CAPP-2023-Pipeline-and-Refinery-Map-36x22-wall-size.pdf"
TM_PUGET_URL = "https://www.transmountain.com/news/2019/trans-mountains-puget-sound-pipeline-shipping-products-to-washington-state-refineries-since-1954"
AER_FEEDER_PIPELINES = ROOT / "public" / "data" / "aer_feeder_pipelines.geojson"


ROUTES: list[dict[str, Any]] = [
    {
        "route_id": "enbridge-mainline-lakehead",
        "route_name": "Enbridge Mainline / Lakehead",
        "operator": "Enbridge",
        "commodity": "Crude oil / dilbit / SCO",
        "flow_role": "Major Western Canada crude export trunk",
        "direction": "Edmonton/Hardisty to U.S. Midwest, Sarnia, and downstream markets",
        "color": "#2563eb",
        "display_order": 10,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'EnbridgeMainline'"},
            {
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": "Opername = 'ENBRIDGE' AND Pipename IN ('Lakehead', 'Mainline', 'Alberta Clipper')",
                "line_filter": {"max_lon": -82.0, "max_lat": 49.2},
            },
        ],
    },
    {
        "route_id": "enbridge-line-9",
        "route_name": "Enbridge Line 9",
        "operator": "Enbridge",
        "commodity": "Crude oil",
        "flow_role": "Eastern Canada refinery and terminal access",
        "direction": "Sarnia/North Westover to Montreal corridor",
        "color": "#3b82f6",
        "display_order": 11,
        "default_visible": True,
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'EnbridgeLine9'"}],
    },
    {
        "route_id": "enbridge-bakken",
        "route_name": "Enbridge Bakken System / North Dakota",
        "operator": "Enbridge",
        "commodity": "Crude oil",
        "flow_role": "Bakken and Saskatchewan crude access into Enbridge system",
        "direction": "Saskatchewan/Bakken to Enbridge Mainline connections",
        "color": "#60a5fa",
        "display_order": 12,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'EnbridgeBakken'"},
            {"source": "EIA", "url": EIA_CRUDE_URL, "where": "Opername = 'ENBRIDGE' AND Pipename = 'North Dakota System'"},
        ],
    },
    {
        "route_id": "enbridge-us-downstream",
        "route_name": "Enbridge U.S. downstream laterals",
        "operator": "Enbridge",
        "commodity": "Crude oil / liquids",
        "flow_role": "U.S. refinery and terminal laterals connected to Enbridge crude markets",
        "direction": "Midwest, Midcontinent, Ontario border, and Gulf-area laterals",
        "color": "#93c5fd",
        "display_order": 19,
        "default_visible": False,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [
            {
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": (
                    "Opername = 'ENBRIDGE' AND Pipename IN "
                    "('Buffalo', 'Chicap', 'Kiantone pipeline', 'LSr Project', "
                    "'Midcontinent (Ozark)', 'Mustang', 'Nanticoke', 'Tinsley', 'Toledo', 'Tulsa', "
                    "'Southern Access', 'Spearhead')"
                ),
            }
        ],
    },
    {
        "route_id": "trans-mountain-puget",
        "route_name": "Trans Mountain / Puget Sound",
        "operator": "Trans Mountain",
        "commodity": "Crude oil / refined products",
        "flow_role": "Pacific Coast export, Burnaby terminal, and Washington refinery access",
        "direction": "Edmonton to Burnaby/Westridge, Sumas, Anacortes, and Ferndale/Cherry Point",
        "color": "#059669",
        "display_order": 20,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'TransMountain'"},
        ],
    },
    {
        "route_id": "keystone",
        "route_name": "Keystone",
        "operator": "South Bow / TC Energy",
        "commodity": "Crude oil",
        "flow_role": "Major Western Canada crude export trunk",
        "direction": "Hardisty to U.S. Midwest and Gulf Coast",
        "color": "#dc2626",
        "display_order": 30,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'Keystone'"},
            {
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": "Opername = 'TRANSCANADA' AND Pipename IN ('Keystone', 'Gulf Coast Project')",
                "line_filter": {"max_lat": 49.2},
            },
        ],
    },
    {
        "route_id": "express-platte",
        "route_name": "Express / Platte",
        "operator": "Express Pipeline / Platte Pipeline",
        "commodity": "Crude oil",
        "flow_role": "Western Canada crude export trunk to Rockies/Midwest",
        "direction": "Hardisty to Montana/Wyoming/Illinois corridor",
        "color": "#7c3aed",
        "display_order": 40,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'Express'"},
            {"source": "EIA", "url": EIA_CRUDE_URL, "where": "Opername = 'SPECTRA ENERGY' AND Pipename IN ('Express System', 'Platte Pipeline')"},
        ],
    },
    {
        "route_id": "southern-lights",
        "route_name": "Southern Lights",
        "operator": "Enbridge",
        "commodity": "Diluent / condensate",
        "flow_role": "Diluent import trunk into Alberta oil sands blending markets",
        "direction": "U.S. Midwest to Edmonton/Hardisty area",
        "color": "#0891b2",
        "display_order": 50,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'SouthernLights'"},
            {
                "source": "EIA",
                "url": EIA_PRODUCTS_URL,
                "where": "Opername = 'ENBRIDGE' AND Pipename = 'Southern Lights'",
                "line_filter": {"max_lat": 49.2},
            },
        ],
    },
    {
        "route_id": "cochin",
        "route_name": "Cochin",
        "operator": "Kinder Morgan / PKM Cochin",
        "commodity": "Condensate / HGL",
        "flow_role": "Condensate/HGL import trunk for diluent supply",
        "direction": "U.S. Midwest to Fort Saskatchewan area",
        "color": "#0e7490",
        "display_order": 60,
        "default_visible": True,
        "parts": [
            {"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'Cochin'"},
            {
                "source": "EIA",
                "url": EIA_HGL_URL,
                "where": "Opername = 'KINDER MORGAN' AND Pipename = 'Cochin Pipeline'",
                "line_filter": {"max_lat": 49.2},
            },
        ],
    },
    {
        "route_id": "wascana",
        "route_name": "Wascana",
        "operator": "Plains Midstream",
        "commodity": "Crude oil",
        "flow_role": "Saskatchewan/Bakken regional crude access",
        "direction": "Southeast Saskatchewan and cross-border crude access",
        "color": "#b45309",
        "display_order": 70,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'Wascana'"}],
    },
    {
        "route_id": "westspur",
        "route_name": "Westspur",
        "operator": "Kingston Midstream",
        "commodity": "Crude oil",
        "flow_role": "Southeast Saskatchewan crude gathering and market access",
        "direction": "Southeast Saskatchewan to Enbridge/Wascana connections",
        "color": "#d97706",
        "display_order": 71,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'Westspur'"}],
    },
    {
        "route_id": "rangeland-aurora-glacier",
        "route_name": "Rangeland / Aurora / Glacier",
        "operator": "Plains / Aurora / Phillips 66 / CHS",
        "commodity": "Crude oil / LVP products",
        "flow_role": "Selected other crude oil route from central Alberta to Montana/Rockies refining markets",
        "direction": "Edmonton/Sundre corridor to Carway/Cut Bank/Billings and Rockies connections",
        "color": "#9333ea",
        "display_order": 72,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [
            {
                "source": "AER",
                "local_geojson": AER_FEEDER_PIPELINES,
                "licences": ["64941", "179", "1386", "64954", "80010"],
            },
            {
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": "Opername = 'PHILLIPS 66 PIPELINE' AND Pipename = 'Glacier Pipeline'",
            },
        ],
    },
    {
        "route_id": "enbridge-lines-7-11",
        "route_name": "Enbridge Lines 7 / 11",
        "operator": "Enbridge",
        "commodity": "Crude oil / liquids",
        "flow_role": "Ontario and cross-border refinery access",
        "direction": "Ontario/New York regional Enbridge corridors",
        "color": "#bfdbfe",
        "display_order": 80,
        "default_visible": False,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID IN ('EnbridgeLine7', 'EnbridgeLine11')"}],
    },
    {
        "route_id": "trans-northern",
        "route_name": "Trans-Northern",
        "operator": "Trans-Northern Pipelines",
        "commodity": "Refined products",
        "flow_role": "Eastern refined-product distribution",
        "direction": "Ontario/Quebec refined-products corridor",
        "color": "#64748b",
        "display_order": 90,
        "default_visible": False,
        "menu_section": "Other Liquids / Products",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'TransNorthern'"}],
    },
    {
        "route_id": "other-cer-liquids",
        "route_name": "Other CER liquid systems",
        "operator": "Various",
        "commodity": "Liquid pipelines",
        "flow_role": "Other federally regulated liquid systems",
        "direction": "Various",
        "color": "#94a3b8",
        "display_order": 100,
        "default_visible": False,
        "menu_section": "Other Liquids / Products",
        "parts": [
            {
                "source": "CER",
                "url": CER_PIPELINES_URL,
                "where": "PipelineID IN ('Genesis', 'Montreal', 'NormanWells')",
            }
        ],
    },
]


MARKET_HUBS = [
    ("Hardisty", "Terminal / hub", -111.31, 52.67),
    ("Edmonton", "Refining / pipeline hub", -113.49, 53.55),
    ("Fort Saskatchewan", "Diluent / NGL hub", -113.22, 53.71),
    ("Sundre", "Rangeland corridor node", -114.64, 51.80),
    ("Carway", "Canada-U.S. border interconnect", -113.38, 49.00),
    ("Kamloops", "Pipeline terminal", -120.33, 50.67),
    ("Burnaby / Westridge", "Marine terminal / refinery market", -122.95, 49.25),
    ("Sumas", "Border / Puget Sound interconnect", -122.27, 49.00),
    ("Ferndale / Cherry Point", "Washington refinery market", -122.69, 48.86),
    ("Anacortes", "Washington refinery market", -122.61, 48.51),
    ("Regina", "Refinery / pipeline hub", -104.62, 50.45),
    ("Cromer", "Pipeline hub", -101.24, 49.73),
    ("Gretna", "Canada-U.S. border interconnect", -97.56, 49.00),
    ("Superior", "Lakehead terminal / refinery market", -92.10, 46.72),
    ("Sarnia", "Refinery / petrochemical market", -82.39, 42.98),
    ("Montreal", "Refinery / terminal market", -73.57, 45.50),
    ("Cut Bank", "Montana hub", -112.33, 48.63),
    ("Billings", "Refinery market", -108.50, 45.78),
    ("Guernsey", "Pipeline hub", -104.74, 42.27),
    ("Casper", "Pipeline hub / refinery market", -106.31, 42.85),
    ("Patoka", "Midwest crude hub", -89.09, 38.75),
    ("Wood River", "Midwest refinery market", -90.20, 38.86),
    ("Cushing", "U.S. crude hub", -96.77, 35.99),
    ("Steele City", "Pipeline interconnect", -97.02, 40.04),
]


def request_json(url: str, retries: int = 3) -> dict[str, Any]:
    headers = {"User-Agent": "western-canada-production-exposure/market-access-builder"}
    req = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Request failed after {retries} attempts: {url}") from last_error


def query_arcgis_geojson(service_url: str, where: str, page_size: int = 2000) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultRecordCount": str(page_size),
            "resultOffset": str(offset),
        }
        url = f"{service_url}/query?{urllib.parse.urlencode(params)}"
        data = request_json(url)
        page = data.get("features") or []
        features.extend(page)
        if not data.get("exceededTransferLimit") or not page:
            break
        offset += len(page)
    return features


def query_local_geojson(path: Path, part: dict[str, Any]) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    licences = {str(value) for value in part.get("licences", [])}
    statuses = {str(value) for value in part.get("statuses", ["Operating"])}

    selected: list[dict[str, Any]] = []
    for feature in features:
        properties = feature.get("properties") or {}
        if licences and str(properties.get("licence")) not in licences:
            continue
        if statuses and str(properties.get("status")) not in statuses:
            continue
        selected.append(feature)
    return selected


def feature_lines(feature: dict[str, Any]) -> list[list[list[float]]]:
    geometry = feature.get("geometry") or {}
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geom_type == "LineString":
        return [coords]
    if geom_type == "MultiLineString":
        return coords
    return []


def line_bbox(line: list[list[float]]) -> tuple[float, float, float, float]:
    lons = [float(point[0]) for point in line]
    lats = [float(point[1]) for point in line]
    return min(lons), max(lons), min(lats), max(lats)


def line_max_segment_km(line: list[list[float]]) -> float:
    max_segment = 0.0
    for a, b in zip(line, line[1:]):
        # Approximate enough for QA filtering in western Canada / northern U.S.
        dx = (float(a[0]) - float(b[0])) * 85.0
        dy = (float(a[1]) - float(b[1])) * 111.0
        max_segment = max(max_segment, math.hypot(dx, dy))
    return max_segment


def line_allowed(line: list[list[float]], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    min_lon, max_lon, min_lat, max_lat = line_bbox(line)
    if "min_lon" in filters and min_lon < float(filters["min_lon"]):
        return False
    if "max_lon" in filters and max_lon > float(filters["max_lon"]):
        return False
    if "min_lat" in filters and min_lat < float(filters["min_lat"]):
        return False
    if "max_lat" in filters and max_lat > float(filters["max_lat"]):
        return False
    if "max_segment_km" in filters and line_max_segment_km(line) > float(filters["max_segment_km"]):
        return False
    return True


def geometry_from_lines(lines: list[list[list[float]]]) -> dict[str, Any]:
    if len(lines) == 1:
        return {"type": "LineString", "coordinates": lines[0]}
    return {"type": "MultiLineString", "coordinates": lines}


def source_reference(part: dict[str, Any]) -> str:
    if part.get("url"):
        return str(part["url"])
    path = Path(part["local_geojson"])
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def route_feature(route: dict[str, Any], include_remote: bool) -> tuple[dict[str, Any] | None, list[str]]:
    lines: list[list[list[float]]] = []
    sources: list[str] = []
    warnings: list[str] = []

    for part in route.get("parts", []):
        if part.get("local_geojson"):
            path = Path(part["local_geojson"])
            try:
                part_features = query_local_geojson(path, part)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{route['route_name']}: {part['source']} local read failed: {exc}")
                continue
            for feature in part_features:
                lines.extend(line for line in feature_lines(feature) if line_allowed(line, part.get("line_filter")))
            if part_features:
                sources.append(f"{part['source']} ({len(part_features)} local feature{'s' if len(part_features) != 1 else ''})")
            continue

        if not include_remote:
            continue
        try:
            part_features = query_arcgis_geojson(part["url"], part["where"])
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{route['route_name']}: {part['source']} query failed: {exc}")
            continue
        for feature in part_features:
            lines.extend(line for line in feature_lines(feature) if line_allowed(line, part.get("line_filter")))
        if part_features:
            sources.append(f"{part['source']} ({len(part_features)} feature{'s' if len(part_features) != 1 else ''})")

    if not lines:
        warnings.append(f"{route['route_name']}: no geometry returned")
        return None, warnings

    unique_lines: list[list[list[float]]] = []
    seen_lines: set[str] = set()
    for line in lines:
        line_key = json.dumps(line, separators=(",", ":"))
        if line_key in seen_lines:
            continue
        seen_lines.add(line_key)
        unique_lines.append(line)
    lines = unique_lines

    properties = {
        "feature_kind": "pipeline",
        "route_id": route["route_id"],
        "route_name": route["route_name"],
        "operator": route["operator"],
        "commodity": route["commodity"],
        "flow_role": route["flow_role"],
        "direction": route["direction"],
        "color": route["color"],
        "display_order": route["display_order"],
        "default_visible": bool(route.get("default_visible", True)),
        "menu_section": route.get("menu_section", "Core Market Access Pipelines"),
        "source_summary": "; ".join(sources),
        "source_urls": sorted({source_reference(part) for part in route.get("parts", [])}),
        "geometry_confidence": "public GIS linework, route-level display",
    }
    return {"type": "Feature", "properties": properties, "geometry": geometry_from_lines(lines)}, warnings


def hub_feature(name: str, hub_type: str, lon: float, lat: float) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "hub",
            "name": name,
            "hub_type": hub_type,
            "source_summary": "CAPP map route-node reference and public geographic coordinates",
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def build_feature_collection(include_remote: bool) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    warnings: list[str] = []

    for route in ROUTES:
        feature, route_warnings = route_feature(route, include_remote=include_remote)
        warnings.extend(route_warnings)
        if feature:
            features.append(feature)
            print(f"{route['route_name']}: {feature['properties']['source_summary']}", file=sys.stderr)

    features.extend(hub_feature(*hub) for hub in MARKET_HUBS)

    return {
        "type": "FeatureCollection",
        "metadata": {
            "name": "Major Market Access Pipelines",
            "description": "Named Western Canada crude, condensate/diluent, and connected market-access routes plus hub points.",
            "generated_with": "scripts/build_market_access_pipelines.py",
            "source_notes": [
                "Canadian federally regulated liquid linework is selected from the public CER pipeline systems FeatureServer.",
                "Alberta Rangeland/Aurora corridor linework uses local AER feeder pipeline features where public licences identify operating Plains/Aurora segments.",
                "U.S. continuations are selected from EIA Energy Atlas FeatureServers where available; coarse EIA chords that duplicate Canadian CER linework are filtered out.",
                "Route-level manual connectors are intentionally excluded to avoid straight-line artifacts over water or across border gaps.",
                "CAPP's 2023 Pipeline and Refinery Map is used as route/hub reference, not as coordinate geometry.",
                "Analytical context only; not for construction, excavation, or ground disturbance.",
            ],
            "source_urls": {
                "cer_pipeline_systems": CER_PIPELINES_URL,
                "eia_crude": EIA_CRUDE_URL,
                "eia_products": EIA_PRODUCTS_URL,
                "eia_hgl": EIA_HGL_URL,
                "aer_feeder_pipelines": AER_FEEDER_PIPELINES.relative_to(ROOT).as_posix(),
                "capp_reference_map": CAPP_MAP_URL,
                "trans_mountain_puget_reference": TM_PUGET_URL,
            },
            "warnings": warnings,
        },
        "features": features,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Build only local content. Useful for UI tests when network is unavailable.",
    )
    args = parser.parse_args()

    collection = build_feature_collection(include_remote=not args.local_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(collection, separators=(",", ":")), encoding="utf-8")
    size_mb = args.output.stat().st_size / (1024 * 1024)
    pipeline_count = sum(1 for f in collection["features"] if f["properties"].get("feature_kind") == "pipeline")
    hub_count = sum(1 for f in collection["features"] if f["properties"].get("feature_kind") == "hub")
    print(f"Wrote {pipeline_count} pipelines and {hub_count} hubs to {args.output} ({size_mb:.2f} MB)")
    if collection["metadata"]["warnings"]:
        print("Build warnings:")
        for warning in collection["metadata"]["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
