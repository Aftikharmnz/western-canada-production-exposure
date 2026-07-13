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

# Full Canadian and U.S. rail network context. The line filter keeps the BTS/FRA
# main network and industrial leads; terminal layers include all U.S. EIA points.
DEFAULT_BBOX = (-170.0, 24.0, -52.0, 72.0)
DEFAULT_RAIL_WHERE = "COUNTRY IN ('CA', 'US') AND NET IN ('M', 'I')"
DEFAULT_CRUDE_TERMINAL_WHERE = "1=1"
DEFAULT_PRODUCT_TERMINAL_WHERE = "1=1"

SUNCOR_TERMINALS_URL = "https://www.suncor.com/en-ca/what-we-do/refining/terminals"
TORQ_TERMINALS_URL = "https://torqlogistics.com/transloading-services/"
GIBSON_OPERATIONS_URL = "https://www.gibsonenergy.com/operations/"
USDG_DRU_URL = "https://usdg.com/terminal/dru/"
KEYERA_ADT_URL = "https://www.keyera.com/investors/news/keyera-facilities-income-fund-announces-long-term-oil-sands-services-agreement-with-imperial-oil/"
BRUDERHEIM_RAIL_URL = "https://www.ogj.com/general-interest/companies/article/17245710/cenovus-completes-purchase-of-rail-terminal"

CANADIAN_TERMINALS: list[dict[str, Any]] = [
    {
        "name": "Hardisty Rail Terminal / DRU",
        "operator": "Gibson Energy / USD Group",
        "category": "crude-rail-terminal",
        "city": "Hardisty",
        "state": "Alberta",
        "coordinates": [-111.309, 52.659],
        "commodity": "Heavy Canadian crude / DRUbit / recovered diluent",
        "facility_type": "Crude-by-rail / diluent recovery terminal",
        "rail_connection": "CP/KCS-connected DRUbit rail movement to U.S. Gulf Coast markets",
        "source": "USD Group DRU terminal and Gibson operations",
        "source_url": USDG_DRU_URL,
    },
    {
        "name": "Gibson Edmonton Terminal",
        "operator": "Gibson Energy",
        "category": "crude-rail-terminal",
        "city": "Edmonton",
        "state": "Alberta",
        "coordinates": [-113.337, 53.557],
        "commodity": "Crude oil",
        "facility_type": "Crude storage and rail-loading terminal",
        "rail_connection": "Rail loading capabilities",
        "source": "Gibson Energy operations",
        "source_url": GIBSON_OPERATIONS_URL,
    },
    {
        "name": "Keyera Alberta Diluent Terminal",
        "operator": "Keyera",
        "category": "crude-rail-terminal",
        "city": "Fort Saskatchewan",
        "state": "Alberta",
        "coordinates": [-113.101, 53.716],
        "commodity": "Diluent / condensate",
        "facility_type": "Diluent storage and rail-offload terminal",
        "rail_connection": "Rail offload services",
        "source": "Keyera oil sands services agreement",
        "source_url": KEYERA_ADT_URL,
    },
    {
        "name": "Keyera Edmonton Terminal",
        "operator": "Keyera",
        "category": "crude-rail-terminal",
        "city": "Edmonton",
        "state": "Alberta",
        "coordinates": [-113.333, 53.562],
        "commodity": "Diluent / condensate",
        "facility_type": "Diluent storage and rail-offload terminal",
        "rail_connection": "Rail offload services",
        "source": "Keyera oil sands services agreement",
        "source_url": KEYERA_ADT_URL,
    },
    {
        "name": "Edmonton Rail Terminal (ERT)",
        "operator": "Pembina / Imperial Oil JV",
        "category": "crude-rail-terminal",
        "city": "Edmonton (Strathcona County)",
        "state": "Alberta",
        "coordinates": [-113.354, 53.494],
        "commodity": "Crude oil / dilbit",
        "facility_type": "Crude-by-rail loading terminal (largest in Canada, ~210 kbbl/d nameplate)",
        "rail_connection": "CN and CPKC connections adjacent to the Imperial Strathcona refinery",
        "source": "Pembina/Imperial Edmonton Rail Terminal public references",
        "source_url": "https://www.pembina.com/",
    },
    {
        "name": "Alberta Crude Terminal (KACT)",
        "operator": "Pembina / Keyera JV",
        "category": "crude-rail-terminal",
        "city": "Edmonton",
        "state": "Alberta",
        "coordinates": [-113.340, 53.570],
        "commodity": "Crude oil",
        "facility_type": "Crude-by-rail loading terminal (~40 kbbl/d)",
        "rail_connection": "CN-served, adjacent to the Keyera Edmonton Terminal",
        "source": "Keyera/Pembina Alberta Crude Terminal public references",
        "source_url": KEYERA_ADT_URL,
    },
    {
        "name": "Bruderheim Rail Terminal",
        "operator": "Cenovus / Bruderheim terminal",
        "category": "crude-rail-terminal",
        "city": "Bruderheim",
        "state": "Alberta",
        "coordinates": [-112.923, 53.800],
        "commodity": "Crude oil",
        "facility_type": "Crude-by-rail terminal",
        "rail_connection": "Links to Canadian Pacific and Canadian National rail lines",
        "source": "Oil & Gas Journal, Cenovus terminal acquisition",
        "source_url": BRUDERHEIM_RAIL_URL,
    },
    {
        "name": "Torq Unity Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Unity",
        "state": "Saskatchewan",
        "coordinates": [-109.145, 52.444],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "Dual CN and CP main line connections",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Lloydminster Big Gully Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Lloydminster",
        "state": "Saskatchewan",
        "coordinates": [-109.977, 53.278],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "CP",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Kerrobert Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Kerrobert",
        "state": "Saskatchewan",
        "coordinates": [-109.131, 51.920],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "CP",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Instow Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Instow",
        "state": "Saskatchewan",
        "coordinates": [-107.424, 49.853],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "Great Western Railway interchange with CP",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Tilley Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Tilley",
        "state": "Alberta",
        "coordinates": [-111.666, 50.455],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "CP",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Whitecourt Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Whitecourt",
        "state": "Alberta",
        "coordinates": [-115.684, 54.139],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "CN local yard",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Torq Buick Terminal",
        "operator": "Torq Energy Logistics",
        "category": "crude-rail-terminal",
        "city": "Buick",
        "state": "British Columbia",
        "coordinates": [-121.625, 56.750],
        "commodity": "Crude oil / condensate / refined products / LPGs",
        "facility_type": "Multi-product rail transload terminal",
        "rail_connection": "CN",
        "source": "Torq transloading services",
        "source_url": TORQ_TERMINALS_URL,
    },
    {
        "name": "Suncor Burrard Products Terminal",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Port Moody / Burnaby",
        "state": "British Columbia",
        "coordinates": [-122.939, 49.288],
        "commodity": "Gasoline / diesel / jet fuel / ethanol / biodiesel",
        "facility_type": "Refined-product terminal",
        "rail_connection": "Marine and rail facilities",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Suncor Edmonton Terminal",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Edmonton",
        "state": "Alberta",
        "coordinates": [-113.358, 53.568],
        "commodity": "Refined products",
        "facility_type": "Refined-product terminal adjacent to refinery",
        "rail_connection": "Refined-product terminal in Suncor network",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Suncor Saskatoon Terminal",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Saskatoon",
        "state": "Saskatchewan",
        "coordinates": [-106.664, 52.111],
        "commodity": "Refined products",
        "facility_type": "Refined-product terminal",
        "rail_connection": "Product terminal in Suncor Saskatoon pipeline and terminal system",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Suncor Milden Tank Farm",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Milden",
        "state": "Saskatchewan",
        "coordinates": [-107.527, 51.488],
        "commodity": "Refined products",
        "facility_type": "Refined-product tank farm and pumping station",
        "rail_connection": "Connected to Saskatoon terminal system",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Suncor Terrace Products Terminal",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Terrace",
        "state": "British Columbia",
        "coordinates": [-128.585, 54.513],
        "commodity": "Gasoline / diesel",
        "facility_type": "Refined-product terminal",
        "rail_connection": "Receives gasoline and diesel by rail and truck",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Suncor Thunder Bay Products Terminal",
        "operator": "Suncor",
        "category": "product-terminal",
        "city": "Thunder Bay",
        "state": "Ontario",
        "coordinates": [-89.220, 48.385],
        "commodity": "Gasoline / diesel",
        "facility_type": "Refined-product terminal",
        "rail_connection": "Receives/distributes product via marine, rail cars, and trucks",
        "source": "Suncor terminals",
        "source_url": SUNCOR_TERMINALS_URL,
    },
    {
        "name": "Gibson Moose Jaw Facility",
        "operator": "Gibson Energy",
        "category": "product-terminal",
        "city": "Moose Jaw",
        "state": "Saskatchewan",
        "coordinates": [-105.547, 50.390],
        "commodity": "Heavy crude oil / refined products",
        "facility_type": "Heavy crude processing and refined-products facility",
        "rail_connection": "Rail-served Moose Jaw industrial corridor",
        "source": "Gibson Energy operations",
        "source_url": GIBSON_OPERATIONS_URL,
    },
]

RAIL_OUT_FIELDS = ",".join(
    [
        "COUNTRY",
        "STATEAB",
        "RROWNER1",
        "RROWNER2",
        "RROWNER3",
        "SUBDIV",
        "BRANCH",
        "YARDNAME",
        "NET",
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
    return round(float(value), 3)


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
    name = props.get("SUBDIV") or props.get("BRANCH") or props.get("YARDNAME") or railway_category_label(category)
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "rail_line",
            "category": category,
            "name": name,
            "owner": ", ".join(dict.fromkeys(str(v) for v in owners)),
            "country": props.get("COUNTRY"),
            "state": props.get("STATEAB"),
            "source": "BTS/FRA North American Rail Network Lines",
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


def canadian_terminal_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for terminal in CANADIAN_TERMINALS:
        props = {
            "feature_kind": "terminal",
            "category": terminal["category"],
            "category_label": "Canadian crude / products rail terminals"
            if terminal["category"] == "crude-rail-terminal"
            else "Canadian petroleum product terminals",
            "name": terminal["name"],
            "city": terminal.get("city"),
            "state": terminal.get("state"),
            "operator": terminal.get("operator"),
            "facility_type": terminal.get("facility_type"),
            "rail_connection": terminal.get("rail_connection"),
            "commodity": terminal.get("commodity"),
            "source": terminal.get("source"),
            "source_url": terminal.get("source_url"),
            "location_confidence": "approximate public-location centroid",
        }
        features.append(
            {
                "type": "Feature",
                "properties": compact_props(props),
                "geometry": {
                    "type": "Point",
                    "coordinates": [round_coord(terminal["coordinates"][0]), round_coord(terminal["coordinates"][1])],
                },
            }
        )
    return features


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

    canadian = canadian_terminal_features()
    print(f"  {len(canadian):,} Canadian curated petroleum rail terminals")

    features = sorted(
        [*lines, *crude, *products, *canadian],
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
            "scope": "All Canada and all U.S. rail lines plus all U.S. EIA crude and petroleum-product terminal points.",
            "rail_detail": "BTS/FRA main network and industrial leads, with compact per-feature properties to stay under GitHub file limits.",
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
                {
                    "name": "Curated Canadian petroleum rail terminals",
                    "url": "See per-feature source_url values",
                    "coverage": "Canadian crude, diluent, transload, and refined-product terminals identified from public operator/regulator pages",
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
