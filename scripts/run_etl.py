"""
Build the local Western Canada crude production store.

The pipeline has two layers:
1. Optional raw-source refresh into data/raw from official public URLs.
2. Normalization from the current analytical workbook into SQLite and web JSON.

The workbook import keeps the app immediately usable while preserving the
business logic, forecasts, blend ratios, and source harmonization already in the
analyst workbook. Raw downloads are cached for audit/rebuild work.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import io
import json
import math
import re
import sqlite3
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile as _zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PUBLIC_DATA_DIR = ROOT / "public" / "data"
REGISTRY_PATH = DATA_DIR / "asset_registry.csv"
DLS_CACHE_PATH = PROCESSED_DIR / "dls_centroids.csv"
ST44_PATH = RAW_DIR / "aer_st44_2025_q4.xlsx"
ST102_SHP_PATH = RAW_DIR / "aer_st102_facility_list_shapefile.zip"
SCHEME_GEOJSON_PATH = PUBLIC_DATA_DIR / "aer_scheme_approvals.geojson"
ST102_OIL_SANDS_GEOJSON_PATH = PUBLIC_DATA_DIR / "aer_st102_oil_sands_facilities.geojson"
ASSET_GEOMETRIES_GEOJSON_PATH = PUBLIC_DATA_DIR / "asset_geometries.geojson"
ST39_SYNTHETIC_EXTRACT_R = ROOT / "scripts" / "extract_aer_st39_synthetic.R"
DEFAULT_RSCRIPT = Path(r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe")

PETRINEX_DIR = RAW_DIR / "petrinex"
PETRINEX_AB_VOL_DIR = PETRINEX_DIR / "ab" / "vol"
PETRINEX_AB_INFRA_DIR = PETRINEX_DIR / "ab" / "infra"
PETRINEX_BC_REF_DIR = PETRINEX_DIR / "bc" / "reference"
BCER_DIR = RAW_DIR / "bcer"
BCER_PRODUCTION_ZIP = BCER_DIR / "prod_csv.zip"
BCER_WELL_INDEX_CSV = BCER_DIR / "well_index.csv"
BCER_WELL_SURFACE_GEOJSON = BCER_DIR / "well_surface_locations.geojson"
M3_TO_BBL = 6.28981077
ON_DEMAND_RECORD_SOURCES = {
    "petrinex_ab_conventional_vol",
    "petrinex_ab_pentanes_plus_vol",
    "petrinex_ab_condensate_vol",
    "bcer_well_production",
}
PETRINEX_AB_EARLIEST_PUBLIC_PERIOD = "2022-01"

DEFAULT_WORKBOOK = Path(
    r"C:\Users\aftik\Documents\Projects\Western Canada crude oil S&D"
    r"\st53_company_scheme_breakdown_v25.xlsx"
)

CUTOFF = dt.date(2015, 1, 1)
RUN_DATE = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)

SOURCE_MANIFEST = [
    {
        "source_id": "aer_st53",
        "agency": "Alberta Energy Regulator",
        "name": "AER ST53 In-Situ Oil Sands Scheme Production",
        "url": "https://www.aer.ca/documents/sts/ST53/ST53_Current.xls",
        "raw_file": "aer_st53_current.xls",
        "grain": "monthly scheme/asset",
    },
    {
        "source_id": "aer_st39",
        "agency": "Alberta Energy Regulator",
        "name": "AER ST39 Alberta Mined Oil Sands Production",
        "url": "https://www.aer.ca/documents/sts/ST39.xls",
        "raw_file": "aer_st39_current.xls",
        "grain": "monthly mine/project",
    },
    {
        "source_id": "aer_st44",
        "agency": "Alberta Energy Regulator",
        "name": "AER ST44 Active Oil Sands Schemes",
        "url": "https://static.aer.ca/prd/documents/sts/ST44_2025-Q4.xlsx",
        "raw_file": "aer_st44_2025_q4.xlsx",
        "grain": "active scheme bridge",
    },
    {
        "source_id": "aer_scheme_spatial",
        "agency": "Alberta Energy Regulator",
        "name": "AER Scheme Approval Spatial Data",
        "url": "https://www.aer.ca/data/shapefiles/Scheme_Approval_SHP.zip",
        "raw_file": "aer_scheme_approval_spatial.zip",
        "grain": "scheme geometry",
    },
    {
        "source_id": "aer_st102_facility_spatial",
        "agency": "Alberta Energy Regulator",
        "name": "AER ST102 Facility List Shapefile",
        "url": "https://www.aer.ca/data/codes/ST102-SHP.zip",
        "raw_file": "aer_st102_facility_list_shapefile.zip",
        "grain": "facility point geometry",
    },
    {
        "source_id": "petrinex_ab_conventional_vol",
        "agency": "Petrinex",
        "name": "Petrinex Alberta Conventional Volumetrics",
        "url": "https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Vol/YYYY-MM/CSV",
        "raw_file": "petrinex/ab/vol/Vol_YYYY-MM-AB.zip",
        "grain": "monthly well/facility/DLS",
        "download": False,
    },
    {
        "source_id": "petrinex_ab_well_facility_link",
        "agency": "Petrinex",
        "name": "Petrinex Alberta Well to Facility Link",
        "url": "https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Infra/Well%20to%20Facility%20Link/CSV",
        "raw_file": "petrinex/ab/infra/well_to_facility_link_ab.zip",
        "grain": "current well/facility/DLS bridge",
        "download": False,
    },
    {
        "source_id": "petrinex_ab_facility_infrastructure",
        "agency": "Petrinex",
        "name": "Petrinex Alberta Facility Infrastructure",
        "url": "https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Infra/Facility%20Infrastructure/CSV",
        "raw_file": "petrinex/ab/infra/facility_infrastructure_ab.zip",
        "grain": "current facility/DLS reference",
        "download": False,
    },
    {
        "source_id": "petrinex_bc_facility_ids",
        "agency": "Petrinex",
        "name": "Petrinex BC PRA Facility IDs",
        "url": "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAFacilityIds.csv",
        "raw_file": "petrinex/bc/reference/PRAFacilityIds.csv",
        "grain": "BC facility reference",
    },
    {
        "source_id": "petrinex_bc_formation_codes",
        "agency": "Petrinex",
        "name": "Petrinex BC PRA Formation Codes",
        "url": "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAFormationCodes.csv",
        "raw_file": "petrinex/bc/reference/PRAFormationCodes.csv",
        "grain": "BC formation reference",
    },
    {
        "source_id": "petrinex_bc_activity_codes",
        "agency": "Petrinex",
        "name": "Petrinex BC PRA Activity Codes",
        "url": "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAActivityCodes.csv",
        "raw_file": "petrinex/bc/reference/PRAActivityCodes.csv",
        "grain": "BC activity reference",
    },
    {
        "source_id": "bcer_well_production",
        "agency": "British Columbia Energy Regulator",
        "name": "BCER Production Data for All Wells in B.C.",
        "url": "https://iris.bcogc.ca/download/prod_csv.zip",
        "raw_file": "bcer/prod_csv.zip",
        "grain": "monthly well/completion/zone production",
        "download": False,
    },
    {
        "source_id": "bcer_well_index",
        "agency": "British Columbia Energy Regulator",
        "name": "BCER Well Index",
        "url": "https://iris.bcogc.ca/download/well_index.csv",
        "raw_file": "bcer/well_index.csv",
        "grain": "well reference",
        "download": False,
    },
    {
        "source_id": "bcer_well_surface_locations",
        "agency": "British Columbia Energy Regulator",
        "name": "BCER Well Surface Hole Locations",
        "url": "https://geoweb-ags.bc-er.ca/arcgis/rest/services/PASR/PASR_WELL_SURFACE_STATE_FA_PT/MapServer/0/query",
        "raw_file": "bcer/well_surface_locations.geojson",
        "grain": "well surface point geometry",
        "download": False,
    },
]


ST39_SYNTHETIC_APPROVAL_MAP = {
    "ABOS0093231": {"display_name": "Horizon Upgrader", "company": "CNRL"},
    "ABOS0144578": {"display_name": "Sturgeon Refinery", "company": "North West Redwater"},
    "ABOS0077192": {"display_name": "Scotford Upgrader", "company": "CNRL"},
    "ABOS0077189": {"display_name": "Suncor Base Plant Upgrader", "company": "Suncor"},
    "ABOS0077533": {"display_name": "Syncrude Mildred Lake Upgrader", "company": "Syncrude JV"},
}

STREAM_LEGEND_KEYS_EXPORT = {
    "In-situ bitumen": "in-situ",
    "Mined bitumen gross": "mined",
    "Synthetic crude oil": "synthetic",
    "Conventional crude oil": "conventional",
    "Pentanes plus total": "pentanes-plus",
    "Heavy crude oil": "heavy-conv",
    "Condensate Production": "condensate",
    "Condensate production": "condensate",
    "Total Condensate Supply": "condensate",
}

SYSTEM_LEGEND_KEYS_EXPORT = {
    "in_situ": "in-situ",
    "mined": "mined",
    "synthetic": "synthetic",
    "conventional": "conventional",
    "pentanes_plus": "pentanes-plus",
    "heavy_conventional": "heavy-conv",
    "condensate": "condensate",
    "gas_plant": "gas-plant",
    "integrated_plant": "integrated-plant",
    "spec_plant": "spec-plant",
}


PROVINCE_COORDS = {
    "Alberta": (53.9333, -116.5765),
    "Saskatchewan": (52.9399, -106.4509),
    "British Columbia": (54.0, -125.0),
    "Manitoba": (53.7609, -98.8139),
    "Northwest Territories": (64.8255, -124.8457),
    "Western Canada": (55.4, -111.5),
}


def log(message: str) -> None:
    print(message, flush=True)


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\n", " ")).strip()


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        if math.isnan(value):
            return None
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def as_date(value: Any) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m"):
        try:
            parsed = dt.datetime.strptime(text[: len(fmt)], fmt)
            return parsed.date()
        except ValueError:
            pass
    return None


def parse_period(value: str) -> tuple[int, int] | None:
    value = clean_text(value)
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        return None
    year, month = int(value[:4]), int(value[5:7])
    if not 1 <= month <= 12:
        return None
    return year, month


def month_end(value: dt.date) -> dt.date:
    if value.month == 12:
        return dt.date(value.year, 12, 31)
    return dt.date(value.year, value.month + 1, 1) - dt.timedelta(days=1)


def month_period(value: dt.date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def iter_month_periods(start: str, end: str) -> list[str]:
    start_parts = parse_period(start)
    end_parts = parse_period(end)
    if not start_parts or not end_parts:
        return []
    year, month = start_parts
    end_year, end_month = end_parts
    periods = []
    while (year, month) <= (end_year, end_month):
        periods.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return periods


def recent_month_periods(end_period: str, count: int) -> list[str]:
    end_parts = parse_period(end_period)
    if not end_parts or count <= 0:
        return [end_period] if end_parts else []
    year, month = end_parts
    periods = []
    for _ in range(count):
        periods.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return sorted(periods)


def normalize_stream(header: str) -> str:
    text = clean_text(header)
    text = re.sub(r"\(bbl/d\)", "", text, flags=re.I).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def read_workbook_latest_actual(workbook_path: Path) -> dt.date:
    try:
        wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
        if "Trading Dashboard" in wb.sheetnames:
            latest = as_date(wb["Trading Dashboard"]["D6"].value)
            if latest:
                return month_end(latest)
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: could not read workbook latest actual date: {exc}")
    cached_petrinex_months: list[dt.date] = []
    for path in PETRINEX_AB_VOL_DIR.glob("Vol_????-??-AB.zip"):
        match = re.search(r"Vol_(\d{4}-\d{2})-AB\.zip$", path.name)
        if not match:
            continue
        period = parse_period(match.group(1))
        if not period:
            continue
        cached_petrinex_months.append(month_end(dt.date(period[0], period[1], 1)))
    if cached_petrinex_months:
        # Use the latest common AB Petrinex month as the app default when the
        # workbook summary cell is blank. This avoids defaulting to a partial
        # forecast/current-day date where the location-specific layers are absent.
        return max(cached_petrinex_months)
    return month_end(dt.date.today().replace(day=1))


def petrinex_ab_vol_path(period: str) -> Path:
    return PETRINEX_AB_VOL_DIR / f"Vol_{period}-AB.zip"


def download_url(url: str, target: Path, force: bool = False) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return {
            "url": url,
            "local_path": str(target.relative_to(ROOT)),
            "status": "cached",
            "error": None,
        }
    try:
        log(f"Downloading {url} -> {target}")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "western-canada-production-etl/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            target.write_bytes(response.read())
        return {
            "url": url,
            "local_path": str(target.relative_to(ROOT)),
            "status": "downloaded",
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "url": url,
            "local_path": str(target.relative_to(ROOT)),
            "status": "failed",
            "error": str(exc),
        }


def ensure_petrinex_cache(
    latest_actual: dt.date,
    months: int,
    start_period: str | None,
    force: bool = False,
    refresh: bool = False,
) -> list[dict[str, Any]]:
    """Cache the Petrinex files needed for the conventional location layer.

    Alberta volumes use the documented monthly API. BC's public Petrinex page
    exposes reference files, not a tested monthly volumetric API, so the ETL
    caches those references but does not synthesize BC production volumes.
    """

    status: list[dict[str, Any]] = []
    latest_period = month_period(latest_actual)
    if start_period:
        periods = iter_month_periods(start_period, latest_period)
    else:
        periods = recent_month_periods(latest_period, max(1, months))

    for period in periods:
        if parse_period(period) is None:
            continue
        url = f"https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Vol/{period}/CSV"
        item = download_url(url, petrinex_ab_vol_path(period), force=force if refresh else False)
        item.update(
            {
                "source_id": "petrinex_ab_conventional_vol",
                "period": period,
                "agency": "Petrinex",
                "name": "Petrinex Alberta Conventional Volumetrics",
                "raw_file": str(petrinex_ab_vol_path(period).relative_to(RAW_DIR)),
                "grain": "monthly well/facility/DLS",
            }
        )
        status.append(item)

    infra_sources = [
        (
            "petrinex_ab_well_facility_link",
            "Petrinex Alberta Well to Facility Link",
            "https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Infra/Well%20to%20Facility%20Link/CSV",
            PETRINEX_AB_INFRA_DIR / "well_to_facility_link_ab.zip",
        ),
        (
            "petrinex_ab_facility_infrastructure",
            "Petrinex Alberta Facility Infrastructure",
            "https://www.petrinex.gov.ab.ca/publicdata/API/Files/AB/Infra/Facility%20Infrastructure/CSV",
            PETRINEX_AB_INFRA_DIR / "facility_infrastructure_ab.zip",
        ),
    ]
    for source_id, name, url, target in infra_sources:
        item = download_url(url, target, force=force if refresh else False)
        item.update(
            {
                "source_id": source_id,
                "agency": "Petrinex",
                "name": name,
                "raw_file": str(target.relative_to(RAW_DIR)),
                "grain": "current infrastructure",
            }
        )
        status.append(item)

    bc_refs = [
        (
            "petrinex_bc_facility_ids",
            "Petrinex BC PRA Facility IDs",
            "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAFacilityIds.csv",
            PETRINEX_BC_REF_DIR / "PRAFacilityIds.csv",
        ),
        (
            "petrinex_bc_formation_codes",
            "Petrinex BC PRA Formation Codes",
            "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAFormationCodes.csv",
            PETRINEX_BC_REF_DIR / "PRAFormationCodes.csv",
        ),
        (
            "petrinex_bc_activity_codes",
            "Petrinex BC PRA Activity Codes",
            "https://www.petrinex.gov.ab.ca/bbreportsBC/PRAActivityCodes.csv",
            PETRINEX_BC_REF_DIR / "PRAActivityCodes.csv",
        ),
    ]
    for source_id, name, url, target in bc_refs:
        item = download_url(url, target, force=force if refresh else False)
        item.update(
            {
                "source_id": source_id,
                "agency": "Petrinex",
                "name": name,
                "raw_file": str(target.relative_to(RAW_DIR)),
                "grain": "BC reference only",
            }
        )
        status.append(item)
    return status


def download_bcer_well_surface_points(force: bool = False) -> dict[str, Any]:
    url_base = (
        "https://geoweb-ags.bc-er.ca/arcgis/rest/services/"
        "PASR/PASR_WELL_SURFACE_STATE_FA_PT/MapServer/0/query"
    )
    BCER_WELL_SURFACE_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    if BCER_WELL_SURFACE_GEOJSON.exists() and not force:
        return {
            "url": url_base,
            "local_path": str(BCER_WELL_SURFACE_GEOJSON.relative_to(ROOT)),
            "status": "cached",
            "error": None,
            "source_id": "bcer_well_surface_locations",
            "agency": "British Columbia Energy Regulator",
            "name": "BCER Well Surface Hole Locations",
            "raw_file": str(BCER_WELL_SURFACE_GEOJSON.relative_to(RAW_DIR)),
            "grain": "well surface point geometry",
        }

    features: list[dict[str, Any]] = []
    offset = 0
    page_size = 2000
    try:
        while True:
            params = {
                "where": "1=1",
                "outFields": "WELL_AUTHORITY_NUMBER,WELL_NAME,OPERATOR_ABBREVIATION,WELL_SURFACE_LOCATION",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": str(offset),
                "resultRecordCount": str(page_size),
                "f": "geojson",
            }
            url = f"{url_base}?{urllib.parse.urlencode(params)}"
            log(f"Downloading BCER well surface points offset {offset:,}")
            req = urllib.request.Request(url, headers={"User-Agent": "western-canada-production-etl/1.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                page = json.loads(response.read().decode("utf-8"))
            if page.get("error"):
                raise RuntimeError(page["error"])
            page_features = page.get("features", [])
            if not page_features:
                break
            features.extend(page_features)
            if len(page_features) < page_size or not page.get("properties", {}).get("exceededTransferLimit"):
                break
            offset += page_size

        BCER_WELL_SURFACE_GEOJSON.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")),
            encoding="utf-8",
        )
        return {
            "url": url_base,
            "local_path": str(BCER_WELL_SURFACE_GEOJSON.relative_to(ROOT)),
            "status": "downloaded",
            "error": None,
            "source_id": "bcer_well_surface_locations",
            "agency": "British Columbia Energy Regulator",
            "name": "BCER Well Surface Hole Locations",
            "raw_file": str(BCER_WELL_SURFACE_GEOJSON.relative_to(RAW_DIR)),
            "grain": f"{len(features):,} well surface point geometries",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "url": url_base,
            "local_path": str(BCER_WELL_SURFACE_GEOJSON.relative_to(ROOT)),
            "status": "failed",
            "error": str(exc),
            "source_id": "bcer_well_surface_locations",
            "agency": "British Columbia Energy Regulator",
            "name": "BCER Well Surface Hole Locations",
            "raw_file": str(BCER_WELL_SURFACE_GEOJSON.relative_to(RAW_DIR)),
            "grain": "well surface point geometry",
        }


def ensure_bcer_cache(force: bool = False, refresh: bool = False) -> list[dict[str, Any]]:
    status = []
    for source_id, name, url, target, grain in [
        (
            "bcer_well_production",
            "BCER Production Data for All Wells in B.C.",
            "https://iris.bcogc.ca/download/prod_csv.zip",
            BCER_PRODUCTION_ZIP,
            "monthly well/completion/zone production",
        ),
        (
            "bcer_well_index",
            "BCER Well Index",
            "https://iris.bcogc.ca/download/well_index.csv",
            BCER_WELL_INDEX_CSV,
            "well reference",
        ),
    ]:
        item = download_url(url, target, force=force if refresh else False)
        item.update(
            {
                "source_id": source_id,
                "agency": "British Columbia Energy Regulator",
                "name": name,
                "raw_file": str(target.relative_to(RAW_DIR)),
                "grain": grain,
            }
        )
        status.append(item)
    status.append(download_bcer_well_surface_points(force=force if refresh else False))
    return status


def open_nested_petrinex_csv(zip_path: Path) -> csv.DictReader:
    data = zip_path.read_bytes()
    with _zipfile.ZipFile(io.BytesIO(data)) as outer:
        first = outer.namelist()[0]
        inner_bytes = outer.read(first)
    if inner_bytes[:2] == b"PK":
        with _zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
            inner_name = next(name for name in inner.namelist() if name.lower().endswith(".csv"))
            csv_bytes = inner.read(inner_name)
    else:
        csv_bytes = inner_bytes
    return csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))


def format_dls(lsd: Any, section: Any, township: Any, range_: Any, meridian: Any) -> str | None:
    try:
        lsd_i = int(str(lsd).strip())
        section_i = int(str(section).strip())
        township_i = int(str(township).strip())
        range_i = int(str(range_).strip())
        meridian_i = int(str(meridian).strip())
    except (TypeError, ValueError):
        return None
    if not (1 <= lsd_i <= 16 and 1 <= section_i <= 36 and 1 <= township_i <= 126 and 1 <= range_i <= 36):
        return None
    return f"{lsd_i:02d}-{section_i:02d}-{township_i:03d}-{range_i:02d}W{meridian_i}"


def parse_dls_label(label: str) -> tuple[int, int, int, int, int] | None:
    match = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{2,3})-(\d{1,2})W([456])", clean_text(label))
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def parse_bc_location(location: str) -> str | None:
    match = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{2,3})-(\d{1,2})W([456])", clean_text(location))
    if not match:
        return None
    return format_dls(*match.groups())


def load_dls_cache() -> dict[tuple[str, str], dict[str, str]]:
    cache: dict[tuple[str, str], dict[str, str]] = {}
    if not DLS_CACHE_PATH.exists():
        return cache
    with DLS_CACHE_PATH.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            province = row.get("province", "")
            dls = row.get("dls", "")
            if province and dls:
                cache[(province, dls)] = row
    return cache


def save_dls_cache(cache: dict[tuple[str, str], dict[str, str]]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = ["province", "dls", "latitude", "longitude", "method", "updated_at"]
    with DLS_CACHE_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (_, _), row in sorted(cache.items()):
            writer.writerow({key: row.get(key, "") for key in fieldnames})


class AgsAtsConverter:
    def __init__(self) -> None:
        self.url = "https://www1.aer.ca/GISConversionTools/ATSDegreesConverter.aspx"
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        self.base_fields: dict[str, str] | None = None

    def _init_fields(self) -> None:
        if self.base_fields is not None:
            return
        req = urllib.request.Request(self.url, headers={"User-Agent": "western-canada-production-etl/1.0"})
        html = self.opener.open(req, timeout=30).read().decode("utf-8", "replace")
        base: dict[str, str] = {"__EVENTTARGET": "", "__EVENTARGUMENT": ""}
        for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
            match = re.search(rf'name="{re.escape(name)}"[^>]*value="([^"]*)"', html)
            base[name] = match.group(1) if match else ""
        base.update({"position": "C", "feet_west": "0", "feet_north": "0", "btnSubmit": "CONVERT"})
        self.base_fields = base

    def convert(self, dls: str) -> tuple[float, float] | None:
        parts = parse_dls_label(dls)
        if not parts:
            return None
        lsd, section, township, range_, meridian = parts
        self._init_fields()
        assert self.base_fields is not None
        fields = dict(self.base_fields)
        fields.update(
            {
                "lsd": str(lsd),
                "section": str(section),
                "township": str(township),
                "range": str(range_),
                "meridian": str(meridian),
            }
        )
        data = urllib.parse.urlencode(fields).encode()
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "western-canada-production-etl/1.0",
            },
        )
        html = self.opener.open(req, timeout=30).read().decode("utf-8", "replace")
        plain = re.sub(r"<[^>]+>", " ", html)
        plain = re.sub(r"\s+", " ", plain)
        idx = plain.find("Latitude Longitude")
        if idx < 0:
            return None
        nums = re.findall(r"[-+]?\d+(?:\.\d+)?", plain[idx : idx + 500])
        if len(nums) < 8:
            return None
        return float(nums[6]), -float(nums[7])


def approximate_dls_centroid(dls: str) -> tuple[float, float] | None:
    parts = parse_dls_label(dls)
    if not parts:
        return None
    lsd, section, township, range_, meridian = parts
    meridian_lon = {4: -110.0, 5: -114.0, 6: -118.0}.get(meridian)
    if meridian_lon is None:
        return None

    sec_row = (section - 1) // 6
    sec_pos = (section - 1) % 6
    sec_col_west = sec_pos if sec_row % 2 == 0 else 5 - sec_pos

    lsd_row = (lsd - 1) // 4
    lsd_pos = (lsd - 1) % 4
    lsd_col_west = lsd_pos if lsd_row % 2 == 0 else 3 - lsd_pos

    miles_north = (township - 1) * 6 + sec_row + (lsd_row + 0.5) / 4
    lat = 49.0 + miles_north / 69.0
    miles_west = (range_ - 1) * 6 + sec_col_west + (lsd_col_west + 0.5) / 4
    lon = meridian_lon - miles_west / (69.0 * math.cos(math.radians(lat)))
    return lat, lon


def resolve_dls_locations(
    site_items: list[dict[str, Any]],
    official_limit: int,
) -> dict[tuple[str, str], dict[str, str]]:
    cache = load_dls_cache()
    converter = AgsAtsConverter()
    official_used = 0
    changed = False
    now = RUN_DATE.isoformat()

    unique_sites: dict[tuple[str, str], float] = {}
    for item in site_items:
        key = (item["province"], item["dls"])
        unique_sites[key] = unique_sites.get(key, 0.0) + float(item.get("volume_bbl_d", 0.0))

    for key, _volume in sorted(unique_sites.items(), key=lambda kv: kv[1], reverse=True):
        province, dls = key
        if key in cache:
            continue
        coords = None
        method = "approx_dls_centroid"
        if province == "Alberta" and official_used < official_limit:
            try:
                coords = converter.convert(dls)
                if coords:
                    method = "ags_ats_v4_1_web_converter"
                    official_used += 1
                    time.sleep(0.08)
            except Exception as exc:  # noqa: BLE001
                log(f"  warning: AGS ATS conversion failed for {dls}: {exc}")
        if coords is None:
            coords = approximate_dls_centroid(dls)
        if coords is None:
            continue
        lat, lon = coords
        cache[key] = {
            "province": province,
            "dls": dls,
            "latitude": f"{lat:.7f}",
            "longitude": f"{lon:.7f}",
            "method": method,
            "updated_at": now,
        }
        changed = True
    if changed:
        save_dls_cache(cache)
    return cache


def download_sources(force: bool = False) -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for source in SOURCE_MANIFEST:
        target = RAW_DIR / source["raw_file"]
        status = "skipped"
        error = None
        if not source.get("download", True) or not str(source["url"]).lower().startswith(("http://", "https://")):
            results.append(
                {
                    **source,
                    "local_path": str(target.relative_to(ROOT)),
                    "status": "local",
                    "error": None,
                }
            )
            continue
        if force or not target.exists():
            status = "downloaded"
            try:
                log(f"Downloading {source['source_id']} -> {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                req = urllib.request.Request(
                    source["url"],
                    headers={"User-Agent": "western-canada-production-etl/1.0"},
                )
                with urllib.request.urlopen(req, timeout=90) as response:
                    target.write_bytes(response.read())
            except Exception as exc:  # noqa: BLE001 - cache failures should not block workbook import
                status = "failed"
                error = str(exc)
                log(f"  warning: {source['source_id']} download failed: {error}")
        results.append(
            {
                **source,
                "local_path": str(target.relative_to(ROOT)),
                "status": status,
                "error": error,
            }
        )
    return results


@dataclass
class Asset:
    asset_id: str
    display_name: str
    source_id: str
    source_name: str
    production_system: str
    asset_kind: str
    company: str
    province: str
    latitude: float | None
    longitude: float | None
    ownership_text: str = ""
    is_rollup: bool = False
    notes: str = ""
    coordinate_method: str = ""
    location_confidence: str = ""
    location_basis: str = ""
    geometry_kind: str = ""
    geometry_source: str = ""
    geometry_features: list[dict[str, Any]] = field(default_factory=list)


def infer_coordinate_method(
    latitude: float | None,
    longitude: float | None,
    notes: str = "",
    registry_row: dict[str, str] | None = None,
) -> str:
    if latitude is None or longitude is None:
        return "unmapped"
    text = clean_text(notes)
    match = re.search(r"coordinate method:\s*([^.;]+)", text, flags=re.I)
    if match:
        return slug(match.group(1))
    lower = text.lower()
    if "aer st102" in lower:
        return "aer_st102_facility_point"
    if "aer scheme approval spatial data centroid" in lower or "aer spatial centroid" in lower:
        return "aer_scheme_approval_centroid"
    if "st44" in lower and "dls" in lower:
        return "aer_st44_dls_centroid"
    if "approx" in lower:
        return "asset_registry_manual_estimate" if registry_row else "manual_estimate"
    if registry_row:
        return "asset_registry_manual"
    return "manual_or_unspecified"


def coordinate_confidence(
    latitude: float | None,
    longitude: float | None,
    method: str,
    geometry_kind: str = "",
    is_rollup: bool = False,
    asset_kind: str = "",
) -> str:
    if latitude is None or longitude is None:
        return "unmapped"
    if is_rollup or asset_kind in {"province", "province_refinery", "region", "company_rollup", "asset_bucket"}:
        return "aggregate"
    method = slug(method)
    geometry_kind = slug(geometry_kind)
    if method in {"aer_st102_facility_point", "bcer_well_surface_point", "aer_st37_well_surface_point"}:
        return "exact"
    if geometry_kind == "scheme_polygon" or method in {"aer_scheme_approval_centroid"}:
        return "high"
    if method in {"ags_ats_v4_1_web_converter", "aer_st44_dls_centroid", "asset_registry_manual"}:
        return "medium"
    if method in {"approx_dls_centroid", "asset_registry_manual_estimate", "manual_estimate", "manual_or_unspecified"}:
        return "low"
    return "medium"


def load_registry() -> dict[tuple[str, str, str], dict[str, str]]:
    registry: dict[tuple[str, str, str], dict[str, str]] = {}
    if not REGISTRY_PATH.exists():
        return registry
    with REGISTRY_PATH.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                slug(row.get("production_system", "")),
                slug(row.get("company", "")),
                slug(row.get("asset_name", "")),
            )
            registry[key] = row
    return registry


def registry_lookup(
    registry: dict[tuple[str, str, str], dict[str, str]],
    production_system: str,
    company: str,
    asset_name: str,
) -> dict[str, str] | None:
    keys = [
        (slug(production_system), slug(company), slug(asset_name)),
        (slug(production_system), "", slug(asset_name)),
        ("", slug(company), slug(asset_name)),
        ("", "", slug(asset_name)),
    ]
    for key in keys:
        if key in registry:
            return registry[key]
    return None


def source_name(source_id: str) -> str:
    for source in SOURCE_MANIFEST:
        if source["source_id"] == source_id:
            return source["name"]
    return source_id


def rscript_path() -> Path | None:
    if DEFAULT_RSCRIPT.exists():
        return DEFAULT_RSCRIPT
    return None


def extract_st39_current_synthetic() -> list[dict[str, Any]]:
    """Read the cached official AER ST39 current XLS synthetic section.

    The Python runtime used by this project does not include xlrd, while the
    workstation already has R/readxl available. Keep the bridge narrow: R only
    extracts the official synthetic production rows into a CSV; Python owns all
    mapping, units, and export logic.
    """
    raw_path = RAW_DIR / "aer_st39_current.xls"
    runner = rscript_path()
    if not raw_path.exists() or not runner or not ST39_SYNTHETIC_EXTRACT_R.exists():
        return []
    output_path = PROCESSED_DIR / "aer_st39_current_synthetic.csv"
    try:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                str(runner),
                str(ST39_SYNTHETIC_EXTRACT_R),
                str(raw_path),
                str(output_path),
            ],
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            log(f"  warning: official ST39 synthetic extract failed: {result.stderr.strip()}")
            return []
        rows: list[dict[str, Any]] = []
        with output_path.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                period = clean_text(row.get("period"))
                volume_m3 = as_float(row.get("volume_m3"))
                if not period or volume_m3 is None or volume_m3 <= 0:
                    continue
                rows.append(
                    {
                        "operator": clean_text(row.get("operator")),
                        "approval": clean_text(row.get("approval")),
                        "facility": clean_text(row.get("facility")),
                        "period": period,
                        "header_period": clean_text(row.get("header_period")),
                        "volume_m3": volume_m3,
                    }
                )
        return rows
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: official ST39 synthetic extract failed: {exc}")
        return []


def overlay_official_st39_current_synthetic(
    records: list[dict[str, Any]],
    add_asset: Any,
    add_record: Any,
    oil_sands_locations: dict[str, Any],
) -> None:
    rows = extract_st39_current_synthetic()
    if not rows:
        return

    by_period: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_period[row["period"]].append(row)

    removed = 0
    override_dates = {
        month_end(dt.date(int(period[:4]), int(period[5:7]), 1)).isoformat()
        for period in by_period
        if parse_period(period)
    }
    kept: list[dict[str, Any]] = []
    for record in records:
        if (
            record.get("source_id") == "aer_st39"
            and record.get("stream") == "Synthetic crude oil"
            and record.get("date") in override_dates
        ):
            removed += 1
            continue
        kept.append(record)
    records[:] = kept

    added = 0
    for period, period_rows in sorted(by_period.items()):
        parsed = parse_period(period)
        if not parsed:
            continue
        year, month = parsed
        date_value = dt.date(year, month, 1)
        days = calendar.monthrange(year, month)[1]
        for row in period_rows:
            mapping = ST39_SYNTHETIC_APPROVAL_MAP.get(row["approval"])
            if not mapping:
                continue
            volume_bbl_d = row["volume_m3"] * M3_TO_BBL / days
            location = resolve_oil_sands_asset_location(
                "synthetic",
                mapping["company"],
                mapping["display_name"],
                oil_sands_locations,
            )
            asset_id = add_asset(
                display_name=mapping["display_name"],
                source_id="aer_st39",
                production_system="synthetic",
                company=mapping["company"],
                province="Alberta",
                asset_kind="upgrader",
                latitude=as_float(location.get("latitude")) if location else None,
                longitude=as_float(location.get("longitude")) if location else None,
                coordinate_method=clean_text(location.get("method")) if location else None,
                geometry_kind=clean_text(location.get("geometry_kind")) if location else "",
                geometry_source=clean_text(location.get("geometry_source")) if location else "",
                notes=(
                    "Official AER ST39 current XLS synthetic crude oil production "
                    f"for {row['facility']} ({row['approval']}). "
                    f"{clean_text(location.get('notes')) if location else ''}"
                ),
            )
            add_record(
                date_value,
                asset_id,
                "Synthetic crude oil",
                volume_bbl_d,
                "AER ST39 current XLS",
                row["approval"],
                "aer_st39",
                scenario="actual",
            )
            added += 1

    log(
        "  AER ST39 official current synthetic overlay: "
        f"removed {removed:,} workbook rows and added {added:,} official rows "
        f"for {', '.join(sorted(override_dates))}."
    )


def company_from_ownership(text: str) -> str:
    value = clean_text(text)
    if not value:
        return ""
    if "Syncrude" in value or "Sinopec" in value:
        return "Syncrude JV"
    first = value.split("  ")[0].strip()
    first = re.sub(r"\s+\d+(\.\d+)?%.*$", "", first).strip()
    first = first.replace("(acq. Shell 2017)", "").strip()
    aliases = {
        "IOL": "Imperial Oil",
        "Imperial": "Imperial Oil",
        "CNRL": "CNRL",
        "Suncor": "Suncor",
    }
    return aliases.get(first, first)


def normalize_match_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", clean_text(value).upper()).strip()


def approval_numbers(value: str) -> list[str]:
    return [match.upper() for match in re.findall(r"\b\d{3,5}[A-Z]*\b", clean_text(value).upper())]


def approval_root(value: str) -> str:
    match = re.match(r"(\d+)", clean_text(value).upper())
    return match.group(1) if match else ""


def read_dbf_bytes(data: bytes) -> list[dict[str, str]]:
    num_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]

    fields: list[tuple[str, str, int, int]] = []
    offset = 32
    while offset < header_len - 1:
        field = data[offset : offset + 32]
        if field[0] == 0x0D:
            break
        field_name = field[:11].split(b"\x00", 1)[0].decode("latin1", errors="ignore").strip()
        fields.append((field_name, chr(field[11]), field[16], field[17]))
        offset += 32

    rows: list[dict[str, str]] = []
    offset = header_len
    for _ in range(num_records):
        raw_row = data[offset : offset + record_len]
        offset += record_len
        if not raw_row or raw_row[0:1] == b"*":
            continue
        cursor = 1
        row: dict[str, str] = {}
        for field_name, field_type, field_len, _field_dec in fields:
            raw = raw_row[cursor : cursor + field_len]
            cursor += field_len
            text = raw.decode("latin1", errors="ignore").strip()
            if field_type == "D" and len(text) == 8:
                text = f"{text[:4]}-{text[4:6]}-{text[6:]}"
            row[field_name] = text
        rows.append(row)
    return rows


def read_point_shapes(data: bytes) -> list[tuple[float, float] | None]:
    offset = 100
    points: list[tuple[float, float] | None] = []
    while offset + 8 <= len(data):
        _record_number, content_words = struct.unpack(">2i", data[offset : offset + 8])
        offset += 8
        content = data[offset : offset + content_words * 2]
        offset += content_words * 2
        if len(content) < 4:
            continue
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type == 0:
            points.append(None)
            continue
        if shape_type != 1 or len(content) < 20:
            points.append(None)
            continue
        lon, lat = struct.unpack("<2d", content[4:20])
        points.append((lat, lon))
    return points


def polygon_centroid_area(ring: list[list[float]]) -> tuple[float, float, float] | None:
    if len(ring) < 4:
        return None
    area_twice = 0.0
    cx = 0.0
    cy = 0.0
    for idx in range(len(ring) - 1):
        x0, y0 = ring[idx]
        x1, y1 = ring[idx + 1]
        cross = x0 * y1 - x1 * y0
        area_twice += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area_twice) < 1e-12:
        lon = sum(point[0] for point in ring[:-1]) / max(1, len(ring) - 1)
        lat = sum(point[1] for point in ring[:-1]) / max(1, len(ring) - 1)
        return lat, lon, 0.0
    area = area_twice / 2.0
    lon = cx / (3.0 * area_twice)
    lat = cy / (3.0 * area_twice)
    return lat, lon, abs(area)


def geometry_centroid_area(geometry: dict[str, Any]) -> tuple[float, float, float] | None:
    if not geometry:
        return None
    polygons = []
    if geometry.get("type") == "Polygon":
        polygons = [geometry.get("coordinates", [])]
    elif geometry.get("type") == "MultiPolygon":
        polygons = geometry.get("coordinates", [])
    weighted_lat = weighted_lon = weighted_area = 0.0
    fallback: tuple[float, float] | None = None
    for polygon in polygons:
        if not polygon:
            continue
        result = polygon_centroid_area(polygon[0])
        if not result:
            continue
        lat, lon, area = result
        fallback = fallback or (lat, lon)
        if area <= 0:
            continue
        weighted_lat += lat * area
        weighted_lon += lon * area
        weighted_area += area
    if weighted_area > 0:
        return weighted_lat / weighted_area, weighted_lon / weighted_area, weighted_area
    if fallback:
        return fallback[0], fallback[1], 0.0
    return None


def combined_centroid(features: list[dict[str, Any]]) -> tuple[float, float] | None:
    weighted_lat = weighted_lon = weighted_area = 0.0
    fallback = None
    for feature in features:
        centroid = feature.get("centroid")
        if not centroid:
            continue
        lat, lon = centroid
        area = float(feature.get("area") or 0.0)
        fallback = fallback or (lat, lon)
        if area <= 0:
            continue
        weighted_lat += lat * area
        weighted_lon += lon * area
        weighted_area += area
    if weighted_area > 0:
        return weighted_lat / weighted_area, weighted_lon / weighted_area
    return fallback


def load_scheme_feature_index() -> dict[str, Any]:
    if not SCHEME_GEOJSON_PATH.exists() and (RAW_DIR / "aer_scheme_approval_spatial.zip").exists():
        try:
            from build_scheme_geojson import build as build_scheme_payload

            SCHEME_GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            SCHEME_GEOJSON_PATH.write_text(
                json.dumps(build_scheme_payload(), separators=(",", ":")),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            log(f"  warning: could not build AER scheme GeoJSON for location matching: {exc}")
    if not SCHEME_GEOJSON_PATH.exists():
        return {"features": [], "by_approval": {}, "by_root": {}}
    payload = json.loads(SCHEME_GEOJSON_PATH.read_text(encoding="utf-8"))
    features = []
    by_approval: dict[str, list[dict[str, Any]]] = {}
    by_root: dict[str, list[dict[str, Any]]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        centroid = geometry_centroid_area(feature.get("geometry", {}))
        if not centroid:
            continue
        lat, lon, area = centroid
        item = {
            "feature": feature,
            "properties": props,
            "centroid": (lat, lon),
            "area": area,
            "name_norm": normalize_match_text(props.get("name", "")),
            "holder_norm": normalize_match_text(props.get("holder", "")),
            "kind": props.get("kind", ""),
            "approval": clean_text(props.get("scheme_no", "")).upper(),
        }
        features.append(item)
        if item["approval"]:
            by_approval.setdefault(item["approval"], []).append(item)
            root = approval_root(item["approval"])
            if root:
                by_root.setdefault(root, []).append(item)
    return {"features": features, "by_approval": by_approval, "by_root": by_root}


def parse_st44_rows() -> list[dict[str, Any]]:
    if not ST44_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        wb = openpyxl.load_workbook(ST44_PATH, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: could not read ST44 active scheme workbook: {exc}")
        return []

    if "ActiveInSitu" in wb.sheetnames:
        ws = wb["ActiveInSitu"]
        for row in ws.iter_rows(values_only=True):
            values = [clean_text(value) for value in row]
            if len(values) < 11:
                continue
            approvals = approval_numbers(values[2])
            if not approvals:
                continue
            rows.append(
                {
                    "kind": "in_situ_scheme",
                    "approvals": approvals,
                    "approval": approvals[0],
                    "operator": values[3],
                    "scheme_name": values[6],
                    "area": values[7],
                    "deposit": values[8],
                    "location": values[9],
                    "recovery": values[10],
                }
            )
    if "ActiveMinable" in wb.sheetnames:
        ws = wb["ActiveMinable"]
        for row in ws.iter_rows(values_only=True):
            values = [clean_text(value) for value in row]
            if len(values) < 9:
                continue
            approvals = approval_numbers(values[1])
            if not approvals or not values[2]:
                continue
            rows.append(
                {
                    "kind": "mineable_scheme",
                    "approvals": approvals,
                    "approval": approvals[0],
                    "operator": values[2],
                    "scheme_name": values[6],
                    "area": values[6],
                    "deposit": values[5],
                    "location": values[7],
                    "recovery": values[8],
                }
            )
    return rows


def st44_location_to_centroid(location: str) -> tuple[float, float] | None:
    text = clean_text(location).upper().replace("M", "")
    match = re.search(r"\b(\d{1,2})-(\d{2,3})-(\d{1,2})-?W([456])\b", text)
    if match:
        section, township, range_, meridian = match.groups()
        return approximate_dls_centroid(f"08-{int(section):02d}-{int(township):03d}-{int(range_):02d}W{meridian}")
    match = re.search(r"\b(\d{2,3})(?:/\d{2,3})*-(\d{1,2})(?:/\d{1,2})*W([456])\b", text)
    if match:
        township, range_, meridian = match.groups()
        return approximate_dls_centroid(f"08-18-{int(township):03d}-{int(range_):02d}W{meridian}")
    return None


def load_st102_facilities() -> list[dict[str, Any]]:
    if not ST102_SHP_PATH.exists():
        return []
    try:
        with _zipfile.ZipFile(ST102_SHP_PATH) as zf:
            rows = read_dbf_bytes(zf.read("ST102_Facility_GCS_NAD83.dbf"))
            points = read_point_shapes(zf.read("ST102_Facility_GCS_NAD83.shp"))
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: could not read ST102 facility shapefile: {exc}")
        return []
    facilities = []
    for row, point in zip(rows, points):
        if not point:
            continue
        lat, lon = point
        text = " ".join(row.get(key, "") for key in ("FAC_ID", "FAC_NAME", "OPERATOR", "LICENSEE", "FAC_SUB_TY", "EDCT_DESCR"))
        facilities.append({**row, "latitude": lat, "longitude": lon, "text_norm": normalize_match_text(text)})
    return facilities


OIL_SANDS_ASSET_LOCATION_RULES: dict[tuple[str, str, str], dict[str, Any]] = {
    ("in_situ", "athabasca", "hangingstone"): {"approvals": ["11888L"]},
    ("in_situ", "athabasca", "leismer"): {"approvals": ["10935II"]},
    ("in_situ", "baytex", "cadotte"): {"approvals": ["11778D"], "scheme_terms": ["CADOTTE"]},
    ("in_situ", "baytex", "seal_peace_river"): {
        "approvals": ["11320G", "11936A", "11437A", "11327A", "11915"],
        "scheme_terms": ["SEAL", "PEACE RIVER"],
        "operator_terms": ["BAYTEX"],
    },
    ("in_situ", "cnooc_nexen", "long_lake"): {"approvals": ["9485BBBB"]},
    ("in_situ", "cnrl", "brintnell"): {"approvals": ["9466W", "10147G", "10423GG"]},
    ("in_situ", "cnrl", "jackfish"): {"approvals": ["10097AAAA"]},
    ("in_situ", "cnrl", "kirby"): {"approvals": ["11475QQQ"]},
    ("in_situ", "cnrl", "primrose_wolf_lake"): {"approvals": ["9140QQQ"]},
    ("in_situ", "cenovus", "christina_lake"): {"approvals": ["8591LLLL"]},
    ("in_situ", "cenovus", "foster_creek"): {"approvals": ["8623RRRRR", "8623PPPPP"]},
    ("in_situ", "cenovus", "narrows_lake"): {"approvals": ["11798M"], "st44_terms": ["NARROWS LAKE"]},
    ("in_situ", "cenovus", "sunrise"): {"approvals": ["10419JJJ"]},
    ("in_situ", "connacher", "great_divide"): {"approvals": ["10587GG"]},
    ("in_situ", "conocophillips", "surmont"): {"approvals": ["9426III"]},
    ("in_situ", "greenfire", "hangingstone_demo"): {"approvals": ["8788R"]},
    ("in_situ", "greenfire", "hangingstone_exp"): {"approvals": ["11910S"]},
    ("in_situ", "harvest", "blackgold"): {"approvals": ["11387K"]},
    ("in_situ", "imperial_oil", "cold_lake"): {"approvals": ["8558GGG"]},
    ("in_situ", "meg_energy", "christina_lake"): {"approvals": ["10773YYY"]},
    ("in_situ", "petrochina", "mackay_river_pc"): {"approvals": ["11715X"]},
    ("in_situ", "strathcona", "lindbergh"): {"approvals": ["6410NN", "6410MM"]},
    ("in_situ", "strathcona", "orion"): {"approvals": ["10103JJ", "10103II"]},
    ("in_situ", "strathcona", "tucker"): {"approvals": ["9835LL"]},
    ("in_situ", "suncor", "firebag"): {"approvals": ["8870JJJJJ"]},
    ("in_situ", "suncor", "mackay_river"): {"approvals": ["8668OOO"]},
    ("mined", "cnrl", "cnrl_horizon"): {"approvals": ["9752Q", "9752P"], "scheme_terms": ["HORIZON"]},
    ("mined", "cnrl", "jackpine_mine"): {"approvals": ["9756M"], "scheme_terms": ["JACKPINE"]},
    ("mined", "cnrl", "muskeg_river_mine"): {"approvals": ["8512Q"], "scheme_terms": ["MUSKEG"]},
    ("mined", "cnrl", "shell_jackpine_mine"): {"approvals": ["9756M"], "scheme_terms": ["JACKPINE"]},
    ("mined", "imperial_oil", "kearl_mine"): {"approvals": ["10829S", "10829R"], "scheme_terms": ["KEARL"]},
    ("mined", "suncor", "fort_hills_mine"): {"approvals": ["9241M", "9241L"], "scheme_terms": ["FORT HILLS"]},
    ("mined", "suncor", "suncor_osg"): {"approvals": ["8535V"], "scheme_terms": ["BASE MINE", "MILLENNIUM", "NORTH STEEPBANK"]},
    ("mined", "syncrude_jv", "syncrude_aurora"): {"approvals": ["10781Q"], "scheme_terms": ["AURORA"]},
    ("mined", "syncrude_jv", "syncrude_mildred_lake"): {"approvals": ["8573U"], "scheme_terms": ["MILDRED"]},
}


ROLLUP_ASSET_NAME_TOKENS = ("OTHER", "(ASSETS)")


def oil_sands_rule(production_system: str, company: str, display_name: str) -> dict[str, Any] | None:
    return OIL_SANDS_ASSET_LOCATION_RULES.get((slug(production_system), slug(company), slug(display_name)))


def non_specific_oil_sands_bucket(display_name: str) -> bool:
    name = clean_text(display_name).upper()
    return any(token in name for token in ROLLUP_ASSET_NAME_TOKENS)


def score_scheme_feature(
    feature: dict[str, Any],
    production_system: str,
    company: str,
    display_name: str,
    rule: dict[str, Any] | None,
) -> float:
    props = feature.get("properties", {})
    name_norm = feature.get("name_norm", "")
    holder_norm = feature.get("holder_norm", "")
    target_name = normalize_match_text(display_name)
    target_company = normalize_match_text(company)
    score = 0.0
    if slug(production_system) == "mined" and feature.get("kind") == "mineable_scheme":
        score += 8
    if slug(production_system) == "in_situ" and feature.get("kind") == "in_situ_scheme":
        score += 8
    if target_company and target_company.split()[0] in holder_norm:
        score += 5
    if target_name and target_name in name_norm:
        score += 10
    for term in (rule or {}).get("scheme_terms", []):
        term_norm = normalize_match_text(term)
        if term_norm and term_norm in name_norm:
            score += 12
    if props.get("status") == "AC":
        score += 1
    return score


def resolve_scheme_location(
    production_system: str,
    company: str,
    display_name: str,
    scheme_index: dict[str, Any],
    st44_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    rule = oil_sands_rule(production_system, company, display_name)
    candidates: list[dict[str, Any]] = []
    for approval in (rule or {}).get("approvals", []):
        approval_key = clean_text(approval).upper()
        candidates.extend(scheme_index["by_approval"].get(approval_key, []))
        root = approval_root(approval_key)
        if root:
            candidates.extend(scheme_index["by_root"].get(root, []))
    if not candidates:
        target_name = normalize_match_text(display_name.replace("&", " and "))
        target_company = normalize_match_text(company)
        for feature in scheme_index["features"]:
            if slug(production_system) == "mined" and feature.get("kind") != "mineable_scheme":
                continue
            if slug(production_system) == "in_situ" and feature.get("kind") != "in_situ_scheme":
                continue
            text = f"{feature.get('name_norm', '')} {feature.get('holder_norm', '')}"
            if target_name and target_name in text:
                candidates.append(feature)
            elif target_company and target_company.split()[0] in text and any(token in text for token in target_name.split() if len(token) > 3):
                candidates.append(feature)
    if candidates:
        deduped = {id(item): item for item in candidates}.values()
        scored = sorted(
            deduped,
            key=lambda item: score_scheme_feature(item, production_system, company, display_name, rule),
            reverse=True,
        )
        top_score = score_scheme_feature(scored[0], production_system, company, display_name, rule)
        selected = [
            item
            for item in scored
            if score_scheme_feature(item, production_system, company, display_name, rule) >= max(1.0, top_score - 3.0)
        ]
        coords = combined_centroid(selected)
        if coords:
            approvals = sorted({item.get("approval", "") for item in selected if item.get("approval")})
            names = sorted({item.get("properties", {}).get("name", "") for item in selected if item.get("properties", {}).get("name")})
            return {
                "latitude": coords[0],
                "longitude": coords[1],
                "method": "aer_scheme_approval_centroid",
                "geometry_kind": "scheme_polygon",
                "geometry_source": "AER Scheme Approval Spatial Data",
                "geometry_features": [item["feature"] for item in selected if item.get("feature")],
                "notes": f"Location from AER Scheme Approval Spatial Data centroid; matched scheme(s): {', '.join(names[:4])}; approval(s): {', '.join(approvals[:5])}.",
            }
    if rule:
        rule_terms = [normalize_match_text(term) for term in rule.get("st44_terms", []) + rule.get("scheme_terms", [])]
        for item in st44_rows:
            approvals = set(item.get("approvals", []))
            if approvals.intersection(set(rule.get("approvals", []))):
                coords = st44_location_to_centroid(item.get("location", ""))
            elif rule_terms and any(term and term in normalize_match_text(item.get("scheme_name", "")) for term in rule_terms):
                coords = st44_location_to_centroid(item.get("location", ""))
            else:
                coords = None
            if coords:
                return {
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "method": "aer_st44_dls_centroid",
                    "geometry_kind": "dls_centroid",
                    "geometry_source": "AER ST44 Active Oil Sands Schemes",
                    "notes": f"Location from AER ST44 township/DLS location {item.get('location', '')}; approval {item.get('approval', '')}.",
                }
    return None


def st102_term_rule(display_name: str) -> list[str]:
    name = normalize_match_text(display_name)
    explicit = {
        "LONG LAKE UPGRADER": ["LONG LAKE PROJECT UPGRADER", "LONG LAKE"],
        "HORIZON UPGRADER": ["CNRL HORIZON OIL SANDS PROJECT", "HORIZON"],
        "SCOTFORD UPGRADER": ["SHELL SCOTFORD UPGRADER", "SCOTFORD"],
        "SUNCOR BASE PLANT UPGRADER": ["SUNCOR ENERGY OSG", "SUNCOR"],
        "SYNCRUDE MILDRED LAKE UPGRADER": ["SYNCRUDE MILDRED LAKE", "MILDRED"],
        "CNRL HORIZON": ["CNRL HORIZON OIL SANDS PROJECT", "HORIZON"],
        "KEARL MINE": ["KEARL MINE"],
        "FORT HILLS MINE": ["FORT HILLS MINE"],
        "MUSKEG RIVER MINE": ["MUSKEG RIVER MINE"],
        "JACKPINE MINE": ["JACKPINE MINE"],
        "SHELL JACKPINE MINE": ["JACKPINE MINE"],
        "SYNCRUDE AURORA": ["SYNCRUDE AURORA"],
        "SYNCRUDE MILDRED LAKE": ["SYNCRUDE MILDRED LAKE"],
    }
    for key, terms in explicit.items():
        if key in name:
            return terms
    return [name]


def resolve_st102_facility_location(
    production_system: str,
    company: str,
    display_name: str,
    st102_facilities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not st102_facilities:
        return None
    terms = [normalize_match_text(term) for term in st102_term_rule(display_name) if normalize_match_text(term)]
    company_norm = normalize_match_text(company)
    best: tuple[float, dict[str, Any]] | None = None
    for facility in st102_facilities:
        text = facility["text_norm"]
        score = 0.0
        for term in terms:
            if term and term in text:
                score += 20 + len(term.split())
        if not score:
            continue
        if company_norm and company_norm.split()[0] in text:
            score += 5
        status = normalize_match_text(facility.get("FAC_STATUS", ""))
        subtype = normalize_match_text(facility.get("FAC_SUB_TY", ""))
        if status in {"ACTIVE", "NEW", "RECERTIFIED"}:
            score += 4
        if slug(production_system) in {"synthetic", "mined"} and "OIL SANDS PROCESSING PLANT" in subtype:
            score += 5
        if slug(production_system) == "in_situ" and "IN SITU OIL SANDS BATTERY" in subtype:
            score += 4
        if best is None or score > best[0]:
            best = (score, facility)
    if not best:
        return None
    facility = best[1]
    return {
        "latitude": facility["latitude"],
        "longitude": facility["longitude"],
        "method": "aer_st102_facility_point",
        "geometry_kind": "facility_point",
        "geometry_source": "AER ST102 Facility List Shapefile",
        "notes": (
            "Location from AER ST102 Facility List Shapefile point: "
            f"{facility.get('FAC_ID', '')} {facility.get('FAC_NAME', '')}; "
            f"{facility.get('FAC_SUB_TY', '')}; status {facility.get('FAC_STATUS', '')}."
        ),
    }


def build_oil_sands_location_index() -> dict[str, Any]:
    scheme_index = load_scheme_feature_index()
    st44_rows = parse_st44_rows()
    st102_facilities = load_st102_facilities()
    log(
        "  AER location index: "
        f"{len(scheme_index['features']):,} scheme polygons, "
        f"{len(st44_rows):,} ST44 rows, "
        f"{len(st102_facilities):,} ST102 facility points."
    )
    return {"scheme_index": scheme_index, "st44_rows": st44_rows, "st102_facilities": st102_facilities}


def resolve_oil_sands_asset_location(
    production_system: str,
    company: str,
    display_name: str,
    location_index: dict[str, Any],
) -> dict[str, Any] | None:
    if non_specific_oil_sands_bucket(display_name):
        return {"is_rollup": True, "asset_kind": "asset_bucket", "notes": "Non-specific workbook bucket; retained in data but excluded from map markers."}
    if slug(production_system) == "synthetic":
        return resolve_st102_facility_location(production_system, company, display_name, location_index["st102_facilities"])
    scheme_location = resolve_scheme_location(
        production_system,
        company,
        display_name,
        location_index["scheme_index"],
        location_index["st44_rows"],
    )
    if scheme_location:
        return scheme_location
    return resolve_st102_facility_location(production_system, company, display_name, location_index["st102_facilities"])


def oil_sands_facility_geojson(st102_facilities: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_status = {"ACTIVE", "NEW", "RECERTIFIED"}
    allowed_subtypes = {"IN SITU OIL SANDS BATTERY", "OIL SANDS PROCESSING PLANT", "SULPHUR REPORTING AT OIL SANDS"}
    features = []
    for facility in st102_facilities:
        status = normalize_match_text(facility.get("FAC_STATUS", ""))
        subtype = normalize_match_text(facility.get("FAC_SUB_TY", ""))
        if status not in allowed_status or subtype not in allowed_subtypes:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [facility["longitude"], facility["latitude"]]},
                "properties": {
                    "facility_id": facility.get("FAC_ID", ""),
                    "name": facility.get("FAC_NAME", ""),
                    "operator": facility.get("OPERATOR", ""),
                    "subtype": facility.get("FAC_SUB_TY", ""),
                    "status": facility.get("FAC_STATUS", ""),
                    "source": "AER ST102 Facility List Shapefile",
                },
            }
        )
    return {"type": "FeatureCollection", "name": "AER ST102 oil sands facility points", "features": features}


def is_oil_sands_reporting_subtype(desc: str) -> bool:
    text = clean_text(desc).upper()
    return any(token in text for token in ("OIL SANDS", "IN-SITU", "IN SITU", "SULPHUR REPORTING AT OIL SANDS"))


def read_well_facility_links(target_wells: set[str]) -> dict[str, dict[str, str]]:
    path = PETRINEX_AB_INFRA_DIR / "well_to_facility_link_ab.zip"
    if not path.exists() or not target_wells:
        return {}
    links: dict[str, dict[str, str]] = {}
    log(f"  Parsing Petrinex well-to-facility links for {len(target_wells):,} target wells")
    reader = open_nested_petrinex_csv(path)
    for row in reader:
        well_id = row.get("WellID", "")
        if well_id not in target_wells:
            continue
        dls = format_dls(
            row.get("WellLegalSubdivision"),
            row.get("WellSection"),
            row.get("WellTownship"),
            row.get("WellRange"),
            row.get("WellMeridian"),
        )
        if not dls:
            continue
        links[well_id] = {
            "dls": dls,
            "well_name": clean_text(row.get("WellName")),
            "well_status_fluid": clean_text(row.get("WellStatusFluid")),
            "linked_facility_id": clean_text(row.get("LinkedFacilityID")),
            "linked_start_date": clean_text(row.get("LinkedStartDate")),
        }
        if len(links) == len(target_wells):
            break
    log(f"  Petrinex well links matched {len(links):,} wells")
    return links


def append_petrinex_ab_conventional(
    assets: dict[str, Asset],
    records: list[dict[str, Any]],
    add_asset: Any,
    add_record: Any,
) -> None:
    del assets, records  # callbacks own insertion; keep signature explicit for future ETL split.
    volume_paths = sorted(PETRINEX_AB_VOL_DIR.glob("Vol_????-??-AB.zip"))
    if not volume_paths:
        log("  Petrinex AB volumetric cache is empty - skipping conventional location layer.")
        return

    raw_rows: list[dict[str, Any]] = []
    target_wells: set[str] = set()
    total_rows = 0
    skipped_oil_sands = 0
    # Pentanes plus (C5-SP PROC+FRAC) rows — collected in same pass to avoid re-reading zips
    c5_raw_rows: list[dict[str, Any]] = []
    # Condensate (COND PROD, non-oil-sands) rows — collected in same pass
    cond_raw_rows: list[dict[str, Any]] = []
    # NGL (C3-MX, C3-SP, C4-MX, C4-SP at PROC) — shared asset per facility, 4 streams
    ngl_raw: dict[str, list[dict[str, Any]]] = {"C3-MX": [], "C3-SP": [], "C4-MX": [], "C4-SP": []}
    for path in volume_paths:
        period_match = re.search(r"Vol_(\d{4}-\d{2})-AB\.zip$", path.name)
        if not period_match:
            continue
        period = period_match.group(1)
        year_month = parse_period(period)
        if not year_month:
            continue
        year, month = year_month
        date_value = dt.date(year, month, 1)
        if month_end(date_value) < CUTOFF:
            continue
        log(f"  Parsing Petrinex AB conventional volume {period}")
        reader = open_nested_petrinex_csv(path)
        for row in reader:
            total_rows += 1
            province = row.get("ReportingFacilityProvinceState")
            activity = row.get("ActivityID")
            product = row.get("ProductID")

            # ── Conventional crude (OIL/PROD) ──────────────────────────────
            if activity == "PROD" and product == "OIL" and province == "AB":
                if is_oil_sands_reporting_subtype(row.get("ReportingFacilitySubTypeDesc", "")):
                    skipped_oil_sands += 1
                    continue
                volume_m3 = as_float(row.get("Volume"))
                if volume_m3 is None or volume_m3 <= 0:
                    continue
                facility_dls = format_dls(
                    row.get("FacilityLegalSubdivision"),
                    row.get("FacilitySection"),
                    row.get("FacilityTownship"),
                    row.get("FacilityRange"),
                    row.get("FacilityMeridian"),
                )
                if not facility_dls:
                    continue
                well_id = clean_text(row.get("FromToID")) if row.get("FromToIDType") == "WI" else ""
                if well_id.startswith("ABWI"):
                    target_wells.add(well_id)
                raw_rows.append(
                    {
                        "date": date_value,
                        "period": period,
                        "volume_m3": volume_m3,
                        "well_id": well_id,
                        "facility_dls": facility_dls,
                        "facility_id": clean_text(row.get("ReportingFacilityID")),
                        "facility_name": clean_text(row.get("ReportingFacilityName")),
                        "facility_subtype": clean_text(row.get("ReportingFacilitySubTypeDesc")),
                        "operator": clean_text(row.get("OperatorName")) or "Unknown operator",
                    }
                )

            # ── Pentanes plus (C5-SP PROC or FRAC) ─────────────────────────
            elif product == "C5-SP" and activity in {"PROC", "FRAC"} and province == "AB":
                volume_m3 = as_float(row.get("Volume"))
                if volume_m3 is None or volume_m3 <= 0:
                    continue
                facility_dls = format_dls(
                    row.get("FacilityLegalSubdivision"),
                    row.get("FacilitySection"),
                    row.get("FacilityTownship"),
                    row.get("FacilityRange"),
                    row.get("FacilityMeridian"),
                )
                if not facility_dls:
                    continue
                c5_raw_rows.append(
                    {
                        "date": date_value,
                        "period": period,
                        "volume_m3": volume_m3,
                        "facility_dls": facility_dls,
                        "facility_id": clean_text(row.get("ReportingFacilityID")),
                        "facility_name": clean_text(row.get("ReportingFacilityName")),
                        "operator": clean_text(row.get("OperatorName")) or "Unknown operator",
                    }
                )

            # ── Condensate (COND PROD, non-oil-sands) ───────────────────────
            elif product == "COND" and activity == "PROD" and province == "AB":
                if is_oil_sands_reporting_subtype(row.get("ReportingFacilitySubTypeDesc", "")):
                    continue
                volume_m3 = as_float(row.get("Volume"))
                if volume_m3 is None or volume_m3 <= 0:
                    continue
                facility_dls = format_dls(
                    row.get("FacilityLegalSubdivision"),
                    row.get("FacilitySection"),
                    row.get("FacilityTownship"),
                    row.get("FacilityRange"),
                    row.get("FacilityMeridian"),
                )
                if not facility_dls:
                    continue
                well_id = clean_text(row.get("FromToID")) if row.get("FromToIDType") == "WI" else ""
                cond_raw_rows.append(
                    {
                        "date": date_value,
                        "period": period,
                        "volume_m3": volume_m3,
                        "well_id": well_id,
                        "facility_dls": facility_dls,
                        "facility_id": clean_text(row.get("ReportingFacilityID")),
                        "facility_name": clean_text(row.get("ReportingFacilityName")),
                        "operator": clean_text(row.get("OperatorName")) or "Unknown operator",
                    }
                )

            # ── NGL — C3/C4 mix and spec at PROC ────────────────────────────
            elif product in {"C3-MX", "C3-SP", "C4-MX", "C4-SP"} and activity == "PROC" and province == "AB":
                volume_m3 = as_float(row.get("Volume"))
                if volume_m3 is None or volume_m3 <= 0:
                    continue
                facility_dls = format_dls(
                    row.get("FacilityLegalSubdivision"),
                    row.get("FacilitySection"),
                    row.get("FacilityTownship"),
                    row.get("FacilityRange"),
                    row.get("FacilityMeridian"),
                )
                if not facility_dls:
                    continue
                ngl_raw[product].append(
                    {
                        "date": date_value,
                        "period": period,
                        "volume_m3": volume_m3,
                        "facility_dls": facility_dls,
                        "facility_id": clean_text(row.get("ReportingFacilityID")),
                        "facility_name": clean_text(row.get("ReportingFacilityName")),
                        "operator": clean_text(row.get("OperatorName")) or "Unknown operator",
                    }
                )

    if not raw_rows:
        log("  Petrinex AB conventional layer found no positive OIL/PROD rows after oil-sands exclusion.")
        return

    well_links = read_well_facility_links(target_wells)
    sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in raw_rows:
        link = well_links.get(item["well_id"], {})
        dls = link.get("dls") or item["facility_dls"]
        key = (month_end(item["date"]).isoformat(), item["operator"], dls)
        site = sites.setdefault(
            key,
            {
                "date": item["date"],
                "operator": item["operator"],
                "dls": dls,
                "province": "Alberta",
                "volume_m3": 0.0,
                "wells": set(),
                "facilities": set(),
                "facility_names": set(),
                "location_basis": "well_dls_current_link" if link else "reporting_facility_dls",
            },
        )
        site["volume_m3"] += item["volume_m3"]
        if item["well_id"]:
            site["wells"].add(item["well_id"])
        if item["facility_id"]:
            site["facilities"].add(item["facility_id"])
        if item["facility_name"]:
            site["facility_names"].add(item["facility_name"])
        if not link and site["location_basis"] != "well_dls_current_link":
            site["location_basis"] = "reporting_facility_dls"

    site_items: list[dict[str, Any]] = []
    for site in sites.values():
        date_value = site["date"]
        days = calendar.monthrange(date_value.year, date_value.month)[1]
        site["volume_bbl_d"] = site["volume_m3"] * M3_TO_BBL / days
        site_items.append(site)
    location_cache = resolve_dls_locations(site_items, official_limit=250)

    added = 0
    for site in site_items:
        cache_row = location_cache.get((site["province"], site["dls"]))
        if not cache_row:
            continue
        lat = as_float(cache_row.get("latitude"))
        lon = as_float(cache_row.get("longitude"))
        if lat is None or lon is None:
            continue
        facility_count = len(site["facilities"])
        well_count = len(site["wells"])
        display = f"{site['dls']} - {site['operator']}"
        note_bits = [
            "Petrinex AB OIL/PROD rows aggregated by operator and DLS site.",
            f"Location basis: {site['location_basis']}; coordinate method: {cache_row.get('method', '')}.",
        ]
        if facility_count:
            note_bits.append(f"{facility_count} reporting facilit{'y' if facility_count == 1 else 'ies'}.")
        if well_count:
            note_bits.append(f"{well_count} well event{'s' if well_count != 1 else ''}.")
        asset_id = add_asset(
            display_name=display,
            source_id="petrinex_ab_conventional_vol",
            production_system="conventional",
            company=site["operator"],
            province=site["province"],
            asset_kind="dls_site",
            latitude=lat,
            longitude=lon,
            coordinate_method=clean_text(cache_row.get("method")),
            location_basis=site["location_basis"],
            geometry_kind="dls_centroid",
            geometry_source="Petrinex DLS / AGS ATS lookup",
            notes=" ".join(note_bits),
        )
        add_record(
            site["date"],
            asset_id,
            "Conventional crude oil",
            site["volume_bbl_d"],
            f"Petrinex AB Vol {month_period(site['date'])}",
            site["dls"],
            "petrinex_ab_conventional_vol",
            scenario="actual",
        )
        added += 1
    log(
        "  Petrinex AB conventional: "
        f"{added:,} DLS/operator records from {len(raw_rows):,} OIL/PROD rows; "
        f"excluded {skipped_oil_sands:,} oil-sands rows."
    )

    # ── Pentanes plus processing ────────────────────────────────────────────
    if not c5_raw_rows:
        log("  Petrinex AB pentanes plus: no C5-SP PROC/FRAC rows found.")
        return

    c5_sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in c5_raw_rows:
        key = (month_end(item["date"]).isoformat(), item["operator"], item["facility_dls"])
        site = c5_sites.setdefault(
            key,
            {
                "date": item["date"],
                "operator": item["operator"],
                "dls": item["facility_dls"],
                "province": "Alberta",
                "volume_m3": 0.0,
                "facilities": set(),
                "facility_names": set(),
            },
        )
        site["volume_m3"] += item["volume_m3"]
        if item["facility_id"]:
            site["facilities"].add(item["facility_id"])
        if item["facility_name"]:
            site["facility_names"].add(item["facility_name"])

    c5_items: list[dict[str, Any]] = []
    for site in c5_sites.values():
        date_value = site["date"]
        days = calendar.monthrange(date_value.year, date_value.month)[1]
        site["volume_bbl_d"] = site["volume_m3"] * M3_TO_BBL / days
        c5_items.append(site)

    c5_location_cache = resolve_dls_locations(c5_items, official_limit=250)
    c5_added = 0
    for site in c5_items:
        cache_row = c5_location_cache.get((site["province"], site["dls"]))
        if not cache_row:
            continue
        lat = as_float(cache_row.get("latitude"))
        lon = as_float(cache_row.get("longitude"))
        if lat is None or lon is None:
            continue
        facility_count = len(site["facilities"])
        display = f"{site['dls']} - {site['operator']}"
        note_bits = [
            "Petrinex AB C5-SP PROC+FRAC rows aggregated by operator and DLS site.",
            f"Location basis: reporting_facility_dls; coordinate method: {cache_row.get('method', '')}.",
        ]
        if facility_count:
            note_bits.append(f"{facility_count} reporting facilit{'y' if facility_count == 1 else 'ies'}.")
        asset_id = add_asset(
            display_name=display,
            source_id="petrinex_ab_pentanes_plus_vol",
            production_system="pentanes_plus",
            company=site["operator"],
            province=site["province"],
            asset_kind="dls_site",
            latitude=lat,
            longitude=lon,
            coordinate_method=clean_text(cache_row.get("method")),
            location_basis="reporting_facility_dls",
            geometry_kind="dls_centroid",
            geometry_source="Petrinex DLS / AGS ATS lookup",
            notes=" ".join(note_bits),
        )
        add_record(
            site["date"],
            asset_id,
            "Pentanes plus total",
            site["volume_bbl_d"],
            f"Petrinex AB Vol {month_period(site['date'])}",
            site["dls"],
            "petrinex_ab_pentanes_plus_vol",
            scenario="actual",
        )
        c5_added += 1
    log(
        "  Petrinex AB pentanes plus: "
        f"{c5_added:,} facility records from {len(c5_raw_rows):,} C5-SP PROC/FRAC rows."
    )

    # ── Condensate processing ───────────────────────────────────────────────
    if not cond_raw_rows:
        log("  Petrinex AB condensate: no COND PROD rows found.")
        return

    cond_sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in cond_raw_rows:
        link = well_links.get(item["well_id"], {}) if item.get("well_id") else {}
        dls = link.get("dls") or item["facility_dls"]
        key = (month_end(item["date"]).isoformat(), item["operator"], dls)
        site = cond_sites.setdefault(
            key,
            {
                "date": item["date"],
                "operator": item["operator"],
                "dls": dls,
                "province": "Alberta",
                "volume_m3": 0.0,
                "facilities": set(),
                "facility_names": set(),
                "location_basis": "well_dls_current_link" if link else "reporting_facility_dls",
            },
        )
        site["volume_m3"] += item["volume_m3"]
        if item["facility_id"]:
            site["facilities"].add(item["facility_id"])
        if item["facility_name"]:
            site["facility_names"].add(item["facility_name"])

    cond_items: list[dict[str, Any]] = []
    for site in cond_sites.values():
        date_value = site["date"]
        days = calendar.monthrange(date_value.year, date_value.month)[1]
        site["volume_bbl_d"] = site["volume_m3"] * M3_TO_BBL / days
        cond_items.append(site)

    cond_location_cache = resolve_dls_locations(cond_items, official_limit=250)
    cond_added = 0
    for site in cond_items:
        cache_row = cond_location_cache.get((site["province"], site["dls"]))
        if not cache_row:
            continue
        lat = as_float(cache_row.get("latitude"))
        lon = as_float(cache_row.get("longitude"))
        if lat is None or lon is None:
            continue
        facility_count = len(site["facilities"])
        display = f"{site['dls']} - {site['operator']}"
        note_bits = [
            "Petrinex AB COND PROD rows aggregated by operator and DLS site.",
            f"Location basis: {site['location_basis']}; coordinate method: {cache_row.get('method', '')}.",
        ]
        if facility_count:
            note_bits.append(f"{facility_count} reporting facilit{'y' if facility_count == 1 else 'ies'}.")
        asset_id = add_asset(
            display_name=display,
            source_id="petrinex_ab_condensate_vol",
            production_system="condensate",
            company=site["operator"],
            province=site["province"],
            asset_kind="dls_site",
            latitude=lat,
            longitude=lon,
            coordinate_method=clean_text(cache_row.get("method")),
            location_basis=site["location_basis"],
            geometry_kind="dls_centroid",
            geometry_source="Petrinex DLS / AGS ATS lookup",
            notes=" ".join(note_bits),
        )
        add_record(
            site["date"],
            asset_id,
            "Condensate production",
            site["volume_bbl_d"],
            f"Petrinex AB Vol {month_period(site['date'])}",
            site["dls"],
            "petrinex_ab_condensate_vol",
            scenario="actual",
        )
        cond_added += 1
    log(
        "  Petrinex AB condensate: "
        f"{cond_added:,} facility records from {len(cond_raw_rows):,} COND PROD rows."
    )

    # ── NGL processing — facility-typed assets, four separate streams ────────
    NGL_STREAMS = {
        "C3-MX": "Propane mix",
        "C3-SP": "Propane spec",
        "C4-MX": "Butane mix",
        "C4-SP": "Butane spec",
    }
    total_ngl_rows = sum(len(v) for v in ngl_raw.values())
    if not total_ngl_rows:
        log("  Petrinex AB NGL: no C3/C4 PROC rows found.")
    else:
        # ── Classify each (operator, DLS) facility across ALL months ────────
        # gas_plant      = only MX products (raw extraction, ships mix elsewhere)
        # integrated_plant = both MX and SP (extracts + fractionates on-site)
        # spec_plant     = only SP products (standalone fractionator)
        facility_products: dict[tuple[str, str], set[str]] = {}
        for product, rows in ngl_raw.items():
            for item in rows:
                fkey = (item["operator"], item["facility_dls"])
                facility_products.setdefault(fkey, set()).add(product)

        def classify_ngl_facility(products: set[str]) -> str:
            has_mx = bool(products & {"C3-MX", "C4-MX"})
            has_sp = bool(products & {"C3-SP", "C4-SP"})
            if has_mx and has_sp:
                return "integrated_plant"
            if has_sp:
                return "spec_plant"
            return "gas_plant"

        facility_type_map: dict[tuple[str, str], str] = {
            fkey: classify_ngl_facility(prods)
            for fkey, prods in facility_products.items()
        }
        type_counts: dict[str, int] = {}
        for ft in facility_type_map.values():
            type_counts[ft] = type_counts.get(ft, 0) + 1
        log(f"  Petrinex AB NGL facility classification: {type_counts}")

        # ── Aggregate each product type per (date, operator, DLS) ───────────
        ngl_stream_sites: dict[str, dict[tuple, dict[str, Any]]] = {p: {} for p in NGL_STREAMS}
        all_ngl_items: list[dict[str, Any]] = []
        seen_dls: set[tuple[str, str]] = set()

        for product in NGL_STREAMS:
            for item in ngl_raw[product]:
                key = (month_end(item["date"]).isoformat(), item["operator"], item["facility_dls"])
                site = ngl_stream_sites[product].setdefault(
                    key,
                    {
                        "date": item["date"],
                        "operator": item["operator"],
                        "dls": item["facility_dls"],
                        "province": "Alberta",
                        "volume_m3": 0.0,
                        "facilities": set(),
                    },
                )
                site["volume_m3"] += item["volume_m3"]
                if item["facility_id"]:
                    site["facilities"].add(item["facility_id"])
                dls_key = ("Alberta", item["facility_dls"])
                if dls_key not in seen_dls:
                    seen_dls.add(dls_key)
                    all_ngl_items.append(site)

        for product in NGL_STREAMS:
            for site in ngl_stream_sites[product].values():
                date_value = site["date"]
                days = calendar.monthrange(date_value.year, date_value.month)[1]
                site["volume_bbl_d"] = site["volume_m3"] * M3_TO_BBL / days

        ngl_loc_cache = resolve_dls_locations(all_ngl_items, official_limit=250)

        for product, stream_name in NGL_STREAMS.items():
            stream_added = 0
            for site in ngl_stream_sites[product].values():
                cache_row = ngl_loc_cache.get((site["province"], site["dls"]))
                if not cache_row:
                    continue
                lat = as_float(cache_row.get("latitude"))
                lon = as_float(cache_row.get("longitude"))
                if lat is None or lon is None:
                    continue
                fac_type = facility_type_map.get((site["operator"], site["dls"]), "gas_plant")
                display = f"{site['dls']} - {site['operator']}"
                facility_count = len(site["facilities"])
                note_bits = [
                    f"Petrinex AB {product} PROC rows aggregated by operator and DLS site.",
                    f"Facility type: {fac_type.replace('_', ' ')}.",
                    f"Location basis: reporting_facility_dls; coordinate method: {cache_row.get('method', '')}.",
                ]
                if facility_count:
                    note_bits.append(f"{facility_count} reporting facilit{'y' if facility_count == 1 else 'ies'}.")
                asset_id = add_asset(
                    display_name=display,
                    source_id="petrinex_ab_ngl_vol",
                    production_system=fac_type,
                    company=site["operator"],
                    province=site["province"],
                    asset_kind="dls_site",
                    latitude=lat,
                    longitude=lon,
                    coordinate_method=clean_text(cache_row.get("method")),
                    location_basis="reporting_facility_dls",
                    geometry_kind="dls_centroid",
                    geometry_source="Petrinex DLS / AGS ATS lookup",
                    notes=" ".join(note_bits),
                )
                add_record(
                    site["date"],
                    asset_id,
                    stream_name,
                    site["volume_bbl_d"],
                    f"Petrinex AB Vol {month_period(site['date'])}",
                    site["dls"],
                    "petrinex_ab_ngl_vol",
                    scenario="actual",
                )
                stream_added += 1
            log(
                f"  Petrinex AB NGL {stream_name} ({product}): "
                f"{stream_added:,} records from {len(ngl_raw[product]):,} rows."
            )


def load_bcer_well_index() -> dict[str, dict[str, str]]:
    if not BCER_WELL_INDEX_CSV.exists():
        return {}
    wells: dict[str, dict[str, str]] = {}
    try:
        with BCER_WELL_INDEX_CSV.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                wa = clean_text(row.get("WA")).zfill(5)
                if not wa:
                    continue
                wells[wa] = row
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: could not read BCER well index: {exc}")
    return wells


def load_bcer_surface_locations() -> dict[str, dict[str, Any]]:
    if not BCER_WELL_SURFACE_GEOJSON.exists():
        return {}
    try:
        payload = json.loads(BCER_WELL_SURFACE_GEOJSON.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: could not read BCER well surface locations: {exc}")
        return {}
    locations: dict[str, dict[str, Any]] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        wa = clean_text(props.get("WELL_AUTHORITY_NUMBER")).zfill(5)
        coords = (feature.get("geometry") or {}).get("coordinates") or []
        if not wa or len(coords) < 2:
            continue
        lon = as_float(coords[0])
        lat = as_float(coords[1])
        if lat is None or lon is None:
            continue
        locations[wa] = {
            "latitude": lat,
            "longitude": lon,
            "well_name": clean_text(props.get("WELL_NAME")),
            "operator": clean_text(props.get("OPERATOR_ABBREVIATION")),
            "surface_location": clean_text(props.get("WELL_SURFACE_LOCATION")),
        }
    return locations


def bcer_production_members(zf: _zipfile.ZipFile) -> list[str]:
    names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
    preferred = [
        name
        for name in names
        if any(token in name.lower() for token in ("2007_to_2015", "2016_to_present"))
    ]
    return preferred or [name for name in names if Path(name).name.lower() == "zone_prd.csv"]


def iter_bcer_production_rows(zf: _zipfile.ZipFile, member: str) -> Any:
    with zf.open(member) as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        first = wrapper.readline()
        if "Wa_num" not in first:
            reader = csv.DictReader(wrapper)
        else:
            wrapper.seek(0)
            reader = csv.DictReader(wrapper)
        for row in reader:
            yield row


def append_bcer_well_production(add_asset: Any, add_record: Any) -> None:
    if not BCER_PRODUCTION_ZIP.exists():
        log("  BCER production cache is empty - skipping British Columbia conventional crude layer.")
        return

    well_index = load_bcer_well_index()
    surface_locations = load_bcer_surface_locations()
    sites: dict[tuple[str, str, str], dict[str, Any]] = {}
    raw_rows = 0
    used_oil_rows = 0
    used_cond_rows = 0
    missing_location_was: set[str] = set()
    stream_specs = {
        "Conventional crude oil": {
            "field": "Oil_prod_vol (m3)",
            "production_system": "conventional",
            "asset_note": "BCER zone production Oil_prod_vol (m3) aggregated by well authority number.",
            "source_note": "BCER Production Data - oil",
        },
        "Condensate production": {
            "field": "Cond_prod_vol (m3)",
            "production_system": "condensate",
            "asset_note": "BCER zone production Cond_prod_vol (m3) aggregated by well authority number.",
            "source_note": "BCER Production Data - condensate",
        },
    }
    try:
        with _zipfile.ZipFile(BCER_PRODUCTION_ZIP) as zf:
            members = bcer_production_members(zf)
            if not members:
                log("  BCER production ZIP contains no CSV production members.")
                return
            for member in members:
                log(f"  Parsing BCER production {member}")
                for row in iter_bcer_production_rows(zf, member):
                    raw_rows += 1
                    period = clean_text(row.get("Prod_period"))
                    if not re.fullmatch(r"\d{6}", period):
                        continue
                    year = int(period[:4])
                    month = int(period[4:6])
                    if not 1 <= month <= 12:
                        continue
                    date_value = dt.date(year, month, 1)
                    if month_end(date_value) < CUTOFF:
                        continue
                    wa = clean_text(row.get("Wa_num")).zfill(5)
                    if not wa:
                        continue
                    for stream, spec in stream_specs.items():
                        volume_m3 = as_float(row.get(spec["field"]))
                        if volume_m3 is None or volume_m3 <= 0:
                            continue
                        key = (month_end(date_value).isoformat(), wa, stream)
                        site = sites.setdefault(
                            key,
                            {
                                "date": date_value,
                                "wa": wa,
                                "stream": stream,
                                "volume_m3": 0.0,
                                "uwis": set(),
                                "formations": set(),
                                "areas": set(),
                            },
                        )
                        site["volume_m3"] += volume_m3
                        if row.get("UWI"):
                            site["uwis"].add(clean_text(row.get("UWI")))
                        if row.get("Formtn_code"):
                            site["formations"].add(clean_text(row.get("Formtn_code")))
                        if row.get("Area_code"):
                            site["areas"].add(clean_text(row.get("Area_code")))
                        if stream == "Conventional crude oil":
                            used_oil_rows += 1
                        else:
                            used_cond_rows += 1
    except Exception as exc:  # noqa: BLE001
        log(f"  warning: BCER production parse failed: {exc}")
        return

    added = 0
    asset_ids: dict[tuple[str, str], str] = {}
    for site in sites.values():
        wa = site["wa"]
        stream = site["stream"]
        spec = stream_specs[stream]
        surface = surface_locations.get(wa, {})
        index_row = well_index.get(wa, {})
        lat = as_float(surface.get("latitude"))
        lon = as_float(surface.get("longitude"))
        if lat is None or lon is None:
            missing_location_was.add(wa)
        well_name = clean_text(surface.get("well_name")) or clean_text(index_row.get("Well Name")) or f"BC well {wa}"
        operator = clean_text(surface.get("operator")) or clean_text(index_row.get("Oper")) or "Unknown operator"
        surface_location = clean_text(surface.get("surface_location")) or clean_text(index_row.get("Bottom Hole"))
        asset_key = (wa, spec["production_system"])
        if asset_key not in asset_ids:
            notes = [
                spec["asset_note"],
                "Location basis: well_surface_point; coordinate method: bcer_well_surface_point."
                if lat is not None and lon is not None
                else "Location basis: missing BCER well surface point.",
            ]
            if surface_location:
                notes.append(f"Surface location: {surface_location}.")
            asset_ids[asset_key] = add_asset(
                display_name=f"WA {wa} - {well_name}",
                source_id="bcer_well_production",
                production_system=spec["production_system"],
                company=operator,
                province="British Columbia",
                asset_kind="well",
                latitude=lat,
                longitude=lon,
                coordinate_method="bcer_well_surface_point" if lat is not None and lon is not None else "unmapped",
                location_basis="well_surface_point" if lat is not None and lon is not None else "missing_well_surface_point",
                geometry_kind="well_surface_point" if lat is not None and lon is not None else "",
                geometry_source="BCER Well Surface Hole Locations" if lat is not None and lon is not None else "",
                notes=" ".join(notes),
            )
        days = calendar.monthrange(site["date"].year, site["date"].month)[1]
        add_record(
            site["date"],
            asset_ids[asset_key],
            stream,
            site["volume_m3"] * M3_TO_BBL / days,
            spec["source_note"],
            wa,
            "bcer_well_production",
            scenario="actual",
        )
        added += 1

    log(
        "  BCER well liquids: "
        f"{added:,} well-month records from {used_oil_rows:,} positive oil rows "
        f"and {used_cond_rows:,} positive condensate rows "
        f"({raw_rows:,} raw rows); {len(missing_location_was):,} producing wells missing surface coordinates."
    )


def build_assets_and_records(workbook_path: Path) -> tuple[dict[str, Asset], list[dict[str, Any]], dict[str, Any]]:
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    log(f"Reading workbook: {workbook_path}")
    registry = load_registry()
    wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    assets: dict[str, Asset] = {}
    records: list[dict[str, Any]] = []

    latest_actual = read_workbook_latest_actual(workbook_path)
    oil_sands_locations = build_oil_sands_location_index()

    def add_asset(
        display_name: str,
        source_id: str,
        production_system: str,
        company: str = "",
        province: str = "Alberta",
        asset_kind: str = "asset",
        latitude: float | None = None,
        longitude: float | None = None,
        ownership_text: str = "",
        is_rollup: bool = False,
        notes: str = "",
        coordinate_method: str | None = None,
        location_basis: str = "",
        geometry_kind: str = "",
        geometry_source: str = "",
        geometry_features: list[dict[str, Any]] | None = None,
    ) -> str:
        key_source = source_id
        asset_id = f"{key_source}:{slug(production_system)}:{slug(company)}:{slug(display_name)}"
        reg = registry_lookup(registry, production_system, company, display_name)
        lat = latitude if latitude is not None else (as_float(reg.get("latitude")) if reg else None)
        lon = longitude if longitude is not None else (as_float(reg.get("longitude")) if reg else None)
        reg_province = reg.get("province", "").strip() if reg else ""
        reg_kind = reg.get("asset_kind", "").strip() if reg else ""
        reg_notes = reg.get("notes", "").strip() if reg else ""
        if reg_province:
            province = reg_province
        if reg_kind and not is_rollup and asset_kind == "asset":
            asset_kind = reg_kind
        if lat is None or lon is None:
            if asset_kind.startswith("province") or display_name in PROVINCE_COORDS:
                lat, lon = PROVINCE_COORDS.get(display_name, (lat, lon))
            elif province in PROVINCE_COORDS and (is_rollup or asset_kind in {"region", "company_rollup"}):
                lat, lon = PROVINCE_COORDS[province]
        final_notes = notes or reg_notes
        final_method = coordinate_method or (reg.get("coordinate_method", "").strip() if reg else "")
        final_method = final_method or infer_coordinate_method(lat, lon, final_notes, reg)
        final_confidence = coordinate_confidence(
            lat,
            lon,
            final_method,
            geometry_kind=geometry_kind,
            is_rollup=is_rollup,
            asset_kind=asset_kind,
        )
        if asset_id not in assets:
            assets[asset_id] = Asset(
                asset_id=asset_id,
                display_name=display_name,
                source_id=source_id,
                source_name=source_name(source_id),
                production_system=production_system,
                asset_kind=asset_kind,
                company=company,
                province=province,
                latitude=lat,
                longitude=lon,
                ownership_text=ownership_text,
                is_rollup=is_rollup,
                notes=final_notes,
                coordinate_method=final_method,
                location_confidence=final_confidence,
                location_basis=location_basis,
                geometry_kind=geometry_kind or ("point" if lat is not None and lon is not None else ""),
                geometry_source=geometry_source,
                geometry_features=list(geometry_features or []),
            )
        return asset_id

    def add_record(
        date_value: dt.date,
        asset_id: str,
        stream: str,
        volume_bbl_d: float | None,
        workbook_sheet: str,
        workbook_column: str,
        source_id: str,
        scenario: str | None = None,
    ) -> None:
        if volume_bbl_d is None:
            return
        date_value = month_end(date_value)
        if date_value < CUTOFF:
            return
        status = scenario or ("forecast" if date_value > latest_actual else "actual")
        records.append(
            {
                "date": date_value.isoformat(),
                "period": month_period(date_value),
                "asset_id": asset_id,
                "source_id": source_id,
                "source_name": source_name(source_id),
                "stream": stream,
                "volume_bbl_d": volume_bbl_d,
                "volume_kbbl_d": volume_bbl_d / 1000.0,
                "units": "bbl/d",
                "scenario": status,
                "workbook_sheet": workbook_sheet,
                "workbook_column": workbook_column,
            }
        )

    # AER ST53: in-situ asset production plus rollups.
    # Prefer "In-Situ (All Sites)" (individual sites) when available; fall back to "In-Situ Production".
    _insitu_sheet_name = "In-Situ (All Sites)" if "In-Situ (All Sites)" in wb.sheetnames else (
        "In-Situ Production" if "In-Situ Production" in wb.sheetnames else None
    )
    if _insitu_sheet_name:
        ws = wb[_insitu_sheet_name]
        company_row = [cell.value for cell in next(ws.iter_rows(min_row=3, max_row=3))]
        headers = [cell.value for cell in next(ws.iter_rows(min_row=4, max_row=4))]

        if _insitu_sheet_name == "In-Situ (All Sites)":
            # "In-Situ (All Sites)" uses left-aligned company markers (company name at first col of
            # each group); group boundaries are determined by "XYZ Total" header columns.
            company_by_col: dict[int, str] = {}
            group_start = 2
            for idx, raw_h in enumerate(headers, start=1):
                h = clean_text(raw_h)
                if h and "total" in h.lower() and "grand" not in h.lower():
                    # "Cenovus Total" → company = "Cenovus"
                    company_name = h.replace(" Total", "").strip()
                    for col in range(group_start, idx + 1):
                        company_by_col[col] = company_name
                    group_start = idx + 1
            # For remaining columns after the last Total (small individual producers),
            # use the explicit company name from the company row at that column.
            for idx, raw_co in enumerate(company_row, start=1):
                co = clean_text(raw_co)
                if co and co not in {"Company", "GRAND TOTAL"} and idx not in company_by_col:
                    company_by_col[idx] = co
        else:
            # "In-Situ Production" uses right-aligned company markers (name at Total column).
            company_markers: list[tuple[int, str]] = []
            for idx, value in enumerate(company_row, start=1):
                label = clean_text(value)
                if label and label not in {"Company", "GRAND TOTAL"}:
                    company_markers.append((idx, label))
            company_by_col = {}
            start_col = 2
            for marker_col, company in company_markers:
                for col in range(start_col, marker_col + 1):
                    company_by_col[col] = company
                start_col = marker_col + 1

        header_by_col: dict[int, str] = {}
        for idx, raw_header in enumerate(headers, start=1):
            header = clean_text(raw_header)
            if not header or idx == 1:
                continue
            company = company_by_col.get(idx, "")
            is_rollup = "total" in header.lower() or "grand total" in header.lower()
            location = None if is_rollup else resolve_oil_sands_asset_location("in_situ", company, header, oil_sands_locations)
            if location and location.get("is_rollup"):
                is_rollup = True
            asset_id = add_asset(
                display_name=header,
                source_id="aer_st53",
                production_system="in_situ",
                company=company,
                asset_kind=location.get("asset_kind", "company_rollup" if is_rollup else "in_situ_scheme") if location else ("company_rollup" if is_rollup else "in_situ_scheme"),
                latitude=as_float(location.get("latitude")) if location else None,
                longitude=as_float(location.get("longitude")) if location else None,
                is_rollup=is_rollup,
                coordinate_method=clean_text(location.get("method")) if location else None,
                geometry_kind=clean_text(location.get("geometry_kind")) if location else "",
                geometry_source=clean_text(location.get("geometry_source")) if location else "",
                geometry_features=location.get("geometry_features") if location else None,
                notes=" ".join(
                    bit
                    for bit in [
                        f"Imported from workbook sheet {_insitu_sheet_name}.",
                        clean_text(location.get("notes")) if location else "",
                    ]
                    if bit
                ),
            )
            header_by_col[idx] = asset_id

        for row in ws.iter_rows(min_row=5, values_only=True):
            date_value = as_date(row[0] if row else None)
            if not date_value:
                continue
            for col_idx, asset_id in header_by_col.items():
                header = clean_text(headers[col_idx - 1])
                add_record(
                    date_value,
                    asset_id,
                    "In-situ bitumen",
                    as_float(row[col_idx - 1] if col_idx - 1 < len(row) else None),
                    _insitu_sheet_name,
                    header,
                    "aer_st53",
                )

    # AER ST39: mined bitumen monthly section rows.
    if "Mined Bitumen" in wb.sheetnames:
        ws = wb["Mined Bitumen"]
        ownerships = [cell.value for cell in next(ws.iter_rows(min_row=4, max_row=4))]
        headers = [cell.value for cell in next(ws.iter_rows(min_row=5, max_row=5))]
        mined_cols: dict[int, str] = {}
        for idx, raw_header in enumerate(headers, start=1):
            header = clean_text(raw_header)
            if idx == 1 or not header:
                continue
            if "gross" not in header.lower():
                continue
            display_name = (
                header.replace(" Gross (bbl/d)", "")
                .replace(" Gross", "")
                .replace(" Mine", " Mine")
                .strip()
            )
            ownership = clean_text(ownerships[idx - 1] if idx - 1 < len(ownerships) else "")
            company = company_from_ownership(ownership)
            is_rollup = "total" in display_name.lower()
            location = None if is_rollup else resolve_oil_sands_asset_location("mined", company, display_name, oil_sands_locations)
            if location and location.get("is_rollup"):
                is_rollup = True
            asset_id = add_asset(
                display_name=display_name,
                source_id="aer_st39",
                production_system="mined",
                company=company,
                asset_kind=location.get("asset_kind", "mine" if not is_rollup else "company_rollup") if location else ("mine" if not is_rollup else "company_rollup"),
                latitude=as_float(location.get("latitude")) if location else None,
                longitude=as_float(location.get("longitude")) if location else None,
                ownership_text=ownership,
                is_rollup=is_rollup,
                coordinate_method=clean_text(location.get("method")) if location else None,
                geometry_kind=clean_text(location.get("geometry_kind")) if location else "",
                geometry_source=clean_text(location.get("geometry_source")) if location else "",
                geometry_features=location.get("geometry_features") if location else None,
                notes=" ".join(
                    bit
                    for bit in [
                        "Imported from workbook sheet Mined Bitumen.",
                        clean_text(location.get("notes")) if location else "",
                    ]
                    if bit
                ),
            )
            mined_cols[idx] = asset_id
        for row in ws.iter_rows(min_row=6, values_only=True):
            date_value = as_date(row[0] if row else None)
            if not date_value:
                break
            for col_idx, asset_id in mined_cols.items():
                add_record(
                    date_valu