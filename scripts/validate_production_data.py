"""Validate every browser production shard, including its cross-file references."""
from __future__ import annotations

import csv
import json
import math
import argparse
from pathlib import Path
from collections import defaultdict

from run_etl import M3_TO_BBL, PUBLIC_DATA_DIR, PROCESSED_DIR, write_json_file
from production_refresh import DATASET_MODE, safe_relative_path


def main(data_dir: Path = PUBLIC_DATA_DIR) -> None:
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    payload = json.loads((data_dir / "assets.json").read_text(encoding="utf-8"))
    official_only = manifest.get("dataset_mode") == DATASET_MODE
    if official_only:
        assert not any(key.startswith("workbook_") for key in manifest), "Analyst workbook metadata remains"
        assert manifest.get("source_state", {}).get("schema_version") == 1, "Missing durable ingestion receipts"
    assets = [dict(zip(payload["fields"], row)) for row in payload["rows"]]
    asset_by_id = {asset["asset_id"]: asset for asset in assets}
    assert len(asset_by_id) == len(assets), "Duplicate asset identifiers"
    for asset in assets:
        lat, lon = asset["latitude"], asset["longitude"]
        assert (lat is None) == (lon is None), f"Incomplete coordinate pair: {asset['asset_id']}"
        if lat is not None:
            assert math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180
    def check_coordinates(coords):
        if coords and isinstance(coords[0], (int, float)):
            assert len(coords) >= 2 and all(math.isfinite(v) for v in coords)
            assert -180 <= coords[0] <= 180 and -90 <= coords[1] <= 90, "Invalid geometry coordinate"
        else:
            for part in coords:
                check_coordinates(part)
    geometries = json.loads((data_dir / "asset_geometries.geojson").read_text(encoding="utf-8"))["features"]
    for feature in geometries:
        assert feature["properties"]["asset_id"] in asset_by_id, "Orphaned production footprint"
        check_coordinates(feature["geometry"]["coordinates"])
    assert len(geometries) == manifest["asset_geometry_feature_count"]
    count = 0
    coverage = {}
    totals = defaultdict(float)
    official = defaultdict(float)
    monthly_actual_dates = set()

    def check(record):
        nonlocal count
        aid, date, source, stream, scenario = (record[k] for k in ("asset_id", "date", "source_id", "stream", "scenario"))
        assert aid in asset_by_id, f"Unresolved asset reference: {aid}"
        assert date in manifest["periods"], f"Unindexed period: {date}"
        assert scenario in {"actual", "forecast"}, f"Unknown scenario: {scenario}"
        if official_only:
            assert scenario == "actual", "Forecast in an official-observations dataset"
            assert not any(key.startswith("workbook_") for key in record), "Analyst workbook record fields remain"
        value = record["volume_kbbl_d"]
        assert isinstance(value, (int, float)) and math.isfinite(value), "Nonfinite production"
        if "volume_bbl_d" in record:
            assert math.isclose(record["volume_bbl_d"], value * 1000, rel_tol=1e-9, abs_tol=1e-8), "bbl/d unit mismatch"
        asset = asset_by_id[aid]
        if not asset["is_rollup"] and asset["asset_kind"] not in {"province", "province_refinery", "region"}:
            totals[date] += value
        if source in {"aer_st53", "aer_st39"} and scenario == "actual" and asset["province"] == "Alberta":
            official[source, stream, date[:7]] += value
        if scenario == "actual":
            monthly_actual_dates.add(date)
        key = source, stream, scenario
        entry = coverage.setdefault(key, {"first": date, "last": date, "count": 0})
        entry["first"] = min(entry["first"], date)
        entry["last"] = max(entry["last"], date)
        entry["count"] += 1
        count += 1

    base = json.loads((data_dir / "monthly_production.json").read_text(encoding="utf-8"))
    seen = set()
    for record in base:
        if official_only:
            assert record.get("provenance_kind") == "official", "Unproven base-record origin"
            if record["source_id"] in {"aer_st53", "aer_st39"}:
                assert asset_by_id[record["asset_id"]]["province"] == "Alberta", "ST39/ST53 observation outside Alberta"
        key = tuple(record[k] for k in ("asset_id", "date", "source_id", "stream"))
        assert key not in seen, f"Duplicate or forecast/actual overlap: {key}"
        seen.add(key)
        check(record)
    for date, relative in manifest["monthly_record_files"].items():
        assert relative.startswith("public/data/"), "Unexpected shard URL"
        path = safe_relative_path(data_dir, relative[len("public/data/"):])
        groups = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(groups, dict):
            groups = [groups]
        seen = set()
        for group in groups:
            assert group["date"] == date, "Wrong shard month"
            for reference, value in group["rows"]:
                assert isinstance(reference, int) and 0 <= reference < len(assets), "Invalid compact asset reference"
                key = reference, group["source_id"], group["stream"]
                assert key not in seen, f"Duplicate monthly record: {date} {key}"
                seen.add(key)
                check({**group, "asset_id": assets[reference]["asset_id"], "volume_kbbl_d": value})
    assert count == manifest["record_count"], f"Record count mismatch: {count} / {manifest['record_count']}"
    required_sources = {"aer_st53", "aer_st39", "petrinex_ab_conventional_vol", "petrinex_sk_well_production",
                        "bcer_well_production", "ndic_well_production", "manitoba_well_production", "montana_bogc_well_production"}
    actual_sources = {source for source, _stream, scenario in coverage if scenario == "actual"}
    assert required_sources <= actual_sources, f"Missing production layers: {sorted(required_sources - actual_sources)}"
    for item in manifest["source_coverage"]:
        actual = coverage[item["source_id"], item["stream"], item["scenario"]]
        assert (actual["first"], actual["last"], actual["count"]) == (item["first_date"], item["last_date"], item["record_count"])
    for date, value in totals.items():
        assert abs(value - manifest["date_totals_kbbl_d"][date]) < 0.08, f"Monthly totals mismatch: {date}"
    assert manifest["latest_actual_date"] == max(monthly_actual_dates)
    assert "workbook_path" not in manifest, "Private workstation path in public metadata"
    assert manifest["data_quality"]["duplicate_asset_date_stream_group_count"] == 0
    reconciled = []
    if official_only:
        inputs = manifest["source_state"]["files"]
        source_totals = manifest.get("source_reconciliation", [])
        assert source_totals, "No independently retained AER source-unit totals"
        for item in source_totals:
            source, stream, period = item["source_id"], item["stream"], item["period"]
            fingerprints = item.get("input_sha256", {})
            assert fingerprints and all(inputs.get(path, {}).get("sha256") == digest and inputs[path]["source_id"] == source for path, digest in fingerprints.items()), "Reconciliation input receipts do not match the candidate"
            value = item["source_unit_total"] * M3_TO_BBL / 1000
            if item["units"] == "m3/month":
                import calendar
                year, month = map(int, period.split("-"))
                value /= calendar.monthrange(year, month)[1]
            else:
                assert item["units"] == "m3/d", "Unknown reconciliation unit"
            actual = official[source, stream, period]
            assert abs(actual - value) < 0.00001, f"Official source reconciliation failed: {source} {stream} {period}: {actual} / {value}"
            reconciled.append(dict(source=source, stream=stream, period=period, kbbl_d=round(value, 4)))
    for source in (() if official_only else ("aer_st53", "aer_st39")):
        extract = PROCESSED_DIR / f"{source}_{'official' if official_only else 'current'}_production.csv"
        if not extract.exists():
            continue
        expected = defaultdict(float)
        with extract.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                value = float(row["value"]) * M3_TO_BBL / 1000
                if row["units"] == "m3/month":
                    import calendar
                    year, month = map(int, row["period"].split("-"))
                    value /= calendar.monthrange(year, month)[1]
                expected[row["stream"], row["period"]] += value
        for (stream, period), value in expected.items():
            actual = official[source, stream, period]
            assert abs(actual - value) < 0.00001, f"Official source reconciliation failed: {source} {stream} {period}: {actual} / {value}"
            reconciled.append(dict(source=source, stream=stream, period=period, kbbl_d=round(value, 4)))
    result = dict(assets=len(assets), records=count, monthly_files=len(manifest["monthly_record_files"]),
                  latest_actual_date=manifest["latest_actual_date"], default_date=manifest["default_date"],
                  reconciled_official_periods=reconciled)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_json_file(PROCESSED_DIR / "production_validation.json", result, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "reconciled_official_periods"}, indent=2))
    print(f"All production references, units, coordinates, coverage and totals valid; {len(reconciled)} official series/months reconciled.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate production provenance, units and every staged browser shard.")
    parser.add_argument("--data-dir", type=Path, default=PUBLIC_DATA_DIR)
    main(parser.parse_args().data_dir)
