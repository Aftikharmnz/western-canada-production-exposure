"""Transactional, incremental refresh of directly published regulator observations.

The checked-in public dataset is the durable normalized history. Raw caches only
accelerate downloads; SHA-256 ingestion receipts in its manifest identify which
official bytes have already been transformed. Candidates are validated in an
isolated output directory and are promoted by the caller.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

PIPELINE_VERSION = 2
DATASET_MODE = "official_actuals"
GROUP_SOURCES = {
    "aer": {"aer_st53", "aer_st39"},
    "petrinex-ab": {"petrinex_ab_conventional_vol", "petrinex_ab_condensate_vol", "petrinex_ab_pentanes_plus_vol", "petrinex_ab_ngl_vol"},
    "petrinex-sk": {"petrinex_sk_well_production"},
    "bcer": {"bcer_well_production"},
    "ndic": {"ndic_well_production"},
    "manitoba": {"manitoba_well_production"},
    "montana": {"montana_bogc_well_production"},
}
DIRECT_SOURCES = set().union(*GROUP_SOURCES.values())
GROUP_REFERENCES = {
    "aer": {"aer_st44", "aer_scheme_spatial", "aer_st102_facility_spatial"},
    "petrinex-ab": {"petrinex_ab_well_facility_link"},
    "petrinex-sk": {"petrinex_sk_well_infrastructure"},
    "bcer": {"bcer_well_index", "bcer_well_surface_locations"},
    "ndic": set(), "manitoba": set(), "montana": {"montana_bogc_well_list"},
}
RECEIPT_FIELDS = ("source_id", "url", "raw_path", "sha256", "bytes", "checked_at", "etag", "last_modified", "period", "publication_period", "discovery_url", "updated_at")


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def safe_relative_path(directory: Path, relative: str) -> Path:
    path = (directory / relative.replace("\\", "/")).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError(f"Path escapes its dataset directory: {relative}")
    return path


def asset_payload_rows(payload):
    return [dict(zip(payload["fields"], row)) for row in payload["rows"]] if isinstance(payload, dict) else payload


def asset_from_public_row(etl, row):
    fields = {field.name for field in dataclasses.fields(etl.Asset)}
    values = {key: value for key, value in row.items() if key in fields}
    values.setdefault("source_name", etl.source_name(row["source_id"]))
    values["is_rollup"] = bool(values.get("is_rollup", False))
    method = values.get("coordinate_method", "")
    if values.get("asset_kind") == "dls_site" or "dls" in method or "ags_ats" in method:
        values.setdefault("geometry_kind", "dls_centroid")
        values.setdefault("location_basis", "published_dls")
    return etl.Asset(**values)


def keep_official_record(record, assets, direct_baseline=False):
    """Fail closed on analyst history, forecasts and unsupported source families."""
    source = record.get("source_id")
    if source not in DIRECT_SOURCES or record.get("scenario") != "actual":
        return False
    asset = assets.get(record.get("asset_id"))
    if not asset or asset.get("is_rollup") or asset.get("asset_kind") in {"province", "province_refinery", "region", "company_rollup", "asset_bucket"}:
        return False
    if source in GROUP_SOURCES["aer"]:
        # The old bundle mixed workbook histories with labelled direct overlays.
        document = record.get("source_document") or record.get("workbook_sheet") or ""
        return asset.get("province") == "Alberta" and (direct_baseline or document.startswith("Official aer_"))
    return True


def load_baseline(etl, directory: Path, manifest):
    payload = json.loads((directory / "assets.json").read_text(encoding="utf-8"))
    asset_rows = asset_payload_rows(payload)
    source_assets = {row["asset_id"]: row for row in asset_rows}
    records = []
    discarded = 0
    direct = manifest.get("dataset_mode") == DATASET_MODE

    def retain(row):
        nonlocal discarded
        if not keep_official_record(row, source_assets, direct):
            discarded += 1
            return
        volume = etl.as_float(row.get("volume_kbbl_d"))
        if volume is None or volume < 0:
            raise ValueError("Invalid published baseline production value")
        record = {key: row[key] for key in ("date", "asset_id", "source_id", "stream", "scenario")}
        record.update(period=row["date"][:7], source_name=etl.source_name(row["source_id"]),
                      volume_kbbl_d=volume, volume_bbl_d=row.get("volume_bbl_d", volume * 1000), units="bbl/d",
                      provenance_kind="official", source_document=row.get("source_document") or row.get("workbook_sheet") or "Published official-source history",
                      source_row=row.get("source_row") or row.get("workbook_column") or "")
        records.append(record)

    for row in json.loads((directory / "monthly_production.json").read_text(encoding="utf-8")):
        retain(row)
    for date, relative in sorted(manifest.get("monthly_record_files", {}).items()):
        prefix = "public/data/"
        if not relative.startswith(prefix):
            raise ValueError(f"Invalid baseline monthly location: {relative}")
        groups = json.loads(safe_relative_path(directory, relative[len(prefix):]).read_text(encoding="utf-8"))
        groups = [groups] if isinstance(groups, dict) else groups
        for group in groups:
            if group["date"] != date:
                raise ValueError("Baseline month is not indexed correctly")
            for ref, volume in group["rows"]:
                if not isinstance(ref, int) or not 0 <= ref < len(asset_rows):
                    raise ValueError("Invalid baseline compact asset reference")
                retain({"date": date, "asset_id": asset_rows[ref]["asset_id"], "volume_kbbl_d": volume,
                        **{key: group[key] for key in ("source_id", "stream", "scenario")}})
    assets = {aid: asset_from_public_row(etl, row) for aid, row in source_assets.items()}
    geometry_path = directory / "asset_geometries.geojson"
    if geometry_path.exists():
        for feature in json.loads(geometry_path.read_text(encoding="utf-8"))["features"]:
            aid = feature["properties"].get("asset_id")
            if aid in assets:
                assets[aid].geometry_features.append(feature)
                for key in ("location_basis", "geometry_kind", "geometry_source"):
                    if feature["properties"].get(key):
                        setattr(assets[aid], key, feature["properties"][key])
    return assets, records, discarded


def make_callbacks(etl, assets, records):
    def add_asset(**kwargs):
        aid = kwargs.pop("asset_id_override", None) or f"{kwargs['source_id']}:{etl.slug(kwargs['production_system'])}:{etl.slug(kwargs.get('company', ''))}:{etl.slug(kwargs['display_name'])}"
        kwargs.setdefault("province", "Alberta")
        kwargs.setdefault("asset_kind", "asset")
        kwargs.setdefault("company", "")
        kwargs.setdefault("latitude", None)
        kwargs.setdefault("longitude", None)
        kwargs["geometry_features"] = list(kwargs.get("geometry_features") or [])
        kwargs["coordinate_method"] = kwargs.get("coordinate_method") or etl.infer_coordinate_method(kwargs["latitude"], kwargs["longitude"], kwargs.get("notes", ""))
        kwargs["location_confidence"] = etl.coordinate_confidence(kwargs["latitude"], kwargs["longitude"], kwargs["coordinate_method"], geometry_kind=kwargs.get("geometry_kind", ""), asset_kind=kwargs["asset_kind"])
        prior = assets.get(aid)
        confidence_rank = {"unmapped": -1, "low": 0, "medium": 1, "high": 2, "exact": 3}
        if prior and confidence_rank.get(prior.location_confidence, -1) > confidence_rank.get(kwargs["location_confidence"], -1):
            for key in ("latitude", "longitude", "coordinate_method", "location_confidence", "location_basis", "geometry_kind", "geometry_source", "geometry_features"):
                kwargs[key] = getattr(prior, key)
        assets[aid] = etl.Asset(asset_id=aid, source_name=etl.source_name(kwargs["source_id"]), **kwargs)
        return aid

    def add_record(date, aid, stream, volume, document, row, source, scenario="actual"):
        value = etl.as_float(volume)
        if scenario != "actual" or source not in DIRECT_SOURCES:
            raise ValueError("Only directly sourced actual production is accepted")
        if value is None or value < 0:
            raise ValueError("Invalid official production value")
        date = etl.month_end(date)
        if date < etl.CUTOFF:
            return
        records.append(dict(date=date.isoformat(), period=date.strftime("%Y-%m"), asset_id=aid, source_id=source,
                            source_name=etl.source_name(source), stream=stream, scenario="actual", units="bbl/d",
                            volume_bbl_d=value, volume_kbbl_d=value / 1000, provenance_kind="official",
                            source_document=document, source_row=str(row)))
    return add_asset, add_record


def seed_published_dls(etl, assets):
    """Make coordinates reproducible without a private processed-location cache."""
    result = {}
    for asset in assets.values():
        if asset.latitude is None or "dls" not in (asset.location_basis + asset.geometry_kind).lower():
            continue
        match = re.search(r"\b\d{1,2}-\d{1,2}-\d{2,3}-\d{1,2}W[1-6]\b", asset.display_name)
        if not match:
            continue
        dls = etl.format_dls(*etl.parse_dls_label(match[0]))
        key = asset.province, dls
        if key not in result or result[key]["method"] == "approx_dls_centroid":
            result[key] = dict(province=asset.province, dls=dls, latitude=str(asset.latitude), longitude=str(asset.longitude), method=asset.coordinate_method)
    return result


def guard_source_replacement(existing, incoming, source_ids, periods, current_source=False, active_streams=False):
    present = {(row["source_id"], row["stream"], row["date"][:7]) for row in incoming}
    expected = {(row["source_id"], row["stream"], row["date"][:7]) for row in existing
                if row["source_id"] in source_ids and row["date"][:7] in periods}
    missing = expected - present
    if missing:
        raise ValueError("Official transform dropped previously published source/stream/month partitions: " + str(sorted(missing)[:8]))
    if active_streams and incoming:
        newest = max(row["date"] for row in incoming)
        previous = {}
        for row in existing:
            if row["source_id"] in source_ids:
                key = row["source_id"], row["stream"]
                previous[key] = max(previous.get(key, ""), row["date"])
        if previous and newest >= max(previous.values()):
            recent = (dt.date.fromisoformat(max(previous.values())) - dt.timedelta(days=190)).isoformat()
            absent = [(source, stream) for (source, stream), last in previous.items() if last >= recent and (source, stream, newest[:7]) not in present]
            if absent:
                raise ValueError(f"Active official product streams are absent from {newest}: {sorted(absent)}")
    if current_source:
        for source in source_ids:
            old_latest = max((row["date"] for row in existing if row["source_id"] == source), default="")
            new_latest = max((row["date"] for row in incoming if row["source_id"] == source), default="")
            if old_latest and new_latest < old_latest:
                raise ValueError(f"Official current coverage regressed for {source}: {old_latest} -> {new_latest}")


def replace_partitions(existing, incoming, source_ids, periods):
    """Replace complete source-months, including deleted wells and revised zeros."""
    if any(row["source_id"] not in source_ids or row["date"][:7] not in periods for row in incoming):
        raise ValueError("Transform returned an out-of-scope source/month")
    seen = {}
    for row in incoming:
        key = tuple(row[key] for key in ("asset_id", "date", "source_id", "stream"))
        if key in seen:
            # Separate AER approval components can share a canonical identity.
            prior = seen[key]
            prior["volume_bbl_d"] += row["volume_bbl_d"]
            prior["volume_kbbl_d"] += row["volume_kbbl_d"]
        else:
            seen[key] = dict(row)
    return [row for row in existing if not (row["source_id"] in source_ids and row["date"][:7] in periods)] + list(seen.values())


def _descriptor(source, **extra):
    return {key: value for key, value in {**source, **extra}.items() if key in {"source_id", "url", "raw_file", "period", "current", "report_year", "publication_period", "discovery_url", "updated_at"}}


def collect_inputs(etl, args, groups, baseline):
    from official_source_discovery import discover_sources, discover_aer_files
    registry = {row["source_id"]: row for row in etl.SOURCE_MANIFEST}
    descriptors = []
    notices = []
    prior_tokens = baseline.get("source_state", {}).get("publication_tokens", {})
    args.publication_tokens = dict(prior_tokens)
    discovery_ids = set()
    if "aer" in groups:
        discovery_ids.update({"aer_st53", "aer_st39", "aer_st44"})
    if "manitoba" in groups:
        discovery_ids.add("manitoba_well_production")
    if args.offline:
        cached_discovery = etl.RAW_DIR / "discovery/reports.json"
        discovered = json.loads(cached_discovery.read_text(encoding="utf-8")) if cached_discovery.exists() else []
        if isinstance(discovered, dict):
            discovered = discovered.get("reports", discovered.get("sources", []))
        descriptors.extend(_descriptor(row) for row in discovered if row.get("source_id") in discovery_ids and (etl.RAW_DIR / row["raw_file"]).exists())
        for sid in discovery_ids & {"aer_st53", "aer_st39"}:
            known = {row["raw_file"] for row in descriptors}
            for path in discover_aer_files(etl.RAW_DIR, sid):
                if path.name not in known:
                    descriptors.append(_descriptor(registry[sid], raw_file=path.name, current="_current." in path.name))
        if "aer_st44" in discovery_ids and not any(row["source_id"] == "aer_st44" for row in descriptors):
            path = etl.ST44_PATH if etl.ST44_PATH.exists() else etl.RAW_DIR / "aer_st44_2026_q2.xlsx"
            if path.exists():
                known = next((row for row in discovered if row.get("source_id") == "aer_st44"), registry["aer_st44"])
                descriptors.append(_descriptor(known, raw_file=path.name))
        if "manitoba" in groups and not any(row["source_id"] == "manitoba_well_production" for row in descriptors):
            descriptors.extend(_descriptor(registry["manitoba_well_production"], raw_file=str(path.relative_to(etl.RAW_DIR))) for path in etl.MANITOBA_DIR.glob("wmp_*_excel.zip"))
    elif discovery_ids:
        aer_ids = discovery_ids - {"manitoba_well_production"}
        if aer_ids:
            descriptors.extend(discover_sources(etl.RAW_DIR, args.history_start, source_ids=aer_ids))
        if "manitoba_well_production" in discovery_ids:
            descriptors.extend(discover_sources(etl.RAW_DIR, args.history_start or etl.MANITOBA_DEFAULT_START_PERIOD, source_ids={"manitoba_well_production"}))

    for group in groups:
        for sid in GROUP_REFERENCES[group] - {"aer_st44"}:
            descriptors.append(_descriptor(registry[sid]))
        if group in {"petrinex-ab", "petrinex-sk", "ndic"}:
            monthly_source = {"petrinex-ab": "petrinex_ab_conventional_vol", "petrinex-sk": "petrinex_sk_well_production", "ndic": "ndic_well_production"}[group]
            catalog = {}
            if group == "ndic":
                available = sorted(filter(None, (etl.ndic_period_from_filename(path.name) for path in etl.NDIC_DIR.glob("*.xlsx")))) if args.offline else etl.discover_ndic_available_periods()
            else:
                jurisdiction = "AB" if group == "petrinex-ab" else "SK"
                directory = etl.PETRINEX_AB_VOL_DIR if jurisdiction == "AB" else etl.PETRINEX_SK_VOL_DIR
                if args.offline:
                    available = sorted(path.name[4:11] for path in directory.glob(f"Vol_????-??-{jurisdiction}.zip"))
                else:
                    from official_source_discovery import discover_petrinex_months
                    found = discover_petrinex_months(jurisdiction, etl.RAW_DIR)
                    available = sorted(item["period"] if isinstance(item, dict) else item for item in found)
                    catalog = {item["period"]: {key: item[key] for key in ("updated_at", "timestamp_timezone", "url") if key in item} for item in found if isinstance(item, dict)}
            if not available:
                raise ValueError(f"No published monthly reports discovered for {group}")
            periods = [period for period in available if period >= args.history_start] if args.history_start else available[-args.update_months:]
            latest_baseline = max((row["last_date"][:7] for row in baseline.get("source_coverage", []) if row["source_id"] in GROUP_SOURCES[group] and row["scenario"] == "actual"), default="")
            if baseline and latest_baseline:
                periods = sorted(set(periods) | {period for period in available if period > latest_baseline})
            if args.full_revision_scan and group == "ndic":
                prior = baseline.get("source_state", {}).get("files", {}).values()
                periods = sorted(set(periods) | {item["period"] for item in prior if item.get("source_id") in GROUP_SOURCES[group] and item.get("period") in available})
            for period, token in catalog.items():
                key = f"{monthly_source}:{period}"
                previous = prior_tokens.get(key)
                if args.full_revision_scan and previous and previous.get("updated_at") != token.get("updated_at"):
                    periods = sorted(set(periods) | {period})
                # First-seen old periods are catalog observations, not evidence
                # that their raw bytes have been downloaded or re-ingested.
                if previous is None or period in periods:
                    args.publication_tokens[key] = {**token, "observed_at": etl.RUN_DATE.isoformat(), "catalog_only": period not in periods}
            for period in periods:
                if group == "ndic":
                    path = etl.ndic_mpr_path(period)
                    sid = "ndic_well_production"
                    url = f"{etl.NDIC_MPR_BASE_URL}/{path.name}"
                else:
                    jurisdiction = "AB" if group == "petrinex-ab" else "SK"
                    sid = "petrinex_ab_conventional_vol" if jurisdiction == "AB" else "petrinex_sk_well_production"
                    path = etl.petrinex_ab_vol_path(period) if jurisdiction == "AB" else etl.petrinex_sk_vol_path(period)
                    url = f"https://www.petrinex.gov.ab.ca/publicdata/API/Files/{jurisdiction}/Vol/{period}/CSV"
                descriptors.append(dict(source_id=sid, raw_file=path.relative_to(etl.RAW_DIR).as_posix(), url=url, period=period, current=True,
                                        **{key: catalog[period][key] for key in ("updated_at", "timestamp_timezone") if period in catalog and key in catalog[period]}))
            if available[-1] < etl.previous_month_period() and not args.offline:
                notices.append(dict(source_id=monthly_source, status="not_published", period=etl.previous_month_period(),
                                    latest_published_period=available[-1], basis="Official published-report index", content_changed=False))
        elif group == "bcer":
            descriptors.append(_descriptor(registry["bcer_well_production"], current=True))
        elif group == "montana":
            descriptors.append(_descriptor(registry["montana_bogc_well_production"], current=True))
    # A source can be used by discovery and also appear as a reference.
    return list({row["raw_file"].replace("\\", "/"): row for row in descriptors}.values()), notices


def check_inputs(etl, args, descriptors, prior_receipts):
    checks = []
    for descriptor in descriptors:
        relative = descriptor["raw_file"].replace("\\", "/")
        path = safe_relative_path(etl.RAW_DIR, relative)
        prior = prior_receipts.get(relative, {})
        if args.offline:
            check = dict(status="cached" if path.exists() else "failed", error=None if path.exists() else "Required official raw cache is missing")
        elif descriptor["source_id"] == "bcer_well_surface_locations":
            check = etl.download_bcer_well_surface_points(force=True)
        else:
            # Annual snapshots get rechecked on the weekly full revision scan;
            # mutable current/monthly/reference downloads are always fetched.
            immutable = descriptor.get("report_year") is not None
            check = etl.download_url(descriptor["url"], path, force=not immutable or args.full_revision_scan or not prior)
        check.update({key: value for key, value in descriptor.items() if key != "raw_file"})
        check["raw_path"] = relative
        check["checked_at"] = None if args.offline or check["status"] == "cached" else etl.RUN_DATE.isoformat()
        check.pop("local_path", None)
        check["mode"] = "offline" if args.offline else "online"
        if path.exists() and check["status"] != "failed":
            check["sha256"] = sha256_file(path)
            check["bytes"] = path.stat().st_size
            check["content_changed"] = check["sha256"] != prior.get("sha256")
        else:
            check["content_changed"] = False
        if check.get("error"):
            check["error"] = str(check["error"]).replace(str(etl.ROOT), "[workspace]")
        checks.append(check)
    return checks


def main(etl, argv=None):
    parser = argparse.ArgumentParser(description="Refresh direct official production observations into a validated candidate dataset.")
    parser.add_argument("--baseline-dir", type=Path, default=etl.ROOT / "public/data")
    parser.add_argument("--output-dir", type=Path, default=etl.PROCESSED_DIR / "production-candidate")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="Use reviewed raw caches; never represent this as a new web check.")
    mode.add_argument("--download", action="store_true", help="Discover and refresh official reports (the default).")
    parser.add_argument("--sources", default=",".join(GROUP_SOURCES), help="Comma-separated source groups: " + ",".join(GROUP_SOURCES))
    parser.add_argument("--update-months", type=int, default=3)
    parser.add_argument("--history-start", help="YYYY-MM lower bound for a requested historical refresh.")
    parser.add_argument("--full-rebuild", action="store_true", help="Start without normalized published history.")
    parser.add_argument("--full-revision-scan", action="store_true", help="Re-fetch archived reports and all previously receipted monthly inputs.")
    parser.add_argument("--result-json", type=Path, default=etl.PROCESSED_DIR / "production-refresh-result.json")
    args = parser.parse_args(argv)
    groups = set(filter(None, args.sources.split(",")))
    if not groups or not groups <= GROUP_SOURCES.keys():
        parser.error("--sources contains an unknown or empty source group")
    if args.update_months < 1 or args.update_months > 120:
        parser.error("--update-months must be between 1 and 120")
    if args.history_start and not etl.parse_period(args.history_start):
        parser.error("--history-start must be YYYY-MM")
    args.output_dir = args.output_dir.resolve()
    args.baseline_dir = args.baseline_dir.resolve()
    if args.output_dir == args.baseline_dir or args.output_dir.is_relative_to(args.baseline_dir):
        parser.error("--output-dir must be isolated from the published baseline")
    result = dict(schema_version=1, started_at=etl.RUN_DATE.isoformat(), mode="offline" if args.offline else "online", status="failed",
                  candidate_changed=False, changed_partitions=[], checks=[], errors=[])
    try:
        etl.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        etl.RAW_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = args.baseline_dir / "manifest.json"
        baseline = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() and not args.full_rebuild else {}
        prior_receipts = baseline.get("source_state", {}).get("files", {})
        migration = baseline.get("dataset_mode") != DATASET_MODE or baseline.get("pipeline_version") != PIPELINE_VERSION
        descriptors, notices = collect_inputs(etl, args, groups, baseline)
        checks = check_inputs(etl, args, descriptors, prior_receipts)
        result["checks"] = checks + notices
        failures = [check for check in checks if check["status"] == "failed"]
        if failures:
            raise ValueError("Failed official inputs: " + "; ".join(f"{item['source_id']} {item.get('period', '')}: {item.get('error')}" for item in failures))
        changed = {check["raw_path"] for check in checks if check["content_changed"]}
        if not changed and not migration:
            result.update(status="noop", candidate_changed=False)
            return 0
        if baseline:
            etl.log("Loading directly sourced published production history...")
            assets, records, discarded = load_baseline(etl, args.baseline_dir, baseline)
        else:
            assets, records, discarded = {}, [], 0
        result["discarded_nonofficial_or_forecast_records"] = discarded
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name in ("aer_scheme_approvals.geojson", "aer_st102_oil_sands_facilities.geojson"):
            source = args.baseline_dir / name
            if source.exists():
                shutil.copy2(source, args.output_dir / name)
        etl.PUBLIC_DATA_DIR = args.output_dir
        etl.SCHEME_GEOJSON_PATH = args.output_dir / "aer_scheme_approvals.geojson"
        etl.ASSET_GEOMETRIES_GEOJSON_PATH = args.output_dir / "asset_geometries.geojson"
        etl.ST102_OIL_SANDS_GEOJSON_PATH = args.output_dir / "aer_st102_oil_sands_facilities.geojson"
        etl.ALLOW_LOCATION_DOWNLOADS = False  # DLS approximations are labelled; the bulk ETL never issues per-well web calls.
        etl.BASELINE_DLS_CACHE = seed_published_dls(etl, assets)
        etl.AER_SOURCE_TOTALS = {}
        etl.MONTANA_ACTIVE_START_PERIOD = args.history_start or etl.MONTANA_DEFAULT_START_PERIOD
        receipt_updates = dict(prior_receipts)
        for group in sorted(groups):
            inputs = [check for check in checks if check["source_id"] in GROUP_SOURCES[group] | GROUP_REFERENCES[group]]
            source_changed = any(check["raw_path"] in changed for check in inputs)
            if not source_changed and not migration:
                continue
            incoming = []
            add_asset, add_record = make_callbacks(etl, assets, incoming)
            period_inputs = [check for check in inputs if check.get("period")]
            reference_changed = any(check["source_id"] in GROUP_REFERENCES[group] and check["raw_path"] in changed for check in inputs)
            periods = {check["period"] for check in period_inputs if check["content_changed"] or reference_changed or migration}
            if group == "aer":
                st44 = next((check for check in inputs if check["source_id"] == "aer_st44"), None)
                if st44:
                    etl.ST44_PATH = safe_relative_path(etl.RAW_DIR, st44["raw_path"])
                spatial = etl.RAW_DIR / "aer_scheme_approval_spatial.zip"
                if spatial.exists():
                    import build_scheme_geojson
                    etl.write_json_file(etl.SCHEME_GEOJSON_PATH, build_scheme_geojson.build(), separators=(",", ":"))
                etl.AER_IMPORT_PATHS = {sid: [safe_relative_path(etl.RAW_DIR, check["raw_path"]) for check in inputs if check["source_id"] == sid] for sid in GROUP_SOURCES["aer"]}
                locations = etl.build_oil_sands_location_index()
                etl.overlay_official_aer_current(assets, incoming, add_asset, add_record, locations, canonical_ids=True)
            elif group == "petrinex-ab":
                etl.append_petrinex_ab_conventional(assets, incoming, add_asset, add_record, periods=periods)
            elif group == "petrinex-sk":
                etl.append_petrinex_sk_well_production(add_asset, add_record, periods=periods)
            elif group == "ndic":
                etl.append_ndic_well_production(add_asset, add_record, periods=periods)
            elif group == "bcer":
                etl.append_bcer_well_production(add_asset, add_record)
            elif group == "manitoba":
                # Archives can overlap; newer windows replace matching months.
                for check in sorted(inputs, key=lambda item: item["raw_path"]):
                    etl.MANITOBA_PRODUCTION_ZIP = safe_relative_path(etl.RAW_DIR, check["raw_path"])
                    part = []
                    a, r = make_callbacks(etl, assets, part)
                    etl.append_manitoba_well_production(a, r, start_period=args.history_start)
                    incoming = replace_partitions(incoming, part, GROUP_SOURCES[group], {row["date"][:7] for row in part})
            elif group == "montana":
                etl.append_montana_bakken_well_production(add_asset, add_record, start_period=args.history_start)
            actual_periods = {row["date"][:7] for row in incoming}
            if not incoming or (periods and not periods <= actual_periods):
                raise ValueError(f"{group} transform omitted required source/month observations: {sorted(periods - actual_periods)}")
            if not periods:
                periods = actual_periods
            guard_source_replacement(records, incoming, GROUP_SOURCES[group], periods, current_source=group in {"aer", "bcer", "manitoba", "montana"}, active_streams=group in {"petrinex-ab", "bcer"})
            for sid in sorted(GROUP_SOURCES[group]):
                source_incoming = [row for row in incoming if row["source_id"] == sid]
                source_periods = {row["date"][:7] for row in source_incoming}
                records = replace_partitions(records, source_incoming, {sid}, source_periods)
                result["changed_partitions"].append(dict(source_id=sid, periods=sorted(source_periods)))
            for check in inputs:
                receipt = dict(prior_receipts.get(check["raw_path"], {}))
                receipt.update({key: check[key] for key in RECEIPT_FIELDS if check.get(key) is not None})
                receipt["ingested_at"] = etl.RUN_DATE.isoformat()
                receipt["ingestion_mode"] = result["mode"]
                receipt_updates[check["raw_path"]] = receipt
        used = {row["asset_id"] for row in records}
        assets = {aid: asset for aid, asset in assets.items() if aid in used}
        if not records:
            raise ValueError("No direct official observations available to publish")
        latest = max(row["date"] for row in records)
        metadata = dict(dataset_mode=DATASET_MODE, pipeline_version=PIPELINE_VERSION, generated_at=etl.RUN_DATE.isoformat(),
                        latest_actual_date=latest, cutoff_date=etl.CUTOFF.isoformat(), source_state=dict(schema_version=1, files=receipt_updates, publication_tokens=args.publication_tokens),
                        ingestion_mode=result["mode"], baseline_history_policy="Preserve previously published direct regulator observations; analyst workbook rows and all forecasts are excluded.")
        metadata["source_reconciliation"] = [row for row in baseline.get("source_reconciliation", []) if row["source_id"] not in etl.AER_SOURCE_TOTALS]
        for source, rows in etl.AER_SOURCE_TOTALS.items():
            fingerprints = {key: value["sha256"] for key, value in receipt_updates.items() if value["source_id"] == source}
            metadata["source_reconciliation"].extend({**row, "input_sha256": fingerprints} for row in rows)
        etl.write_web_exports(assets, records, metadata, checks + notices)
        # Release the large normalized store before independent file validation.
        count, asset_count = len(records), len(assets)
        del records, assets, incoming
        subprocess.run([sys.executable, str(etl.ROOT / "scripts/build_seasonality_index.py"), "--data-dir", str(args.output_dir)], check=True)
        subprocess.run([sys.executable, str(etl.ROOT / "scripts/validate_production_data.py"), "--data-dir", str(args.output_dir)], check=True)
        result.update(status="changed", candidate_changed=True, records=count, assets=asset_count,
                      output_dir=str(args.output_dir.relative_to(etl.ROOT)) if args.output_dir.is_relative_to(etl.ROOT) else args.output_dir.name,
                      source_state=metadata["source_state"])
        return 0
    except Exception as exc:
        result["errors"].append(str(exc).replace(str(etl.ROOT), "[workspace]"))
        etl.log("Production refresh failed: " + result["errors"][-1])
        return 1
    finally:
        result["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        etl.write_json_file(args.result_json, result, indent=2)
        etl.log(json.dumps({key: result[key] for key in ("status", "candidate_changed", "errors")}, indent=2))
