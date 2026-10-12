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
import copy
import hashlib
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "market_access_pipelines.geojson"
DEFAULT_ROUTE_FACTS = ROOT / "data" / "pipeline_route_facts.json"

CER_PIPELINES_URL = "https://services5.arcgis.com/vNzamREXvX2WcX6d/arcgis/rest/services/CER_Pipeline_Systems_WGS84_WM_v/FeatureServer/0"
EIA_CRUDE_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Crude_Oil_Trunk_Pipelines_1/FeatureServer/0"
EIA_PRODUCTS_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Petroleum_Products_Pipelines_1/FeatureServer/0"
EIA_CANONICAL_PRODUCTS_URL = "https://services7.arcgis.com/FGr1D95XCGALKXqM/arcgis/rest/services/PetroleumProduct_Pipelines_US_EIA/FeatureServer/0"
EIA_PRODUCTS_COPY_ITEM_URL = "https://www.arcgis.com/sharing/rest/content/items/c745d9f4b81e42f3a54aee7aaa396975?f=json"
BUCKEYE_PRODUCTS_URL = "https://gis.buckeye.com/hosting/rest/services/Hosted/PublicWebsiteData_PublicView/FeatureServer/2"
BUCKEYE_MAP_URL = "https://www.buckeye.com/map"
EIA_HGL_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/ArcGIS/rest/services/Hydrocarbon_Gas_Liquids_Pipelines_1/FeatureServer/0"
CAPP_MAP_URL = "https://www.capp.ca/wp-content/uploads/2024/03/CAPP-2023-Pipeline-and-Refinery-Map-36x22-wall-size.pdf"
TM_PUGET_URL = "https://www.transmountain.com/news/2019/trans-mountains-puget-sound-pipeline-shipping-products-to-washington-state-refineries-since-1954"
IMPERIAL_SARNIA_PRODUCTS_URL = "https://www.imperialoil.ca/en-ca/company/waterdown-to-finch"
SUN_CANADIAN_URL = "https://sun-canadian.com/about-us/"
VALERO_SAINT_LAURENT_URL = "https://www.valero.com/fr-ca/Operations/PipelineSaint-Laurent"
AER_FEEDER_PIPELINES = ROOT / "public" / "data" / "aer_feeder_pipelines.geojson"


ROUTES: list[dict[str, Any]] = [
    {
        "route_id": "enbridge-mainline-lakehead",
        "route_name": "Enbridge Mainline / Lakehead",
        "operator": "Enbridge",
        "commodity": "Crude oil / dilbit / SCO",
        "flow_role": "Major Western Canadian liquids transport system",
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
        "operator": "South Bow",
        "operator_source_url": "https://www.southbow.com/keystone-pipeline-system/",
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
        "route_name": "Enbridge Lines 40 / 41 — Express / Platte",
        "operator": "Enbridge (Express Pipeline / Platte Pipeline)",
        "operator_source_url": "https://www.enbridge.com/projects-and-infrastructure/liquids-pipelines/express-platte-system",
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
        "route_name": "Enbridge Line 13 / Southern Lights",
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
        "operator": "Pembina (PKM Cochin)",
        "operator_source_url": "https://www.pembina.com/operations/customers/",
        "commodity": "Condensate / diluent",
        "flow_role": "Condensate import trunk for diluent supply",
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
        "operator": "Inter Pipeline (Milk River Pipeline Ltd.)",
        "operator_source_url": "https://apps.cer-rec.gc.ca/PPS/en/pipeline-profiles/milk-river",
        "commodity": "Crude oil",
        "flow_role": "Southern Alberta cross-border crude link",
        "direction": "Bow River interconnection at Milk River, Alberta, to Front Range at the border west of Coutts",
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
        "route_id": "enbridge-line-7",
        "route_name": "Enbridge Line 7",
        "operator": "Enbridge",
        "commodity": "Crude oil / liquids",
        "flow_role": "Ontario refinery access",
        "direction": "Sarnia to Westover, Ontario",
        "geometry_note": "CER explicitly identifies these published segments as EnbridgeLine7. The linework is a general route reference, not survey-grade.",
        "color": "#60a5fa",
        "display_order": 80,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'EnbridgeLine7'",
                   "expected_identity": {"PipelineID": "EnbridgeLine7"}}],
    },
    {
        "route_id": "enbridge-line-11",
        "route_name": "Enbridge Line 11",
        "operator": "Enbridge",
        "commodity": "Crude oil / liquids",
        "flow_role": "Ontario refinery access",
        "direction": "Westover to Nanticoke, Ontario",
        "geometry_note": "CER explicitly identifies these segments as EnbridgeLine11. Its published geometry begins near Hamilton and omits the connecting portion from Westover; the reviewed endpoints describe the full line.",
        "color": "#93c5fd",
        "display_order": 81,
        "default_visible": True,
        "menu_section": "Selected Other Crude Oil Pipelines",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'EnbridgeLine11'",
                   "expected_identity": {"PipelineID": "EnbridgeLine11"}}],
    },
    {
        "route_id": "enbridge-lines-7-11",
        "route_name": "Enbridge Lines 7 / 11 (combined reference)",
        "operator": "Enbridge",
        "commodity": "Crude oil / liquids",
        "flow_role": "Ontario refinery access",
        "direction": "Line 7: Sarnia to Westover; Line 11: Westover to Nanticoke, Ontario",
        "geometry_note": "The CER Line 11 geometry begins near Hamilton and does not show the connecting portion from Westover. Route endpoints describe the full reviewed system; the map shows the published segments.",
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
        "direction": "Sarnia refinery to Hamilton and the Greater Toronto Area through Waterdown",
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
        "route_id": "vantage",
        "route_name": "Vantage / Stateline II",
        "operator": "Pembina",
        "operator_source_url": "https://www.pembina.com/operations/customers/",
        "commodity": "Ethane",
        "flow_role": "Bakken ethane supply to Alberta petrochemical markets",
        "direction": "Tioga / North Dakota and Saskatchewan to Empress, Alberta",
        "color": "#a855f7",
        "display_order": 96,
        "default_visible": False,
        "menu_section": "Other Liquids / Products",
        "coverage_scope": "EIA named Vantage system and Stateline II lateral. This ethane corridor is not a crude export or diluent pipeline.",
        "parts": [{"source": "EIA", "url": EIA_HGL_URL, "where": "Opername = 'VANTAGE PIPELINE'"}],
    },
    {
        "route_id": "norman-wells",
        "route_name": "Enbridge Line 21 / Norman Wells (supply shut in)",
        "operator": "Enbridge",
        "commodity": "Crude oil",
        "flow_role": "Historical Northwest Territories crude supply connection",
        "direction": "Norman Wells to Zama; Imperial shut in source production in August 2026",
        "color": "#78716c",
        "display_order": 99,
        "default_visible": False,
        "menu_section": "Other Liquids / Products",
        "status_note": "Source production shut in August 2026; pipeline deactivation/abandonment status is not independently verified.",
        "status_source_url": "https://www.imperialoil.ca/en-ca/company/operations/norman-wells",
        "coverage_scope": "Retained as infrastructure context after Imperial's upstream production shut-in; does not imply continuing throughput.",
        "parts": [{"source": "CER", "url": CER_PIPELINES_URL, "where": "PipelineID = 'NormanWells'"}],
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
                "where": "PipelineID IN ('Genesis', 'Montreal')",
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
                data = json.loads(response.read().decode("utf-8"))
                if not isinstance(data, dict) or data.get("error"):
                    raise ValueError(f"ArcGIS returned an error response: {data.get('error') if isinstance(data, dict) else 'not an object'}")
                return data
        except ValueError:
            # Invalid schemas and ArcGIS query errors are not transient HTTP failures.
            raise
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
        if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
            raise ValueError(f"Expected GeoJSON FeatureCollection from {service_url}")
        page = data["features"]
        features.extend(page)
        if not page and data.get("exceededTransferLimit"):
            raise ValueError(f"ArcGIS pagination stalled at offset {offset}: {service_url}")
        if not page or (not data.get("exceededTransferLimit") and len(page) < page_size):
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


def route_feature(route: dict[str, Any], include_remote: bool,
                  aer_feeder_input: Path = AER_FEEDER_PIPELINES) -> tuple[dict[str, Any] | None, list[str]]:
    lines: list[list[list[float]]] = []
    sources: list[str] = []
    warnings: list[str] = []
    identity_records: list[dict[str, Any]] = []

    for part in route.get("parts", []):
        if part.get("manual_lines"):
            manual = [line for line in part["manual_lines"] if isinstance(line, list) and len(line) >= 2]
            lines.extend(manual)
            if manual:
                sources.append(f"{part['source']} ({len(manual)} curated segment{'s' if len(manual) != 1 else ''})")
            continue

        if part.get("local_geojson"):
            path = Path(part["local_geojson"])
            if path == AER_FEEDER_PIPELINES:
                path = aer_feeder_input
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
        if not part_features:
            warnings.append(f"{route['route_name']}: {part['source']} query returned no features ({part['where']})")
        expected = part.get("expected_identity")
        if expected:
            seen_ids = set()
            for feature in part_features:
                attributes = feature.get("properties") or {}
                object_id = attributes.get("OBJECTID")
                if (any(attributes.get(field) != value for field, value in expected.items())
                        or type(object_id) is not int or object_id in seen_ids or not feature_lines(feature)
                        or any(len(line) < 2 for line in feature_lines(feature))):
                    raise ValueError(f"{route['route_id']}: source query did not return unique explicitly identified line geometry")
                seen_ids.add(object_id)
            if part_features:
                identity_records.append({"source_url": part["url"], "identity_fields": expected.copy(),
                                         "source_feature_ids": sorted(seen_ids)})
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
        "operator_source_url": route.get("operator_source_url"),
        "status_note": route.get("status_note"),
        "status_source_url": route.get("status_source_url"),
        "commodity": route["commodity"],
        "flow_role": route["flow_role"],
        "direction": route["direction"],
        "color": route["color"],
        "display_order": route["display_order"],
        "default_visible": bool(route.get("default_visible", True)),
        "menu_section": route.get("menu_section", "Core Market Access Pipelines"),
        "source_summary": "; ".join(sources),
        "source_urls": sorted({source_reference(part) for part in route.get("parts", [])}),
        "geometry_note": route.get("geometry_note"),
        "geometry_confidence": route.get(
            "geometry_confidence",
            "mixed public GIS and curated approximate corridor; not survey-grade"
            if any(part.get("manual_lines") for part in route.get("parts", []))
            else "public GIS linework, route-level display; not survey-grade",
        ),
        "coverage_scope": route.get(
            "coverage_scope",
            "Named route selected for market-access context; not a complete pipeline inventory.",
        ),
    }
    if identity_records:
        properties["geometry_source_identities"] = identity_records
    return {"type": "Feature", "properties": properties, "geometry": geometry_from_lines(lines)}, warnings


def hub_feature(name: str, hub_type: str, lon: float, lat: float) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {
            "feature_kind": "hub",
            "name": name,
            "hub_type": hub_type,
            "source_summary": "CAPP map route-node reference and public geographic coordinates",
            "geometry_confidence": "Approximate market-area centroid; not an individual facility or surveyed interconnect",
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def load_route_facts(path: Path) -> dict[str, dict[str, Any]]:
    """Load dated, reviewed route facts; geometry refreshes cannot infer new capacities."""
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate pipeline fact key: {key}")
            result[key] = value
        return result
    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    if (not isinstance(payload, dict) or not {"schema_version", "routes"} <= set(payload)
            or set(payload) - {"schema_version", "routes", "product_networks"}
            or type(payload["schema_version"]) is not int or payload["schema_version"] != 1):
        raise ValueError("Pipeline route facts require schema_version 1 and routes")
    facts = payload["routes"]
    expected = {route["route_id"] for route in ROUTES}
    if not isinstance(facts, dict) or set(facts) != expected:
        missing = sorted(expected - set(facts)) if isinstance(facts, dict) else sorted(expected)
        extra = sorted(set(facts) - expected) if isinstance(facts, dict) else []
        raise ValueError(f"Pipeline route facts do not match shipped route IDs; missing={missing}, extra={extra}")
    product_facts = payload.get("product_networks", {})
    if (not isinstance(product_facts, dict) or any(not key.startswith("us-products-")
            or key == "us-products-reference" for key in product_facts)):
        raise ValueError("Product network reviews require stable us-products-* IDs")
    facts = {**facts, **product_facts}
    required = {"origin", "destination", "product", "capacity_kbbl_d", "capacity_basis", "capacity_note", "source_url", "source_name", "verified_at"}
    optional = {"capacity_label", "as_of", "route_source_url", "operator", "route_name", "menu_section"}
    for route_id, fact in facts.items():
        if not isinstance(fact, dict) or not required <= set(fact) or set(fact) - required - optional:
            raise ValueError(f"{route_id}: unsupported or missing pipeline fact fields")
        for field in (required | optional) - {"capacity_kbbl_d"}:
            if field in fact and (not isinstance(fact[field], str) or not fact[field].strip()):
                raise ValueError(f"{route_id}: {field} must be a nonempty string")
        capacity = fact["capacity_kbbl_d"]
        if capacity is not None and (type(capacity) not in (int, float) or not math.isfinite(capacity) or capacity <= 0):
            raise ValueError(f"{route_id}: capacity_kbbl_d must be a positive finite number or null")
        for field in ("source_url", "route_source_url"):
            if field in fact:
                url = urllib.parse.urlsplit(fact[field])
                if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                    raise ValueError(f"{route_id}: {field} must be a public HTTP(S) URL")
        try:
            valid = date.fromisoformat(fact["verified_at"])
        except ValueError as exc:
            raise ValueError(f"{route_id}: verified_at must be an ISO calendar date") from exc
        if valid.isoformat() != fact["verified_at"]:
            raise ValueError(f"{route_id}: verified_at must use YYYY-MM-DD")
    return facts


def product_network_id(operator: str | None, pipeline: str | None) -> str:
    """Identifiers depend on publisher identity, never position or feature order."""
    identity = (operator or "", pipeline or "")
    known = {
        ("BUCKEYE PARTNERS", "Buckeye"): "us-products-buckeye",
        ("COLONIALPIPELINE CO", "Colonial"): "us-products-colonial",
        ("MIDSTREAM PARTNERS", "Magellan"): "us-products-magellan",
    }
    if identity in known:
        return known[identity]
    label = re.sub(r"[^a-z0-9]+", "-", "-".join(identity).lower()).strip("-") or "unknown"
    digest = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()[:10]
    return f"us-products-{label[:96]}-{digest}"


def fetch_product_inventory() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Prefer the canonical publisher; identify a public copy explicitly when unavailable."""
    canonical_error = None
    try:
        metadata = request_json(f"{EIA_CANONICAL_PRODUCTS_URL}?f=json")
        source_url = EIA_CANONICAL_PRODUCTS_URL
        publisher = "U.S. Energy Information Administration (canonical EIA organization)"
    except (ValueError, RuntimeError) as exc:
        canonical_error = str(exc)
        metadata = request_json(f"{EIA_PRODUCTS_URL}?f=json")
        source_url = EIA_PRODUCTS_URL
        publisher = request_json(EIA_PRODUCTS_COPY_ITEM_URL).get("owner") or "Publisher owner unavailable"
    count = request_json(f"{source_url}/query?where=1%3D1&returnCountOnly=true&f=json").get("count")
    features = query_arcgis_geojson(source_url, "1=1")
    if type(count) is not int or count <= 0 or len(features) != count:
        raise ValueError(f"EIA product query count mismatch: expected {count}, received {len(features)}")
    metadata.update(_source_url=source_url, _publisher=publisher,
                    _is_hosted_copy=source_url == EIA_PRODUCTS_URL, _canonical_access_error=canonical_error)
    return features, metadata


def build_product_network_features(source_features: list[dict[str, Any]], source_metadata: dict[str, Any],
                                   facts: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Partition every EIA product record exactly once using its two name fields."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    source_ids: set[int] = set()
    for feature in source_features:
        properties = feature.get("properties") or {}
        fid = properties.get("FID", feature.get("id"))
        if type(fid) is not int or fid in source_ids:
            raise ValueError("EIA product features require unique integer FIDs")
        if not feature_lines(feature) or any(len(line) < 2 for line in feature_lines(feature)):
            raise ValueError(f"EIA product feature {fid} has no usable line geometry")
        source_ids.add(fid)
        operator = properties.get("Opername") or ""
        pipeline = properties.get("Pipename") or ""
        if not isinstance(operator, str) or not isinstance(pipeline, str):
            raise ValueError(f"EIA product feature {fid} has invalid identity fields")
        groups.setdefault((operator, pipeline), []).append(feature)

    editing = source_metadata.get("editingInfo") or {}
    timestamp = editing.get("dataLastEditDate")
    data_edit = datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat() if timestamp is not None else None
    schema_timestamp = editing.get("schemaLastEditDate")
    schema_edit = datetime.fromtimestamp(schema_timestamp / 1000, timezone.utc).isoformat() if schema_timestamp is not None else None
    checked_at = datetime.now(timezone.utc).isoformat()
    is_copy = source_metadata.get("_is_hosted_copy", True)
    source_url = source_metadata.get("_source_url", EIA_PRODUCTS_URL)
    source_label = "Archived EIA-attributed public copy" if is_copy else "Canonical EIA published service"
    edit_label = "hosted-copy service" if is_copy else "EIA publisher service"
    palette = ["#0891b2", "#16a34a", "#d97706", "#be123c", "#7c3aed", "#0369a1", "#0f766e", "#9333ea"]
    colors = {"us-products-buckeye": "#ca8a04", "us-products-colonial": "#ea580c", "us-products-magellan": "#7c3aed"}
    output = []
    for number, ((operator, pipeline), members) in enumerate(sorted(groups.items())):
        route_id = product_network_id(operator, pipeline)
        details = facts.get(route_id)
        name = pipeline or "Unknown pipeline name"
        if operator not in {"BUCKEYE PARTNERS", "COLONIALPIPELINE CO", "MIDSTREAM PARTNERS"}:
            name = f"{name} ({operator or 'Unknown source operator'})"
        published_operator = operator or "Unknown source operator"
        if details is None:
            details = {
                "product": "Petroleum products (EIA layer classification; current service unverified)",
                "origin": "Not supplied by the EIA source",
                "destination": "Not supplied by the EIA source",
                "capacity_kbbl_d": None, "capacity_basis": "unavailable",
                "capacity_label": "Not published / not verified",
                "capacity_note": "EIA supplies operator/name labels and geometry, not capacities, endpoints, current batch contents or operating status. No flow direction or ownership is inferred from geometry.",
                "source_url": source_url, "source_name": f"{source_label} — petroleum-products pipeline identity snapshot",
                "as_of": "Underlying EIA inventory date unavailable; hosted service edit is not an inventory/survey date",
            }
        member_ids = sorted(member.get("properties", {}).get("FID", member.get("id")) for member in members)
        lines = [line for member in members for line in feature_lines(member)]
        properties = {
            "feature_kind": "pipeline", "route_id": route_id, "route_name": details.get("route_name", name),
            "operator": details.get("operator", f"{published_operator} (EIA source label)"),
            "operator_source_url": details["source_url"] if "operator" in details else None,
            "commodity": details["product"], "flow_role": "Named EIA petroleum-products network snapshot",
            "direction": "Not inferred from coordinate order",
            "color": colors.get(route_id, palette[int(hashlib.sha256(route_id.encode()).hexdigest()[:4], 16) % len(palette)]),
            "display_order": 300 + number, "default_visible": False,
            "menu_section": details.get("menu_section", "U.S. refined-product networks"),
            "source_summary": f"{source_label} ({len(members)} source features); published operator: {published_operator}",
            "source_urls": sorted({source_url, details["source_url"]}),
            "source_operator_names": [operator] if operator else [],
            "source_pipeline_names": [pipeline] if pipeline else [],
            "source_feature_ids": member_ids, "source_feature_count": len(member_ids),
            "source_as_of": f"Underlying inventory date unavailable; {edit_label} data edit {data_edit[:10] if data_edit else 'unavailable'}",
            "review_status": "reviewed_operator_identity" if "operator" in details else "publisher_snapshot_only",
            "network_identity_basis": "EIA Opername + Pipename; source names are historical labels. Current identities are used only where separately reviewed.",
            "geometry_confidence": f"{source_label}; underlying inventory date unavailable; not survey-grade or evidence of current service",
            "coverage_scope": "Exactly one published operator/pipeline identity. No terminal connection, capacity or flow direction is inferred by proximity.",
            "pipeline_details": details,
        }
        output.append({"type": "Feature", "properties": properties, "geometry": geometry_from_lines(lines)})
    return output, {
        "source_url": source_url, "source_feature_count": len(source_ids), "network_count": len(output),
        "grouping_fields": ["Opername", "Pipename"], "hosted_copy_data_edit_at": data_edit if is_copy else None,
        "hosted_copy_schema_edit_at": schema_edit if is_copy else None, "publisher_service_data_edit_at": data_edit,
        "publisher_service_schema_edit_at": schema_edit, "checked_at": checked_at,
        "canonical_source_url": EIA_CANONICAL_PRODUCTS_URL, "underlying_inventory_date": None,
        "source_publisher": source_metadata.get("_publisher", "Federal_User_Community (Esri-hosted public EIA-attributed copy)"),
        "is_hosted_copy": is_copy, "canonical_access_error": source_metadata.get("_canonical_access_error"),
        "source_item_url": EIA_PRODUCTS_COPY_ITEM_URL if is_copy else None,
        "coverage_note": "Every fetched source FID belongs to exactly one named product group; source labels and edit dates do not establish current ownership or operating status.",
    }


def apply_buckeye_operator_geometry(features: list[dict[str, Any]], operator_features: list[dict[str, Any]],
                                    source_metadata: dict[str, Any]) -> dict[str, Any]:
    """Use exact reviewed name mappings; archived IDs are reconciliation, not geometry IDs."""
    matches = {
        "BUCKEYE PIPE LINE": product_network_id("BUCKEYE PARTNERS", "Buckeye"),
        "LAUREL PIPE LINE": product_network_id("BUCKEYE PARTNERS", "Laurel Pipeline"),
        "WEST SHORE PIPE LINE": product_network_id("WEST SHORE PIPELINE CO", "West Shore Pipeine"),
    }
    by_id = {row["properties"]["route_id"]: row for row in features}
    timestamp = (source_metadata.get("editingInfo") or {}).get("lastEditDate")
    edit_date = datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat() if timestamp is not None else None
    grouped = {}
    seen_ids = set()
    for source in operator_features:
        properties = source.get("properties") or {}
        oid = properties.get("objectid", source.get("id"))
        name = properties.get("name")
        if (type(oid) is not int or oid in seen_ids or not isinstance(name, str) or not name
                or not feature_lines(source) or any(len(line) < 2 for line in feature_lines(source))):
            raise ValueError("Buckeye published geometry requires unique IDs, explicit names and usable lines")
        seen_ids.add(oid)
        grouped.setdefault(name, []).append(source)
    mapped_count = 0
    additional_count = 0
    for name, sources in sorted(grouped.items()):
        route_id = matches.get(name)
        target = by_id.get(route_id)
        if route_id and target is None:
            raise ValueError(f"Reviewed Buckeye identity {name} is absent from archived reference")
        source_ids = sorted(source.get("properties", {}).get("objectid", source.get("id")) for source in sources)
        products = sorted({source.get("properties", {}).get("products") for source in sources
                           if source.get("properties", {}).get("products")})
        descriptions = sorted({source.get("properties", {}).get("description") for source in sources
                               if source.get("properties", {}).get("description")})
        if target is None:
            # No proximity crosswalk to a differently named historical pipe.
            route_id = "operator-products-buckeye-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            target = {"type": "Feature", "properties": {
                "feature_kind": "pipeline", "route_id": route_id, "route_name": name.title(),
                "operator": "Buckeye Partners (operator-published network; ownership shares unspecified)",
                "operator_source_url": BUCKEYE_MAP_URL, "default_visible": False,
                "display_order": 600 + additional_count, "color": "#a16207",
                "menu_section": "Other Liquids / Products" if name == "BUCKEYE TEXAS PARTNERS" else "U.S. refined-product networks",
                "source_operator_names": ["Buckeye Partners"], "source_pipeline_names": [name],
                "source_feature_ids": [], "source_feature_count": 0,
                "pipeline_details": {
                    "product": "; ".join(products) or "Product not specified",
                    "origin": "Individual endpoints not supplied by operator GIS attributes",
                    "destination": "Individual endpoints not supplied by operator GIS attributes",
                    "capacity_kbbl_d": None, "capacity_basis": "unavailable", "capacity_label": "Not published / not verified",
                    "capacity_note": "An operator map record establishes a published named corridor, not installed capacity, current throughput or ownership percentages.",
                    "source_url": BUCKEYE_MAP_URL, "source_name": "Buckeye Partners — official public pipeline map",
                    "as_of": "Operator-published GIS; underlying inventory/survey date not supplied",
                },
            }}
            features.append(target)
            additional_count += 1
        else:
            mapped_count += 1
        props = target["properties"]
        props.update(
            commodity="; ".join(products) or props.get("commodity", "Product not specified"),
            direction="Not inferred from coordinate order",
            source_summary=f"Buckeye official map ({len(sources)} operator records); archived EIA IDs retained only for reconciliation",
            source_urls=sorted(set(props.get("source_urls", [])) | {BUCKEYE_MAP_URL, BUCKEYE_PRODUCTS_URL}),
            source_pipeline_names=sorted(set(props.get("source_pipeline_names", [])) | {name}),
            geometry_source_url=BUCKEYE_PRODUCTS_URL, geometry_source_feature_ids=source_ids,
            source_as_of=f"Operator-published map; inventory date not supplied (service last edit {edit_date[:10] if edit_date else 'unavailable'})",
            review_status="operator_published_geometry",
            network_identity_basis="Operator-published named pipeline geometry; archived EIA identities are matched only by reviewed exact names and retained as reconciliation IDs, never by proximity.",
            geometry_confidence="Buckeye official public map linework, general route location; underlying survey date unavailable; not survey-grade",
            coverage_scope="Operator-published network description; map geometry does not establish terminal ownership, commercial connection or current throughput.",
            operator_description=" ".join(descriptions),
        )
        target["geometry"] = geometry_from_lines([line for source in sources for line in feature_lines(source)])
    return {"source_url": BUCKEYE_PRODUCTS_URL, "official_map_url": BUCKEYE_MAP_URL,
            "source_feature_count": len(seen_ids), "operator_network_count": len(grouped),
            "replaced_archived_group_count": mapped_count, "additional_network_count": additional_count,
            "service_last_edit_at": edit_date, "underlying_inventory_date": None,
            "identity_note": "Reviewed exact-name matches only; additional operator names are emitted separately without guessed archived associations."}


def apply_reviewed_route_facts(feature: dict[str, Any], details: dict[str, Any]) -> None:
    """Update reviewed descriptive facts without changing line geometry/provenance."""
    properties = feature["properties"]
    properties.update(pipeline_details=copy.deepcopy(details), commodity=details["product"],
                      direction=f"{details['origin']} → {details['destination']}")
    for field in ("operator", "route_name", "menu_section"):
        if field in details:
            properties[field] = details[field]
    if "operator" in details:
        properties["operator_source_url"] = details["source_url"]


def merge_verified_enbridge_lines(existing: dict[str, Any], facts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Fetch only explicitly identified CER Lines 7/11; preserve every other geometry.

    The old combined reference remains available but hidden. Reviewed facts may
    refresh display names/products/menus; source IDs and linework are not inferred.
    """
    if existing.get("type") != "FeatureCollection" or not isinstance(existing.get("features"), list):
        raise ValueError("Verified line merge requires an existing FeatureCollection")
    output = copy.deepcopy(existing)
    by_id = {}
    for feature in output["features"]:
        properties = feature.get("properties") or {}
        if properties.get("feature_kind") == "pipeline":
            route_id = properties.get("route_id")
            if not isinstance(route_id, str) or route_id in by_id:
                raise ValueError("Verified line merge requires unique existing route IDs")
            by_id[route_id] = feature
    aggregate_id = "enbridge-lines-7-11"
    if aggregate_id not in by_id:
        raise ValueError("Verified line merge must preserve the existing combined 7/11 reference")
    child_ids = {"enbridge-line-7", "enbridge-line-11"}
    child_features = []
    for route in ROUTES:
        if route["route_id"] not in child_ids:
            continue
        feature, warnings = route_feature(route, include_remote=True)
        if warnings or feature is None:
            raise ValueError(f"Incomplete explicit CER line query: {warnings}")
        apply_reviewed_route_facts(feature, facts[route["route_id"]])
        child_features.append(feature)
    if len(child_features) != 2:
        raise ValueError("Both numbered CER lines are required before publication")
    for feature in output["features"]:
        properties = feature.get("properties") or {}
        route_id = properties.get("route_id")
        if route_id in facts:
            apply_reviewed_route_facts(feature, facts[route_id])
        if route_id in {"southern-lights", "norman-wells", "express-platte", aggregate_id}:
            definition = next(route for route in ROUTES if route["route_id"] == route_id)
            properties["route_name"] = definition["route_name"]
        if route_id == aggregate_id:
            properties["default_visible"] = False
            properties["coverage_scope"] = "Legacy combined CER Lines 7/11 reference. Separately identified numbered lines are available; do not add this geometry to their coverage."
    output["features"] = [feature for feature in output["features"]
                          if feature.get("properties", {}).get("route_id") not in child_ids] + child_features
    output.setdefault("metadata", {})["numbered_line_geometry_review"] = {
        "source_url": CER_PIPELINES_URL, "reviewed_at": date.today().isoformat(),
        "explicit_pipeline_ids": ["EnbridgeLine7", "EnbridgeLine11"],
        "note": "Only exact CER identities were split. Other geometry and source IDs were retained; grouped Mainline/Lakehead corridors are not assigned to individual numbered lines.",
    }
    return output


def build_feature_collection(include_remote: bool, aer_feeder_input: Path = AER_FEEDER_PIPELINES,
                             route_facts: Path = DEFAULT_ROUTE_FACTS) -> dict[str, Any]:
    facts = load_route_facts(route_facts)
    features: list[dict[str, Any]] = []
    warnings: list[str] = []
    products_metadata = None

    for route in ROUTES:
        feature, route_warnings = route_feature(route, include_remote=include_remote, aer_feeder_input=aer_feeder_input)
        warnings.extend(route_warnings)
        if feature:
            details = facts[route["route_id"]]
            apply_reviewed_route_facts(feature, details)
            features.append(feature)
            print(f"{route['route_name']}: {feature['properties']['source_summary']}", file=sys.stderr)

    if include_remote:
        try:
            product_sources, source_metadata = fetch_product_inventory()
            product_features, products_metadata = build_product_network_features(product_sources, source_metadata, facts)
            buckeye_metadata = request_json(f"{BUCKEYE_PRODUCTS_URL}?f=json")
            buckeye_count = request_json(f"{BUCKEYE_PRODUCTS_URL}/query?where=1%3D1&returnCountOnly=true&f=json").get("count")
            buckeye_sources = query_arcgis_geojson(BUCKEYE_PRODUCTS_URL, "1=1")
            if type(buckeye_count) is not int or buckeye_count <= 0 or len(buckeye_sources) != buckeye_count:
                raise ValueError("Buckeye operator query did not return its complete published inventory")
            products_metadata["operator_geometry"] = apply_buckeye_operator_geometry(product_features, buckeye_sources, buckeye_metadata)
            features.extend(product_features)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Named EIA product networks: refresh failed: {exc}")

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
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "geometry_crs": "EPSG:4326 (longitude, latitude)",
            "source_notes": [
                "Canadian federally regulated liquid linework is selected from the public CER pipeline systems FeatureServer.",
                "Alberta Rangeland/Aurora corridor linework uses local AER feeder pipeline features where public licences identify operating Plains/Aurora segments.",
                "U.S. continuations are selected from EIA Energy Atlas FeatureServers where available; coarse EIA chords that duplicate Canadian CER linework are filtered out.",
                "Two hidden U.S. reference features aggregate the EIA crude-oil trunk and HGL public layers. The products layer is partitioned by published Opername + Pipename into separate named selections; no catch-all products geometry is emitted.",
                "EIA product attributes can retain old operator names. Geometry data edit dates are reported separately from later schema edits and current operator reviews; nearby terminals are not inferred connections.",
                "The public EIA-attributed product service is an Esri-hosted copy, not the canonical EIA publisher. Its service edit dates are not underlying inventory/survey dates. Buckeye, Laurel and West Shore use direct operator map geometry by reviewed exact-name matches; other operator-only networks remain separate.",
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
            "product_networks": products_metadata,
        },
        "features": features,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--aer-feeder-input", type=Path, default=AER_FEEDER_PIPELINES,
                        help="Validated AER feeder layer to use, including an isolated ELT candidate")
    parser.add_argument("--route-facts", type=Path, default=DEFAULT_ROUTE_FACTS,
                        help="Reviewed route endpoints and capacity facts; retained across geometry refreshes")
    parser.add_argument("--verified-enbridge-merge", type=Path, metavar="EXISTING_GEOJSON",
                        help="Preserve existing geometry and fetch only exact CER Lines 7/11, then apply reviewed route facts")
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Build only local content. Useful for UI tests when network is unavailable.",
    )
    args = parser.parse_args()

    if args.local_only and args.output.resolve() == DEFAULT_OUTPUT.resolve():
        parser.error("--local-only requires a separate --output; it must not replace the production network")

    if args.verified_enbridge_merge and args.local_only:
        parser.error("--verified-enbridge-merge requires its two live CER identity queries")
    if args.verified_enbridge_merge:
        existing = json.loads(args.verified_enbridge_merge.read_text(encoding="utf-8"))
        collection = merge_verified_enbridge_lines(existing, load_route_facts(args.route_facts.resolve()))
    else:
        collection = build_feature_collection(include_remote=not args.local_only, aer_feeder_input=args.aer_feeder_input.resolve(),
                                             route_facts=args.route_facts.resolve())
    if collection["metadata"]["warnings"] and not args.local_only:
        for warning in collection["metadata"]["warnings"]:
            print(f"ERROR: {warning}", file=sys.stderr)
        print("Preserving existing pipeline output because the refresh is incomplete.", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(collection, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    temporary.replace(args.output)
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
