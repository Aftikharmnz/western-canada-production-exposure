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
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import terminal_inventory


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "public" / "data" / "railways.geojson"

NARN_LINES_URL = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_North_American_Rail_Network_Lines/FeatureServer/0"
EIA_CRUDE_RAIL_TERMINALS_URL = "https://services.arcgis.com/8df8p0NlLFEShl0r/ArcGIS/rest/services/CrudeOil_RailTerminals_US_EIA_3340393128070186484/FeatureServer/0"
EIA_PRODUCT_TERMINALS_URL = "https://services2.arcgis.com/wx8u046p68e0iGuj/arcgis/rest/services/PetroleumProduct_Terminals_US_EIA/FeatureServer/0"

# Canadian and U.S. main-network context. The line filter keeps BTS/FRA main
# routes and major industrial leads; terminal layers include all EIA points.
DEFAULT_BBOX = (-170.0, 24.0, -52.0, 72.0)
DEFAULT_RAIL_WHERE = "COUNTRY IN ('CA', 'US') AND NET IN ('M', 'I')"
DEFAULT_CRUDE_TERMINAL_WHERE = "1=1"
DEFAULT_PRODUCT_TERMINAL_WHERE = "1=1"

SUNCOR_TERMINALS_URL = "https://www.suncor.com/en-ca/what-we-do/refining/terminals"
TRANS_MOUNTAIN_TERMINALS_URL = "https://www.transmountain.com/terminals"
NPRI_FACILITIES_URL = "https://maps-cartes.ec.gc.ca/arcgis/rest/services/STB_DGST/NPRI/MapServer/0"
ENBRIDGE_STORAGE_URL = "https://www.oilsandsmagazine.com/projects/crude-oil-storage-terminals"
IMPERIAL_TERMINALS_URL = "https://www.imperialoil.ca/en-ca/company/operations/pipelines-and-distribution"
SHELL_TERMINALS_URL = "https://www.shell.ca/en_ca/about-us/what-we-do.html"
IRVING_FACILITIES_URL = "https://www.irvingoil.com/en-CA/discover-irving/irving-oil-facilities"
VALERO_CANADA_URL = "https://www.energievalero.ca/en-ca"
HF_SINCLAIR_MISSISSAUGA_URL = "https://www.hfsinclair.com/operations/facilities/canada/mississauga-on/default.aspx"
PEMBINA_ERT_DECOMMISSION_URL = "https://www.pembina.com/media-centre/news/details/c397a7cf-2903-455a-bf6d-fcf5bc685b90"
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
        "name": "Keyera Edmonton Terminal / Alberta Diluent & Crude Terminals (ADT/ACT)",
        "operator": "Keyera / Pembina JV",
        "category": "crude-rail-terminal",
        "city": "Edmonton",
        "state": "Alberta",
        "coordinates": [-113.333, 53.562],
        "commodity": "Crude oil / diluent / condensate",
        "facility_type": "Co-located diluent rail-offload and crude rail-loading terminals",
        "rail_connection": "CN-served rail offload/loading services",
        "source": "Keyera oil sands services agreement and Alberta Crude Terminal public references",
        "source_url": KEYERA_ADT_URL,
        "status": "Verification needed",
        "last_verified": "2026-07-22",
        "modes": "Rail / pipeline",
        "location_confidence": "Approximate public-location centroid",
        "facility_scope": "Combined terminal complex",
    },
    {
        "name": "Edmonton Rail Terminal (ERT)",
        "operator": "Pembina / Imperial Oil JV",
        "category": "inactive-terminal",
        "city": "Edmonton (Strathcona County)",
        "state": "Alberta",
        "coordinates": [-113.354, 53.494],
        "commodity": "Crude oil / dilbit",
        "facility_type": "Crude-by-rail loading terminal (largest in Canada, ~210 kbbl/d nameplate)",
        "rail_connection": "CN and CPKC connections adjacent to the Imperial Strathcona refinery",
        "source": "Pembina disposition/decommissioning disclosure",
        "source_url": PEMBINA_ERT_DECOMMISSION_URL,
        "status": "Decommissioned Q2 2024",
        "last_verified": "2026-07-22",
        "modes": "Rail / pipeline",
        "location_confidence": "Approximate public-location centroid",
        "facility_scope": "Former primary crude-by-rail terminal",
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
        "coordinates": [-106.7058, 52.1146],
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
        "coordinates": [-89.2456, 48.3710],
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


def _terminal_record(
    *,
    name: str,
    operator: str,
    category: str,
    city: str,
    state: str,
    coordinates: list[float],
    commodity: str,
    facility_type: str,
    modes: str,
    source: str,
    source_url: str,
    location_confidence: str,
    facility_scope: str = "Primary terminal",
    status: str = "Operational",
    coordinate_source_url: str | None = None,
) -> dict[str, Any]:
    """Create a consistently sourced Canadian terminal record."""
    return {
        "name": name,
        "operator": operator,
        "category": category,
        "country": "CA",
        "city": city,
        "state": state,
        "coordinates": coordinates,
        "commodity": commodity,
        "facility_type": facility_type,
        "modes": modes,
        "source": source,
        "source_url": source_url,
        "coordinate_source_url": coordinate_source_url,
        "status": status,
        "last_verified": "2026-07-22",
        "location_confidence": location_confidence,
        "facility_scope": facility_scope,
    }


# Suncor's current operator page lists fourteen Canadian terminal locations.
# These are the eight not already represented in the base curated list above.
CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=name,
        operator="Suncor",
        category="product-terminal",
        city=city,
        state=state,
        coordinates=coordinates,
        commodity="Gasoline / diesel / jet fuel / renewable fuel blends",
        facility_type="Refined-product distribution terminal",
        modes=modes,
        source="Suncor terminal network; NPRI facility coordinates where available",
        source_url=SUNCOR_TERMINALS_URL,
        coordinate_source_url=NPRI_FACILITIES_URL,
        location_confidence="NPRI facility coordinates",
    )
    for name, city, state, coordinates, modes in [
        ("Suncor London Products Terminal", "London", "Ontario", [-81.1658, 43.0212], "Pipeline / truck"),
        ("Suncor Metro Depot Products Terminal", "Toronto", "Ontario", [-79.4779, 43.7668], "Pipeline / truck"),
        ("Suncor Oakville South Products Terminal", "Oakville", "Ontario", [-79.73, 43.3901], "Marine / pipeline / truck"),
        ("Suncor Ottawa Products Terminal", "Ottawa / Nepean", "Ontario", [-75.719, 45.3266], "Pipeline / truck"),
        ("Suncor Montreal East Products Terminal", "Montreal", "Quebec", [-73.50813, 45.61264], "Marine / pipeline / truck"),
        ("Suncor Kamloops Products Terminal", "Kamloops", "British Columbia", [-120.4315, 50.7113], "Rail / truck"),
        ("Suncor Nanaimo Products Terminal", "Nanaimo", "British Columbia", [-123.94973, 49.18639], "Marine / truck"),
        ("Suncor Rimouski Products Terminal", "Rimouski", "Quebec", [-68.51001, 48.47524], "Marine / truck"),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=name,
        operator="Trans Mountain",
        category="crude-terminal",
        city=city,
        state=state,
        coordinates=coordinates,
        commodity=commodity,
        facility_type=facility_type,
        modes=modes,
        source="Trans Mountain terminal network",
        source_url=TRANS_MOUNTAIN_TERMINALS_URL,
        location_confidence=confidence,
        facility_scope=scope,
    )
    for name, city, state, coordinates, commodity, facility_type, modes, confidence, scope in [
        ("Trans Mountain Edmonton Terminal", "Edmonton", "Alberta", [-113.366203, 53.544399], "Crude oil / refined petroleum products", "Pipeline receipt, storage, and dispatch terminal", "Pipeline", "Operator-published facility coordinates", "Primary pipeline terminal"),
        ("Trans Mountain Kamloops Terminal", "Kamloops", "British Columbia", [-120.414497, 50.6619], "Crude oil / refined petroleum products", "Pipeline terminal and pump station", "Pipeline", "Operator-published facility coordinates", "Pipeline terminal"),
        ("Trans Mountain Burnaby Terminal", "Burnaby", "British Columbia", [-122.930191, 49.269508], "Crude oil / refined petroleum products", "Pipeline storage and distribution terminal", "Pipeline / truck", "Operator-published facility coordinates", "Primary pipeline terminal"),
        ("Trans Mountain Westridge Marine Terminal", "Burnaby", "British Columbia", [-122.955002, 49.288101], "Crude oil", "Marine export terminal", "Pipeline / marine", "Operator-published facility coordinates", "Primary marine terminal"),
        ("Trans Mountain Sumas Terminal", "Sumas", "British Columbia", [-122.2, 49.0], "Crude oil / refined petroleum products", "Pipeline terminal and pump station", "Pipeline", "Approximate operator-map location", "Pipeline terminal"),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=f"Enbridge {city} Terminal",
        operator="Enbridge",
        category="crude-terminal",
        city=city,
        state=state,
        coordinates=coordinates,
        commodity="Crude oil / petroleum liquids",
        facility_type="Pipeline storage and transfer terminal",
        modes="Pipeline",
        source="NPRI facility coordinates and public crude-storage infrastructure references",
        source_url=ENBRIDGE_STORAGE_URL,
        coordinate_source_url=NPRI_FACILITIES_URL,
        location_confidence="NPRI facility coordinates",
        facility_scope="Primary pipeline terminal",
    )
    for city, state, coordinates in [
        ("Hardisty", "Alberta", [-111.2061, 52.5881]),
        ("Kerrobert", "Saskatchewan", [-109.03138, 51.86884]),
        ("Cromer", "Manitoba", [-101.081, 49.7333]),
        ("Regina", "Saskatchewan", [-104.5977, 50.4769]),
        ("Sarnia", "Ontario", [-82.3525, 42.9405]),
        ("Westover", "Ontario", [-80.091, 43.3285]),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=name,
        operator="Gibson Energy",
        category="crude-terminal",
        city=city,
        state="Alberta",
        coordinates=coordinates,
        commodity="Crude oil / petroleum liquids",
        facility_type="Crude storage and pipeline terminal",
        modes="Pipeline",
        source="Gibson Energy operations",
        source_url=GIBSON_OPERATIONS_URL,
        coordinate_source_url=NPRI_FACILITIES_URL,
        location_confidence="NPRI facility coordinates",
        facility_scope="Primary crude storage terminal",
    )
    for name, city, coordinates in [
        ("Gibson Hardisty Terminal", "Hardisty", [-111.2735, 52.6399]),
        ("Gibson Edmonton South Terminal", "Edmonton", [-113.37163, 53.55167]),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=f"Imperial {name} Products Terminal",
        operator="Imperial Oil",
        category="product-terminal",
        city=city,
        state=state,
        coordinates=coordinates,
        commodity="Gasoline / diesel / aviation fuel / petroleum products",
        facility_type="Refined-product distribution terminal",
        modes=modes,
        source="Imperial Oil distribution network; NPRI facility coordinates",
        source_url=IMPERIAL_TERMINALS_URL,
        coordinate_source_url=NPRI_FACILITIES_URL,
        location_confidence="NPRI facility coordinates",
    )
    for name, city, state, coordinates, modes in [
        ("Calgary", "Calgary", "Alberta", [-113.97668, 50.9636], "Pipeline / rail / truck"),
        ("Edmonton", "Edmonton", "Alberta", [-113.40201, 53.53004], "Pipeline / rail / truck"),
        ("Lougheed", "Burnaby", "British Columbia", [-122.92663, 49.25621], "Pipeline / truck"),
        ("Nanaimo", "Nanaimo", "British Columbia", [-123.9501, 49.19235], "Marine / truck"),
        ("Regina", "Regina", "Saskatchewan", [-104.58882, 50.47261], "Pipeline / rail / truck"),
        ("Winnipeg", "East St. Paul / Winnipeg", "Manitoba", [-97.0464, 49.98149], "Pipeline / rail / truck"),
        ("Gretna", "Gretna", "Manitoba", [-97.5614, 49.009], "Pipeline / truck"),
        ("Finch", "Toronto", "Ontario", [-79.485, 43.7662], "Pipeline / truck"),
        ("Nanticoke", "Nanticoke", "Ontario", [-80.048, 42.8351], "Pipeline / marine / truck"),
        ("Sault Ste. Marie", "Sault Ste. Marie", "Ontario", [-84.2875, 46.518], "Marine / rail / truck"),
        ("Sept-Iles", "Sept-Iles", "Quebec", [-66.373193, 50.197081], "Marine / truck"),
        ("Dartmouth", "Dartmouth", "Nova Scotia", [-63.5384, 44.6408], "Marine / truck"),
        ("Sydney", "Sydney", "Nova Scotia", [-60.202378, 46.148429], "Marine / truck"),
        ("Corner Brook", "Corner Brook", "Newfoundland and Labrador", [-58.0137, 48.9642], "Marine / truck"),
        ("Hay River", "Hay River", "Northwest Territories", [-115.7775, 60.8244], "Rail / marine / truck"),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=f"Shell {name} Products Terminal",
        operator="Shell Canada",
        category="product-terminal",
        city=city,
        state=state,
        coordinates=coordinates,
        commodity="Gasoline / diesel / aviation fuel / petroleum products",
        facility_type="Refined-product distribution terminal",
        modes=modes,
        source="Shell Canada distribution network; NPRI facility coordinates",
        source_url=SHELL_TERMINALS_URL,
        coordinate_source_url=NPRI_FACILITIES_URL,
        location_confidence="NPRI facility coordinates",
    )
    for name, city, state, coordinates, modes in [
        ("Calgary", "Calgary", "Alberta", [-113.9789, 50.96227], "Pipeline / truck"),
        ("Burmount", "Burnaby", "British Columbia", [-122.928, 49.2607], "Pipeline / truck"),
        ("Shellburn", "Burnaby", "British Columbia", [-122.9684, 49.2846], "Marine / pipeline / truck"),
        ("Bare Point", "Chemainus", "British Columbia", [-123.7061, 48.9284], "Marine / truck"),
        ("Winnipeg", "Winnipeg", "Manitoba", [-97.08396, 49.88881], "Rail / truck"),
        ("Hamilton", "Hamilton", "Ontario", [-79.8474, 43.2693], "Marine / pipeline / truck"),
        ("Keele", "Toronto", "Ontario", [-79.4895, 43.7688], "Pipeline / truck"),
        ("Kingston", "Kingston", "Ontario", [-76.5444, 44.276], "Marine / truck"),
        ("Ottawa", "Ottawa", "Ontario", [-75.718, 45.338], "Pipeline / rail / truck"),
        ("Sarnia", "Sarnia", "Ontario", [-82.4565, 42.9055], "Pipeline / marine / truck"),
        ("Sault Ste. Marie", "Sault Ste. Marie", "Ontario", [-84.2776, 46.5227], "Marine / rail / truck"),
        ("Montreal East", "Montreal", "Quebec", [-73.52141, 45.62445], "Marine / pipeline / truck"),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=name,
        operator="Irving Oil",
        category=category,
        city=city,
        state=state,
        coordinates=coordinates,
        commodity=commodity,
        facility_type=facility_type,
        modes=modes,
        source="Irving Oil current facilities",
        source_url=IRVING_FACILITIES_URL,
        location_confidence="Public facility coordinates",
        facility_scope=scope,
    )
    for name, category, city, state, coordinates, commodity, facility_type, modes, scope in [
        ("Irving Halifax Harbour Terminal", "product-terminal", "Dartmouth", "Nova Scotia", [-63.5449, 44.64659], "Refined petroleum products", "Marine product terminal", "Marine / truck", "Primary marine terminal"),
        ("Irving Canaport / East Saint John Terminal", "crude-terminal", "Saint John", "New Brunswick", [-66.0359, 45.2785], "Crude oil / gasoline / distillate / LPG", "Deepwater crude receipt and mixed petroleum terminal", "Marine / pipeline / rail", "Primary crude and marine terminal"),
        ("Irving Charlottetown Terminal", "product-terminal", "Charlottetown", "Prince Edward Island", [-63.1127, 46.2426], "Refined petroleum products", "Marine product terminal", "Marine / truck", "Primary marine terminal"),
        ("Irving St. John's Terminal", "product-terminal", "St. John's", "Newfoundland and Labrador", [-52.6985, 47.5622], "Refined petroleum products", "Marine product terminal", "Marine / truck", "Primary marine terminal"),
    ]
)


CANADIAN_TERMINALS.extend(
    _terminal_record(
        name=name,
        operator="Valero Energy",
        category="product-terminal",
        city=city,
        state="Quebec",
        coordinates=coordinates,
        commodity="Gasoline / diesel / jet fuel / petroleum products",
        facility_type=facility_type,
        modes=modes,
        source="Valero Energy Canada assets",
        source_url=VALERO_CANADA_URL,
        location_confidence=confidence,
        facility_scope=scope,
    )
    for name, city, coordinates, facility_type, modes, confidence, scope in [
        ("Valero Montreal East Terminal", "Montreal", [-73.526, 45.634], "Bulk storage and distribution terminal", "Marine / pipeline / rail / truck", "Approximate public facility location", "Primary product terminal"),
        ("Valero Gaspe Terminal", "Gaspe", [-64.447903, 48.82562], "Marine product terminal", "Marine / truck", "Public facility coordinates", "Primary marine terminal"),
        ("Valero Levis / Jean-Gaulin Marine Terminal", "Levis", [-71.193509, 46.758386], "Refinery-adjacent marine and product terminal", "Marine / pipeline / truck", "Public facility coordinates", "Refinery-adjacent terminal"),
    ]
)


CANADIAN_TERMINALS.append(
    _terminal_record(
        name="HF Sinclair Mississauga Lubricants Centre",
        operator="HF Sinclair / Petro-Canada Lubricants",
        category="product-terminal",
        city="Mississauga",
        state="Ontario",
        coordinates=[-79.6101, 43.5012],
        commodity="Base oils / specialty lubricants / waxes",
        facility_type="Specialty-lubricants refinery and marine terminal",
        modes="Marine / pipeline / truck",
        source="HF Sinclair Mississauga facility",
        source_url=HF_SINCLAIR_MISSISSAUGA_URL,
        location_confidence="Public facility coordinates",
        facility_scope="Specialty refined-products facility",
    )
)


# Bring legacy curated records up to the same explicit provenance schema. Older
# one-off sources are marked for re-verification rather than implied to be a
# complete, currently operating national registry.
LEGACY_TERMINAL_MODES = {
    "Hardisty Rail Terminal / DRU": "Rail / pipeline",
    "Gibson Edmonton Terminal": "Rail / pipeline",
    "Bruderheim Rail Terminal": "Rail",
    "Torq Unity Terminal": "Rail / truck",
    "Torq Lloydminster Big Gully Terminal": "Rail / truck",
    "Torq Kerrobert Terminal": "Rail / truck",
    "Torq Instow Terminal": "Rail / truck",
    "Torq Tilley Terminal": "Rail / truck",
    "Torq Whitecourt Terminal": "Rail / truck",
    "Torq Buick Terminal": "Rail / truck",
    "Suncor Burrard Products Terminal": "Pipeline / marine / rail / truck",
    "Suncor Edmonton Terminal": "Pipeline / truck",
    "Suncor Saskatoon Terminal": "Pipeline / truck",
    "Suncor Milden Tank Farm": "Pipeline",
    "Suncor Terrace Products Terminal": "Rail / truck",
    "Suncor Thunder Bay Products Terminal": "Marine / rail / truck",
    "Gibson Moose Jaw Facility": "Pipeline / rail / truck",
}

for terminal in CANADIAN_TERMINALS:
    terminal.setdefault("country", "CA")
    terminal.setdefault(
        "status",
        "Verification needed" if terminal["name"] == "Bruderheim Rail Terminal" else "Operational",
    )
    terminal.setdefault("last_verified", "2026-07-22")
    terminal.setdefault(
        "modes",
        LEGACY_TERMINAL_MODES.get(
            terminal["name"],
            "Rail / pipeline" if terminal["category"] == "crude-rail-terminal" else "Modes vary by site",
        ),
    )
    terminal.setdefault("location_confidence", "Approximate public-location centroid")
    terminal.setdefault(
        "facility_scope",
        "Rail terminal" if terminal["category"] == "crude-rail-terminal" else "Primary or operator-listed terminal",
    )

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


def request_json(url: str, retries: int = 3, *, post_data: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"User-Agent": "western-canada-production-exposure/railway-builder"}
    encoded = None
    if post_data is not None:
        encoded = urllib.parse.urlencode(post_data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=encoded, headers=headers)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
                if not isinstance(data, dict) or data.get("error"):
                    raise ValueError(f"ArcGIS returned an error response: {data.get('error') if isinstance(data, dict) else 'not an object'}")
                return data
        except ValueError:
            # Retrying a deterministic ArcGIS 400 can stall the entire rebuild.
            raise
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
    bbox: tuple[float, float, float, float] | None = DEFAULT_BBOX,
    page_size: int = 2000,
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultRecordCount": str(page_size),
            "resultOffset": str(offset),
        }
        if bbox is not None:
            min_lon, min_lat, max_lon, max_lat = bbox
            params.update(
                {
                    "geometry": json.dumps(
                        {
                            "xmin": min_lon,
                            "ymin": min_lat,
                            "xmax": max_lon,
                            "ymax": max_lat,
                            "spatialReference": {"wkid": 4326},
                        },
                        separators=(",", ":"),
                    ),
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                }
            )
        data = request_json(f"{service_url}/query?{urllib.parse.urlencode(params)}")
        if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
            raise ValueError(f"Expected GeoJSON FeatureCollection from {service_url}")
        page = data["features"]
        features.extend(page)
        if not page and data.get("exceededTransferLimit"):
            raise ValueError(f"ArcGIS pagination stalled at offset {offset}: {service_url}")
        if not page:
            break
        if not data.get("exceededTransferLimit") and len(page) < page_size:
            break
        offset += len(page)
    return features


def round_coord(value: Any) -> float:
    return round(float(value), 3)


def query_rail_geojson(bbox, where: str, batch_size: int = 500) -> list[dict[str, Any]]:
    """Select IDs once, then fetch bounded geometry batches without a spatial join.

    BTS rejects/timeouts on the former 2,000-feature spatial GeoJSON request.
    Stable IDs also avoid drifting offset pages if the source changes mid-build.
    """
    if not 1 <= batch_size <= 800:
        raise ValueError("Rail geometry batch_size must be between 1 and 800")
    min_lon, min_lat, max_lon, max_lat = bbox
    params = {
        "where": where, "returnIdsOnly": "true", "f": "json",
        "geometry": json.dumps({"xmin": min_lon, "ymin": min_lat, "xmax": max_lon, "ymax": max_lat,
                                "spatialReference": {"wkid": 4326}}),
        "geometryType": "esriGeometryEnvelope", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
    }
    # The national extent is redundant for the current Canada/U.S. source, but
    # asking ArcGIS to join that large envelope to all IDs fails upstream. Prove
    # equivalence by count before omitting the spatial filter. Custom smaller
    # extents retain the original spatial ID selection.
    all_ids_params = {"where": where, "returnIdsOnly": "true", "f": "json"}
    selected = request_json(f"{NARN_LINES_URL}/query?{urllib.parse.urlencode(all_ids_params)}")
    count_params = {key: value for key, value in params.items() if key != "returnIdsOnly"}
    count_params["returnCountOnly"] = "true"
    extent_count = request_json(f"{NARN_LINES_URL}/query?{urllib.parse.urlencode(count_params)}").get("count")
    if extent_count != len(selected.get("objectIds") or []):
        selected = request_json(f"{NARN_LINES_URL}/query?{urllib.parse.urlencode(params)}")
    object_ids = selected.get("objectIds")
    object_field = selected.get("objectIdFieldName")
    if not isinstance(object_ids, list) or not object_ids or not object_field:
        raise ValueError("BTS did not return a usable rail feature-ID inventory")
    object_ids = sorted(set(object_ids))
    if len(object_ids) != extent_count:
        raise ValueError("BTS rail ID inventory does not match the requested extent count")
    batches = [object_ids[start:start + batch_size] for start in range(0, len(object_ids), batch_size)]

    def fetch_batch(ids):
        query = {"objectIds": ",".join(str(i) for i in ids), "outFields": object_field + "," + RAIL_OUT_FIELDS,
                 "returnGeometry": "true", "outSR": "4326", "f": "geojson"}
        # The service returns HTTP 404 for long objectIds query strings. A form
        # POST keeps the request URL short without reducing or omitting IDs.
        data = request_json(f"{NARN_LINES_URL}/query", post_data=query)
        features = data.get("features")
        if data.get("type") != "FeatureCollection" or not isinstance(features, list):
            raise ValueError("BTS rail batch did not return GeoJSON")
        received = {f.get("properties", {}).get(object_field) for f in features}
        if received != set(ids) or len(features) != len(ids) or data.get("exceededTransferLimit"):
            raise ValueError("BTS rail batch was truncated or changed during the refresh")
        return features

    features = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for page in pool.map(fetch_batch, batches):
            features.extend(page)
    return features


def round_point_coord(value: Any) -> float:
    return round(float(value), 5)


def rounded_geometry(geometry: dict[str, Any]) -> dict[str, Any] | None:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
        return {"type": "Point", "coordinates": [round_point_coord(coords[0]), round_point_coord(coords[1])]}
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


def aggregate_rail_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group NARN segments into a much smaller set of Leaflet path layers.

    NARN is segmented at topology/attribute breaks. Rendering every source row as
    its own Leaflet layer is expensive, even though adjacent rows share the same
    visual category and owner. Grouping preserves those styling fields while the
    ``segment_count`` property keeps the source-row cardinality auditable.
    """
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for feature in features:
        props = feature.get("properties") or {}
        key = (
            str(props.get("category") or "rail-other"),
            str(props.get("country") or ""),
            str(props.get("owner") or "Unspecified owner"),
        )
        group = groups.setdefault(
            key,
            {
                "type": "Feature",
                "properties": {
                    "feature_kind": "rail_line",
                    "category": key[0],
                    "name": f"{key[2]} — {railway_category_label(key[0])}",
                    "owner": key[2],
                    "country": key[1],
                    "segment_count": 0,
                    "source": "BTS/FRA North American Rail Network Lines",
                },
                "geometry": {"type": "MultiLineString", "coordinates": []},
            },
        )
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "LineString":
            group["geometry"]["coordinates"].append(geometry.get("coordinates") or [])
        elif geometry.get("type") == "MultiLineString":
            group["geometry"]["coordinates"].extend(geometry.get("coordinates") or [])
        group["properties"]["segment_count"] += 1

    return [
        feature
        for feature in groups.values()
        if feature["geometry"]["coordinates"]
    ]


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
            "country": "US",
            "name": name,
            "city": first_value(props, ["CITY", "City"]),
            "state": first_value(props, ["STATE", "State"]),
            "facility_type": first_value(props, ["FACILITY_T", "Facility_Type"]),
            "handling": first_value(props, ["HANDLING", "Handling"]),
            "commodity": "Crude oil",
            "source": "EIA Crude Oil Rail Terminals",
            "source_url": EIA_CRUDE_RAIL_TERMINALS_URL,
            "coordinate_source_url": EIA_CRUDE_RAIL_TERMINALS_URL,
            **terminal_inventory.archive_properties("crude-rail", props),
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
            "country": "US",
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
            "coordinate_source_url": EIA_PRODUCT_TERMINALS_URL,
            **terminal_inventory.archive_properties("products", props),
        },
        "geometry": geometry,
    }


def canadian_terminal_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    category_labels = {
        "crude-rail-terminal": "Canadian crude / multi-product rail terminals",
        "crude-terminal": "Canadian crude storage / pipeline / marine terminals",
        "product-terminal": "Canadian petroleum product terminals",
        "inactive-terminal": "Inactive / decommissioned terminals",
    }
    for terminal in CANADIAN_TERMINALS:
        props = {
            "feature_kind": "terminal",
            "category": terminal["category"],
            "category_label": category_labels.get(terminal["category"], "Canadian petroleum terminal"),
            "name": terminal["name"],
            "country": terminal.get("country"),
            "city": terminal.get("city"),
            "state": terminal.get("state"),
            "operator": terminal.get("operator"),
            "facility_type": terminal.get("facility_type"),
            "rail_connection": terminal.get("rail_connection"),
            "modes": terminal.get("modes"),
            "commodity": terminal.get("commodity"),
            "status": terminal.get("status"),
            "last_verified": terminal.get("last_verified"),
            "facility_scope": terminal.get("facility_scope"),
            "source": terminal.get("source"),
            "source_url": terminal.get("source_url"),
            "coordinate_source_url": terminal.get("coordinate_source_url"),
            "location_confidence": terminal.get("location_confidence"),
        }
        features.append(
            {
                "type": "Feature",
                "properties": compact_props(props),
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        round_point_coord(terminal["coordinates"][0]),
                        round_point_coord(terminal["coordinates"][1]),
                    ],
                },
            }
        )
    return terminal_inventory.reviewed_canadian_features(features)


def compact_props(props: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in props.items() if value not in (None, "", [])}


def build_layer(
    bbox: tuple[float, float, float, float],
    rail_where: str,
    crude_terminal_where: str,
    product_terminal_where: str,
    existing_rail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if crude_terminal_where != DEFAULT_CRUDE_TERMINAL_WHERE or product_terminal_where != DEFAULT_PRODUCT_TERMINAL_WHERE:
        raise ValueError("Terminal SQL filters cannot be applied to reviewed archival snapshots; update and review the source inventory instead")
    if existing_rail is not None:
        print("Retaining existing rail geometry while rebuilding terminal observations...")
        lines = [f for f in existing_rail["features"] if f["properties"].get("feature_kind") == "rail_line"]
        if not lines or existing_rail["metadata"].get("rail_where") != rail_where or existing_rail["metadata"].get("bbox") != list(bbox):
            raise ValueError("Cached rail geometry is empty or does not match the requested extent/filter")
        raw_rail_segment_count = existing_rail["metadata"]["raw_rail_segment_count"]
        raw_rail_source_count = existing_rail["metadata"].get("raw_rail_source_row_count", raw_rail_segment_count)
    else:
        print("Fetching North American rail lines...")
        raw_lines = query_rail_geojson(bbox, rail_where)
        lines = [feature for feature in (normalize_rail_feature(f) for f in raw_lines) if feature]
        for feature in lines:
            feature["properties"] = compact_props(feature["properties"])
        raw_rail_segment_count = len(lines)
        raw_rail_source_count = len(raw_lines)
        lines = aggregate_rail_features(lines)
        print(f"  {raw_rail_segment_count:,} rail line segments grouped into {len(lines):,} render features")

    print("Reading the reviewed archival EIA crude-by-rail snapshot...")
    raw_crude = terminal_inventory.snapshot("eia_crude_rail_archive")["data"]["features"]
    if crude_terminal_where == DEFAULT_CRUDE_TERMINAL_WHERE and not raw_crude:
        raise ValueError("EIA crude terminal service returned an empty inventory; preserving existing output")
    crude = [feature for feature in (normalize_crude_terminal(f) for f in raw_crude) if feature]
    for feature in crude:
        feature["properties"] = compact_props(feature["properties"])
    print(f"  {len(crude):,} crude rail terminals")

    print("Reading the reviewed January 2020 EIA petroleum product inventory snapshot...")
    raw_products = terminal_inventory.snapshot("eia_products_archive")["data"]["features"]
    if product_terminal_where == DEFAULT_PRODUCT_TERMINAL_WHERE and not raw_products:
        raise ValueError("EIA product terminal service returned an empty inventory; preserving existing output")
    products = [feature for feature in (normalize_product_terminal(f) for f in raw_products) if feature]
    for feature in products:
        feature["properties"] = compact_props(feature["properties"])
    print(f"  {len(products):,} petroleum product terminals")

    canadian = canadian_terminal_features()
    print(f"  {len(canadian):,} Canadian curated petroleum rail terminals")
    buckeye, excluded = terminal_inventory.buckeye_features()
    colonial = terminal_inventory.colonial_features()
    us_storage = terminal_inventory.us_storage_features()
    print(f"  {len(buckeye):,} Buckeye operator-map points; {excluded} out-of-scope points omitted")
    print(f"  {len(colonial):,} Colonial storage sites with explicitly interpolated street locations")

    features = sorted(
        [*lines, *crude, *products, *canadian, *buckeye, *colonial, *us_storage],
        key=lambda f: (
            f["properties"].get("feature_kind") != "rail_line",
            f["properties"].get("category") or "",
            f["properties"].get("name") or "",
        ),
    )
    return {
        "type": "FeatureCollection",
        "name": "Railways and petroleum terminals",
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bbox": list(bbox),
            "rail_where": rail_where,
            "crude_terminal_where": crude_terminal_where,
            "product_terminal_where": product_terminal_where,
            "scope": "Canada/U.S. BTS/FRA main rail network and major industrial leads; archival EIA terminal observations from university-hosted copies, reviewed Buckeye operator-map points, Colonial street-address locations, Cushing Grandstaff regulator office location, and a curated Canadian terminal/storage set. Neither the terminal set nor minor tracks, yards, sidings, and private spurs represents complete national coverage.",
            "rail_detail": "BTS/FRA NET=M main network and NET=I major industrial leads, grouped by category, country, and owner for browser performance.",
            "raw_rail_segment_count": raw_rail_segment_count,
            "raw_rail_source_row_count": raw_rail_source_count,
            "omitted_invalid_rail_geometry_count": raw_rail_source_count - raw_rail_segment_count,
            "rail_geometry_generated_at": existing_rail["metadata"].get("rail_geometry_generated_at", existing_rail["metadata"].get("generated_at")) if existing_rail else datetime.now(timezone.utc).isoformat(),
            "raw_crude_terminal_source_row_count": len(raw_crude),
            "omitted_invalid_crude_terminal_geometry_count": len(raw_crude) - len(crude),
            "raw_product_terminal_source_row_count": len(raw_products),
            "omitted_invalid_product_terminal_geometry_count": len(raw_products) - len(products),
            "geometry_precision_note": "Rail coordinates are rounded to 0.001 degree for display (up to about 111 m per grid step); facility points retain 0.00001 degree. Source precision is not survey accuracy.",
            "grouped_rail_feature_count": len(lines),
            **terminal_inventory.inventory_metadata(canadian, buckeye, colonial, excluded),
            "reviewed_us_crude_storage_facility_count": len(us_storage) + sum(f["properties"]["category"] == "crude-storage" for f in buckeye),
            "sources": [
                {
                    "name": "BTS/FRA North American Rail Network Lines",
                    "url": NARN_LINES_URL,
                    "coverage": "Canada/U.S. main network and major industrial leads clipped to the requested rail extent; not every local track, siding, yard, or private spur",
                },
                {
                    "name": "Archived EIA Crude Oil Rail Terminals (University of Minnesota copy)",
                    "url": EIA_CRUDE_RAIL_TERMINALS_URL,
                    "coverage": "94 valid points from a 99-record public copy snapshot; underlying inventory date unavailable. Canonical EIA origin requires a token; university copy edits do not certify current operations.",
                },
                {
                    "name": "January 2020 EIA Petroleum Product Terminals (UC Merced copy)",
                    "url": EIA_PRODUCT_TERMINALS_URL,
                    "coverage": "1,476 archived EIA-815 observations as of January 2020, from a public UC Merced-hosted copy. Canonical EIA origin requires a token. Historical operator names are preserved separately from reviewed identities.",
                },
                {
                    "name": "Reviewed Canadian petroleum terminals",
                    "url": "See per-feature source_url values",
                    "coverage": "88 curated Canadian terminal/storage observations with individual coordinate provenance and review status, including 2024 NPRI points; unresolved legacy points remain explicitly unverified. Not a complete national registry.",
                },
                {"name": "Buckeye operator public asset map", "url": terminal_inventory.BUCKEYE_MAP, "coverage": "128 U.S. terminal observations including two propane terminals and Puerto Rico; Bahamas and Saint Lucia omitted. Operator GIS source edited March 2023; identity review does not certify operation or survey accuracy."},
                {"name": "Colonial Pipeline own terminals", "url": "https://www.colpipe.com/our-operations/terminals/", "coverage": "Three operator-listed storage sites placed at Census street-address interpolations, explicitly low confidence. Fredericksburg held out because source postal codes conflict. The approximately 270 connected third-party sites are not assumed Colonial-owned."},
                {"name": "Oklahoma DEQ Cushing Grandstaff storage facility", "url": "https://applications.deq.ok.gov/permitspublic/storedpermits/8122.pdf", "coverage": "One dated regulator office-location point, not a surveyed tank centroid or a current permit-status claim. No capacity is assigned to the entire complex from a commercial subset fact sheet."},
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
    parser.add_argument("--terminals-only", action="store_true", help="Rebuild terminal observations from reviewed snapshots while preserving the output's matching rail geometry")
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    existing_rail = json.loads(output.read_text(encoding="utf-8")) if args.terminals_only else None
    data = build_layer(tuple(args.bbox), args.rail_where, args.crude_terminal_where, args.product_terminal_where, existing_rail) if existing_rail is not None else build_layer(tuple(args.bbox), args.rail_where, args.crude_terminal_where, args.product_terminal_where)
    if not data["metadata"]["raw_rail_segment_count"]:
        raise ValueError("Refusing to replace the railway layer with an empty rail network")
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    temporary.replace(output)
    label = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(f"Wrote {label} with {len(data['features']):,} features ({output.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
