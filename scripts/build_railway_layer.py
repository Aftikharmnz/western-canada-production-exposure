"""
Build the app-ready railways GeoJSON layer.

The layer is an analytical context overlay for crude-by-rail and refined-product
rail logistics. Rail linework comes from the BTS/FRA North American Rail Network
and terminal points come from EIA public petroleum infrastructure layers.

Run:
    python scripts/build_railway_layer.py
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "railways.geojson"

NARN_LINES_URL = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0"
EIA_CRUDE_RAIL_TERMINALS_URL = "https://services.arcgis.com/8df8p0NlLFEShl0r/ArcGIS/rest/services/CrudeOil_RailTerminals_US_EIA_3340393128070186484/FeatureServer/0"
EIA_PRODUCT_TERMINALS_URL = "https://services2.arcgis.com/wx8u046p68e0iGuj/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/0"

# Full Canadian rail network plus U.S. states that are part of the common
# Canada/Bakken crude and refined-product rail supply chain: border states,
# Midwest/Great Lakes refining corridors, Rockies/Pacific corridors, and the
# Midcontinent/Gulf route to Cushing and Texas/Louisiana export/refining markets.
SUPPLY_CHAIN_US_STATES = [
    "WA",
    "OR",
    "CA",
    "ID",
    "MT",
    "WY",
    "CO",
    "ND",
    "SD",
    "NE",
    "KS",
    "OK",
    "TX",
    "LA",
    "MN",
    "IA",
    "MO",
    "WI",
    "IL",
    "IN",
    "MI",
    "OH",
    "PA",
    "NY",
    "VT",
    "NH",
    "ME",
    "MA",
    "CT",
    "RI",
    "NJ",
    "DE",
    "MD",
]
SUPPLY_CHAIN_US_STATE_NAMES = [
    "Washington",
    "Oregon",
    "California",
    "Idaho",
    "Montana",
    "Wyoming",
    "Colorado",
    "North Dakota",
    "South Dakota",
    "Nebraska",
    "Kansas",
    "Oklahoma",
    "Texas",
    "Louisiana",
    "Minnesota",
    "Iowa",
    "Missouri",
    "Wisconsin",
    "Illinois",
    "Indiana",
    "Michigan",
    "Ohio",
    "Pennsylvania",
    "New York",
    "Vermont",
    "New Hampshire",
    "Maine",
    "Massachusetts",
    "Connecticut",
    "Rhode Island",
    "New Jersey",
    "Delaware",
    "Maryland",
]
DEFAULT_BBOX = (-170.0, 24.0, -52.0, 72.0)
DEFAULT_RAIL_WHERE = (
    "(COUNTRY = 'CA' OR (COUNTRY = 'US' AND STATEAB IN ({}))) "
    "AND NET IN ('M', 'I')"
).format(",".join(f"'{state}'" for state in SUPPLY_CHAIN_US_STATES))
DEFAULT_CRUDE_TERMINAL_WHERE = "STATE IN ({})".format(",".join(f"'{state}'" for state in SUPPLY_CHAIN_US_STATES))
DEFAULT_PRODUCT_TERMINAL_WHERE = "State_Name IN ({})".format(",".join(f"'{state}'" for state in SUPPLY_CHAIN_US_STATE_NAMES))

RAIL_OUT_FIELDS = ",".join(
    [
        "OBJECTID",
        "FRAARCID",
        "COUNTRY",
        "STATEAB",
        "RROWNER1",
        "RROWNER2",
        "RROWNER3",
        "TRKRGHTS1",
        "TRKRGHTS2",
        "TRKRGHTS3",
        "DIVISION",
        "SUBDIV",
        "BRANCH",
        "YARDNAME",
        "PASSNGR",
        "STRACNET",
        "TRACKS",
        "NET",
        "MILES",
        "KM",
    ]
)


def request_json(url: str, retries: int = 3) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "western-canada-production-exposure/railway-builder"})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Request failed after {retries} attempts: {url}") from last_error


def query_arcgis_geojson(
    service_url: str,
    *,
    where: str = "1=1",
    out_fields: str = "*",
    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
    page_size: int = 2000,
) -> list[dict[str, Any]]:
    min_lon, min_lat, max_lon, max_lat = bbox
    geometry = json.dumps(
        {
            "xmin": min_lon,
            "ymin": min_lat,
            "xmax": max_lon,
            "ymax": max_lat,
            "spatialReference": {"wkid": 4326},
        },
        separators=(",", ":"),
    )
    features: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "geometry": geometry,
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "f": "geojson",
            "resultRecordCount": str(page_size),
            "resultOffset": str(offset),
        }
        data = request_json(f"{service_url}/query?{urllib.parse.urlencode(params)}")
        page = data.get("features") or []
        features.extend(page)
        if not page:
            break
        if not data.get("exceededTransferLimit") and len(page) < page_size:
            break
        offset += len(page)
    return features


def round_coord(value: Any) -> float:
    return round(float(value), 4)


def rounded_geometry(geometry: dict[str, Any]) -> dict[str, Any] | None:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
        return {"type": "Point", "coordinates": [round_coord(coords[0]), round_coord(coords[1])]}
    if geom_type == "LineString" and isinstance(coords, list):
        return {"type": "LineString", "coordinates": [[round_coord(x), round_coord(y)] for x, y, *_ in coords]}
    if geom_type == "MultiLineString" and isinstance(coords, list):
        return {
            "type": "MultiLineString",
            "coordinates": [
                [[round_coord(x), round_coord(y)] for x, y, *_ in line]
                for line in coords
                if isinstance(line, list) and len(line) >= 2
            ],
        }
    return None


def first_value(props: dict[str, Any], keys: list[str]) -> Any:
    lower = {str(k).lower(): v for k, v in props.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def railway_category(props: dict[str, Any]) -> str:
    net = str(props.get("NET") or "").upper()
    yard = str(props.get("YARDNAME") or "").strip()
    if net == "M":
        return "rail-main"
    if net == "I":
        return "rail-industrial"
    if yard:
        return "rail-yard"
    return "rail-other"


def railway_category_label(category: str) -> str:
    return {
        "rail-main": "Main rail network",
        "rail-industrial": "Industrial leads",
        "rail-yard": "Rail yard tracks",
        "rail-other": "Other rail tracks",
    }.get(category, "Rail line")


def normalize_rail_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    geometry = rounded_geometry(feature.get("geometry") or {})
    if not geometry:
        return None
    props = feature.get("properties") or {}
    category = railway_category(props)
    owners = [props.get(key) for key in ("RROWNER1", "RROWNER2", "RROWNER3") if props.get(key)]
    trackage = [props.get(key) for key in ("TRKRGHTS1", "TRKRGHTS2", "TRKRGHTS3") if props.get(key)]
    name = props.get("SUBDIV") or props.get("BRANCH") or props.get("YARDNAME") or railway_category_label(category)
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "rail_line",
            "category": category,
            "category_label": railway_category_label(category),
            "name": name,
            "owner": ", ".join(dict.fromkeys(str(v) for v in owners)),
            "trackage_rights": ", ".join(dict.fromkeys(str(v) for v in trackage)),
            "country": props.get("COUNTRY"),
            "state": props.get("STATEAB"),
            "division": props.get("DIVISION"),
            "subdivision": props.get("SUBDIV"),
            "tracks": props.get("TRACKS"),
            "km": round(float(props.get("KM") or 0), 2) if props.get("KM") not in (None, "") else None,
            "source": "BTS/FRA North American Rail Network Lines",
            "source_url": NARN_LINES_URL,
        },
        "geometry": geometry,
    }


def normalize_crude_terminal(feature: dict[str, Any]) -> dict[str, Any] | None:
    geometry = rounded_geometry(feature.get("geometry") or {})
    if not geometry:
        return None
    props = feature.get("properties") or {}
    name = first_value(props, ["Site_Name", "SITE_NAME", "Name"]) or "Crude oil rail terminal"
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "terminal",
            "category": "crude-rail-terminal",
            "category_label": "Crude-by-rail terminals",
            "name": name,
            "city": first_value(props, ["CITY", "City"]),
            "state": first_value(props, ["STATE", "State"]),
            "facility_type": first_value(props, ["FACILITY_T", "Facility_Type"]),
            "handling": first_value(props, ["HANDLING", "Handling"]),
            "commodity": "Crude oil",
            "source": "EIA Crude Oil Rail Terminals",
            "source_url": EIA_CRUDE_RAIL_TERMINALS_URL,
        },
        "geometry": geometry,
    }


def normalize_product_terminal(feature: dict[str, Any]) -> dict[str, Any] | None:
    geometry = rounded_geometry(feature.get("geometry") or {})
    if not geometry:
        return None
    props = feature.get("properties") or {}
    name = first_value(props, ["Site_Name", "SITE_NAME", "Terminal_N", "Terminal_Name", "Site", "Name"]) or "Petroleum product terminal"
    rail_in = first_value(props, ["RAIL_IN", "Rail_In", "RailIn"])
    rail_out = first_value(props, ["RAIL_OUT", "Rail_Out", "RailOut"])
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "terminal",
            "category": "product-terminal",
            "category_label": "Petroleum product terminals",
            "name": name,
            "city": first_value(props, ["CITY", "City"]),
            "state": first_value(props, ["STATE", "State", "State_Name"]),
            "operator": first_value(props, ["COMPANY", "Company", "Owner", "Operator"]),
            "facility_type": first_value(props, ["FACILITY_T", "TYPE", "Type"]),
            "rail_in": rail_in,
            "rail_out": rail_out,
            "commodity": "Refined products / petroleum liquids",
            "source": "EIA Petroleum Product Terminals",
            "source_url": EIA_PRODUCT_TERMINALS_URL,
        },
        "geometry": geometry,
    }


def compact_props(props: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in props.items() if value not in (None, "", [])}


def build_layer(
    bbox: tuple[float, float, float, float],
    rail_where: str,
    crude_terminal_where: str,
    product_terminal_where: str,
) -> dict[str, Any]:
    print("Fetching North American rail lines...")
    raw_lines = query_arcgis_geojson(NARN_LINES_URL, where=rail_where, out_fields=RAIL_OUT_FIELDS, bbox=bbox)
    lines = [feature for feature in (normalize_rail_feature(f) for f in raw_lines) if feature]
    for feature in lines:
        feature["properties"] = compact_props(feature["properties"])
    print(f"  {len(lines):,} rail line segments")

    print("Fetching EIA crude-by-rail terminals...")
    raw_crude = query_arcgis_geojson(EIA_CRUDE_RAIL_TERMINALS_URL, where=crude_terminal_where, bbox=bbox)
    crude = [feature for feature in (normalize_crude_terminal(f) for f in raw_crude) if feature]
    for feature in crude:
        feature["properties"] = compact_props(feature["properties"])
    print(f"  {len(crude):,} crude rail terminals")

    print("Fetching EIA petroleum product terminals...")
    raw_products = query_arcgis_geojson(EIA_PRODUCT_TERMINALS_URL, where=product_terminal_where, bbox=bbox)
    products = [feature for feature in (normalize_product_terminal(f) for f in raw_products) if feature]
    for feature in products:
        feature["properties"] = compact_props(feature["properties"])
    print(f"  {len(products):,} petroleum product terminals")

    features = sorted(
        [*lines, *crude, *products],
        key=lambda f: (
            f["properties"].get("feature_kind") != "rail_line",
            f["properties"].get("category") or "",
            f["properties"].get("name") or "",
        ),
    )
    return {
        "type": "FeatureCollection",
        "name": "Railways and petroleum rail terminals",
        "metadata": {
            "bbox": list(bbox),
            "rail_where": rail_where,
            "crude_terminal_where": crude_terminal_where,
            "product_terminal_where": product_terminal_where,
            "scope": "All Canada plus selected U.S. states connected to Canadian/Bakken crude and refined-product rail supply chains.",
            "rail_detail": "BTS/FRA main network and major industrial leads to control browser and GitHub payload size.",
            "sources": [
                {
                    "name": "BTS/FRA North American Rail Network Lines",
                    "url": NARN_LINES_URL,
                    "coverage": "North America rail linework clipped to the app rail overlay extent",
                },
                {
                    "name": "EIA Crude Oil Rail Terminals",
                    "url": EIA_CRUDE_RAIL_TERMINALS_URL,
                    "coverage": "Crude oil rail loading/unloading terminals inside the app rail overlay extent",
                },
                {
                    "name": "EIA Petroleum Product Terminals",
                    "url": EIA_PRODUCT_TERMINALS_URL,
                    "coverage": "Bulk refined-product/petroleum terminals inside the app rail overlay extent",
                },
            ],
        },
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bbox", nargs=4, type=float, metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"), default=DEFAULT_BBOX)
    parser.add_argument("--rail-where", default=DEFAULT_RAIL_WHERE)
    parser.add_argument("--crude-terminal-where", default=DEFAULT_CRUDE_TERMINAL_WHERE)
    parser.add_argument("--product-terminal-where", default=DEFAULT_PRODUCT_TERMINAL_WHERE)
    args = parser.parse_args()

    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    data = build_layer(tuple(args.bbox), args.rail_where, args.crude_terminal_where, args.product_terminal_where)
    output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)} with {len(data['features']):,} features ({output.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
