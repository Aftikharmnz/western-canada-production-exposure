"""
Build the app-ready Major Market Access Pipelines GeoJSON.

The layer is route-level, not survey-grade. Canadian linework is pulled from the
public CER pipeline systems FeatureServer when available. U.S. continuations and
hidden national reference networks use EIA Energy Atlas FeatureServers. Selected
provincially regulated Canadian product pipelines are approximate corridors based
on operator-published route descriptions. Each route or reference network is
emitted as one map feature.

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
IMPERIAL_SARNIA_PRODUCTS_URL = "https://www.imperialoil.ca/en-ca/company/waterdown-to-finch"
SUN_CANADIAN_URL = "https://sun-canadian.com/about-us/"
VALERO_SAINT_LAURENT_URL = "https://www.energievalero.ca/en-ca/operations/pipelinesaint-laurent/route"
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
        "operator": "Enbridge (incl. Seaway JV with Enterprise)",
        "commodity": "Crude oil / liquids",
        "flow_role": "U.S. refinery and terminal laterals connected to Enbridge crude markets",
        "direction": "Midwest, Midcontinent, Ontario border, Cushing, and Gulf Coast laterals",
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
            },
            {
                # Seaway (Enbridge/Enterprise 50-50 JV): Cushing -> Gulf Coast, a
                # primary Canadian heavy route to Gulf refining/export markets.
                # EIA does not carry Flanagan South under any name, so Seaway plus
                # Spearhead/Southern Access represent the Enbridge Gulf path.
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": "Opername = 'ENTERPRISE PRODUCTS PARTNERS' AND Pipename = 'Seaway'",
            },
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
            {
                # Puget Sound pipeline (Sumas -> Laurel -> Ferndale/Cherry Point and
                # Laurel -> Burlington -> Anacortes/March Point). EIA does not expose
                # this line under any Trans Mountain name (verified against the EIA
                # crude trunk FeatureServer), so without this part the route stopped
                # at the border while the Anacortes/Ferndale hubs floated unconnected.
                # Route-level approximate corridor, not survey geometry.
                "source": "Curated (Trans Mountain Puget Sound corridor, approximate)",
                "url": TM_PUGET_URL,
                "manual_lines": [
                    [
                        [-122.265, 49.002], [-122.34, 48.95], [-122.42, 48.88],
                        [-122.47, 48.85], [-122.46, 48.75], [-122.40, 48.64],
                        [-122.35, 48.54], [-122.33, 48.47], [-122.43, 48.46],
                        [-122.50, 48.47], [-122.56, 48.49],
                    ],
                    [
                        [-122.47, 48.85], [-122.58, 48.84], [-122.70, 48.83],
                        [-122.755, 48.79],
                    ],
                ],
            },
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
                # CER carries the federally regulated Aurora border segment.
                "source": "CER",
                "url": CER_PIPELINES_URL,
                "where": "PipelineID = 'Aurora'",
            },
            {
                "source": "EIA",
                "url": EIA_CRUDE_URL,
                "where": "Opername = 'PHILLIPS 66 PIPELINE' AND Pipename = 'Glacier Pipeline'",
            },
        ],
    },
    {
        "route_id": "milk-river",
        "route_name": "Milk River",
        "operator": "Plains Midstream",
        "commodity": "Crude oil",
        "flow_role": "Southern Alberta cross-border crude link",
        "direction": "Milk River AB to the Montana border (Front Range/Glacier connections)",
        "color": "#a16207",
        "display_order": 73,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [
            {
                # CER PipelineID carries a literal trailing CR/LF in the service
                # data ("MilkRiver\r\n"), so match on the prefix.
                "source": "CER",
                "url": CER_PIPELINES_URL,
                "where": "PipelineID LIKE 'MilkRiver%'",
            }
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
        "route_id": "imperial-sarnia-products",
        "route_name": "Imperial Sarnia Products Pipeline",
        "operator": "Imperial Oil",
        "commodity": "Refined petroleum products",
        "flow_role": "Southern Ontario gasoline, diesel, and jet-fuel distribution",
        "direction": "Sarnia via London and Waterdown to Hamilton and Finch/Toronto",
        "color": "#be123c",
        "display_order": 91,
        "default_visible": False,
        "menu_section": "Canadian Refined-Product Pipelines",
        "geometry_confidence": (
            "curated approximate corridor from the operator-published route description; "
            "not survey-grade and not suitable for locating"
        ),
        "coverage_scope": "Operator-described intercity route and terminal branches; approximate display corridor.",
        "parts": [
            {
                "source": "Curated (Imperial Sarnia Products Pipeline corridor, approximate)",
                "url": IMPERIAL_SARNIA_PRODUCTS_URL,
                "manual_lines": [
                    [
                        [-82.40, 42.95],
                        [-82.10, 43.00],
                        [-81.73, 42.98],
                        [-81.25, 42.98],
                        [-80.78, 43.14],
                        [-80.32, 43.25],
                        [-79.93, 43.34],
                        [-79.70, 43.48],
                        [-79.48, 43.66],
                        [-79.35, 43.79],
                    ],
                    [
                        [-79.93, 43.34],
                        [-79.87, 43.28],
                        [-79.81, 43.25],
                    ],
                ],
            }
        ],
    },
    {
        "route_id": "sun-canadian",
        "route_name": "Sun-Canadian Pipe Line",
        "operator": "Sun-Canadian Pipe Line",
        "commodity": "Refined petroleum products",
        "flow_role": "Southern Ontario refinery-to-market product distribution",
        "direction": "Sarnia-area refineries to London, Hamilton, and the Toronto area",
        "color": "#ea580c",
        "display_order": 92,
        "default_visible": False,
        "menu_section": "Canadian Refined-Product Pipelines",
        "geometry_confidence": (
            "curated approximate corridor from the operator-published system description; "
            "not survey-grade and not suitable for locating"
        ),
        "coverage_scope": "Operator-described intercity system; approximate display corridor.",
        "parts": [
            {
                "source": "Curated (Sun-Canadian system corridor, approximate)",
                "url": SUN_CANADIAN_URL,
                "manual_lines": [
                    [
                        [-82.39, 42.95],
                        [-82.05, 42.91],
                        [-81.65, 42.91],
                        [-81.25, 42.98],
                        [-80.82, 43.10],
                        [-80.42, 43.18],
                        [-80.08, 43.23],
                        [-79.86, 43.26],
                        [-79.63, 43.46],
                        [-79.43, 43.65],
                    ]
                ],
            }
        ],
    },
    {
        "route_id": "valero-pipeline-saint-laurent",
        "route_name": "Valero Pipeline Saint-Laurent",
        "operator": "Energie Valero",
        "commodity": "Refined petroleum products",
        "flow_role": "Quebec refinery-to-terminal product distribution",
        "direction": "Jean-Gaulin refinery at Levis via the Drummondville corridor to Montreal-East",
        "color": "#a855f7",
        "display_order": 93,
        "default_visible": False,
        "menu_section": "Canadian Refined-Product Pipelines",
        "geometry_confidence": (
            "curated approximate corridor from the operator-published 250 km route description; "
            "not survey-grade and not suitable for locating"
        ),
        "coverage_scope": "Operator-described Levis-to-Montreal-East route; approximate display corridor.",
        "parts": [
            {
                "source": "Curated (Valero Pipeline Saint-Laurent corridor, approximate)",
                "url": VALERO_SAINT_LAURENT_URL,
                "manual_lines": [
                    [
                        [-71.20, 46.75],
                        [-71.50, 46.60],
                        [-71.86, 46.45],
                        [-72.18, 46.28],
                        [-72.49, 46.02],
                        [-72.58, 45.88],
                        [-72.91, 45.72],
                        [-73.20, 45.62],
                        [-73.52, 45.64],
                    ]
                ],
            }
        ],
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
    {
        "route_id": "us-crude-trunk-reference",
        "route_name": "U.S. crude-oil trunk pipeline reference",
        "operator": "Various",
        "commodity": "Crude oil",
        "flow_role": "National context for U.S. crude-oil trunk and selected intrastate corridors",
        "direction": "Various U.S. corridors",
        "color": "#475569",
        "display_order": 200,
        "default_visible": False,
        "menu_section": "U.S. National Reference Networks",
        "geometry_confidence": (
            "official EIA public GIS linework, route-level display; coverage represents major/trunk "
            "and selected intrastate pipelines, not every pipe"
        ),
        "coverage_scope": "EIA crude-oil trunk pipeline layer; not a complete inventory of every pipe.",
        "parts": [
            {
                "source": "EIA Energy Atlas crude-oil trunk pipeline reference layer",
                "url": EIA_CRUDE_URL,
                "where": "1=1",
            }
        ],
    },
    {
        "route_id": "us-products-reference",
        "route_name": "U.S. petroleum-products pipeline reference",
        "operator": "Various",
        "commodity": "Refined petroleum products",
        "flow_role": "National context for U.S. product trunk and selected intrastate corridors",
        "direction": "Various U.S. corridors",
        "color": "#f59e0b",
        "display_order": 201,
        "default_visible": False,
        "menu_section": "U.S. National Reference Networks",
        "geometry_confidence": (
            "official EIA public GIS linework, route-level display; coverage represents major/trunk "
            "and selected intrastate pipelines, not every pipe"
        ),
        "coverage_scope": "EIA petroleum-products pipeline layer; not a complete inventory of every pipe.",
        "parts": [
            {
                "source": "EIA Energy Atlas petroleum-products pipeline reference layer",
                "url": EIA_PRODUCTS_URL,
                "where": "1=1",
            }
        ],
    },
    {
        "route_id": "us-hgl-reference",
        "route_name": "U.S. hydrocarbon-gas-liquids pipeline reference",
        "operator": "Various",
        "commodity": "Hydrocarbon gas liquids",
        "flow_role": "National context for U.S. HGL trunk and selected intrastate corridors",
        "direction": "Various U.S. corridors",
        "color": "#14b8a6",
        "display_order": 202,
        "default_visible": False,
        "menu_section": "U.S. National Reference Networks",
        "geometry_confidence": (
            "official EIA public GIS linework, route-level display; coverage represents major/trunk "
            "and selected intrastate pipelines, not every pipe"
        ),
        "coverage_scope": "EIA HGL pipeline layer; not a complete inventory of every pipe.",
        "parts": [
            {
                "source": "EIA Energy Atlas HGL pipeline reference layer",
                "url": EIA_HGL_URL,
                "where": "1=1",
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
    ("Flanagan", "Enbridge Midwest interconnect", -88.86, 40.88),
    ("Nederland / Port Arthur", "Gulf Coast crude hub / refinery market", -93.99, 29.97),
    ("Houston", "Gulf Coast refinery / export market", -95.26, 29.72),
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
        if part.get("manual_lines"):
            manual = [line for line in part["manual_lines"] if isinstance(line, list) and len(line) >= 2]
            lines.extend(manual)
            if manual:
                sources.append(f"{part['source']} ({len(manual)} curated segment{'s' if len(manual) != 1 else ''})")
            continue

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
        "geometry_confidence": route.get(
            "geometry_confidence",
            "public GIS linework, route-level display",
        ),
        "coverage_scope": route.get(
            "coverage_scope",
            "Named route selected for market-access context; not a complete pipeline inventory.",
        ),
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
            "description": (
                "Named Canadian crude, condensate/diluent, and refined-product market-access routes, "
                "selected connected U.S. routes, hidden U.S. national reference networks, and hub points."
            ),
            "generated_with": "scripts/build_market_access_pipelines.py",
            "source_notes": [
                "Canadian federally regulated liquid linework is selected from the public CER pipeline systems FeatureServer.",
                "Alberta Rangeland/Aurora corridor linework uses local AER feeder pipeline features where public licences identify operating Plains/Aurora segments.",
                "U.S. continuations are selected from EIA Energy Atlas FeatureServers where available; coarse EIA chords that duplicate Canadian CER linework are filtered out.",
                "Three hidden U.S. reference features aggregate the EIA crude-oil trunk, petroleum-products, and HGL public layers. Those layers provide major/trunk and selected intrastate context, not every pipe, connector, gathering line, or plant line.",
                "Imperial's Sarnia Products Pipeline, Sun-Canadian Pipe Line, and Valero's Pipeline Saint-Laurent are hidden by default and rendered as curated approximate corridors from current operator route descriptions because these provincially regulated systems are not in the federal CER layer.",
                "The Trans Mountain Puget Sound leg (Sumas to Ferndale/Cherry Point and Anacortes/March Point) is a curated approximate corridor: EIA does not expose the line under any Trans Mountain name, and without it the route stopped at the border while the Washington refinery hubs floated unconnected.",
                "Other route-level manual connectors are intentionally excluded to avoid unsupported straight-line artifacts over water or across border gaps.",
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
                "imperial_sarnia_products_reference": IMPERIAL_SARNIA_PRODUCTS_URL,
                "sun_canadian_reference": SUN_CANADIAN_URL,
                "valero_saint_laurent_reference": VALERO_SAINT_LAURENT_URL,
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
