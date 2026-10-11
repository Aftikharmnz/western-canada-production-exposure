"""Build actual asset/month totals with compact observation-availability metadata.

Numeric YYYY-MM entries remain compatible with the original seasonality index.
Source/stream months describe observed records, not a complete reporting universe:
an omitted well record must never be converted into an assumed zero.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re


BASE = Path(__file__).resolve().parents[1]
EXCLUDED_KINDS = {"province", "province_refinery", "region", "company_rollup", "asset_bucket"}


def build_index(data_dir: str | Path) -> dict:
    data_dir = Path(data_dir)
    print("Loading assets...")
    assets = json.loads((data_dir / "assets.json").read_text(encoding="utf-8"))
    if isinstance(assets, dict) and "fields" in assets and "rows" in assets:
        asset_rows = [dict(zip(assets["fields"], row)) for row in assets["rows"]]
    else:
        asset_rows = assets
    asset_id_by_ref = {idx: asset["asset_id"] for idx, asset in enumerate(asset_rows)}
    mapped_ids = {
        asset["asset_id"] for asset in asset_rows
        if asset.get("latitude") is not None and asset.get("longitude") is not None
        and not asset.get("is_rollup") and asset.get("asset_kind") not in EXCLUDED_KINDS
    }
    print(f"  Mapped assets: {len(mapped_ids):,}")

    index = {}
    group_months = {}
    asset_groups = {}
    multi_asset_month_groups = {}

    def add_observation(aid, date, volume, source, stream):
        if isinstance(volume, bool) or not isinstance(volume, (int, float)):
            return
        if not math.isfinite(volume) or volume < 0:
            return
        month = date[:7] if isinstance(date, str) else ""
        if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month):
            return

        group_key = None
        if isinstance(source, str) and source and isinstance(stream, str) and stream:
            group_key = (source, stream)
            group_months.setdefault(group_key, set()).add(month)

        # Group availability includes unmapped and excluded assets; selectable
        # asset totals retain the original mapping and rollup filters.
        if not aid or aid not in mapped_ids:
            return
        entry = index.setdefault(aid, {})
        groups = asset_groups.setdefault(aid, set())
        if group_key is not None:
            if group_key not in groups and len(groups) == 1:
                previous_group = next(iter(groups))
                # Most assets have one stream. Allocate detailed month/group
                # membership only once a second stream is actually observed.
                multi_asset_month_groups[aid] = {
                    previous_month: {previous_group} for previous_month in entry
                }
            groups.add(group_key)
            if len(groups) > 1:
                multi_asset_month_groups[aid].setdefault(month, set()).add(group_key)
        entry[month] = entry.get(month, 0) + volume

    def consume_payload(payload):
        if isinstance(payload, dict) and "rows" in payload:
            groups = [payload]
        elif isinstance(payload, list) and payload and isinstance(payload[0], dict) and "rows" in payload[0]:
            groups = payload
        elif isinstance(payload, list):
            for record in payload:
                if record.get("scenario") == "actual":
                    add_observation(record.get("asset_id"), record.get("date"), record.get("volume_kbbl_d"),
                                    record.get("source_id"), record.get("stream"))
            return
        else:
            return

        for group in groups:
            if group.get("scenario") != "actual":
                continue
            for row in group.get("rows", []):
                if len(row) < 2:
                    continue
                aid = asset_id_by_ref.get(row[0]) if isinstance(row[0], int) else row[0]
                add_observation(aid, group.get("date"), row[1], group.get("source_id"), group.get("stream"))

    print("Loading base records from monthly_production.json ...")
    base_records = json.loads((data_dir / "monthly_production.json").read_text(encoding="utf-8"))
    consume_payload(base_records)
    print(f"  Base records: {len(base_records):,} -> index assets so far: {len(index):,}")
    del base_records

    files = sorted((data_dir / "monthly").glob("*.json"))
    print(f"Loading {len(files)} on-demand monthly files...")
    for number, path in enumerate(files, 1):
        print(f"  [{number}/{len(files)}] {path.name}", end="\r", flush=True)
        consume_payload(json.loads(path.read_text(encoding="utf-8")))
    print()

    group_keys = sorted(group_months)
    group_refs = {key: position for position, key in enumerate(group_keys)}
    total_entries = sum(len(entry) for entry in index.values())
    for aid, entry in index.items():
        entry["__groups"] = sorted(group_refs[key] for key in asset_groups[aid])
        if aid in multi_asset_month_groups:
            entry["__month_groups"] = {
                month: sorted(group_refs[key] for key in groups)
                for month, groups in sorted(multi_asset_month_groups[aid].items())
            }
    index["__reporting"] = {
        "schema_version": 1,
        "policy": "Source/stream observation availability; omitted asset records are not zero",
        "groups": [
            {"source_id": source, "stream": stream, "months": sorted(group_months[(source, stream)])}
            for source, stream in group_keys
        ],
    }
    print(f"Assets with any observations: {len(index) - 1:,}")
    print(f"Total (asset, month) entries: {total_entries:,}")
    return index


def write_index(index: dict, output: str | Path) -> None:
    output = Path(output)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, separators=(",", ":"), allow_nan=False)
    temporary.replace(output)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build actual-only asset seasonality for a public or staged dataset.")
    parser.add_argument("--data-dir", type=Path, default=BASE / "public" / "data")
    args = parser.parse_args(argv)
    index = build_index(args.data_dir)
    output = args.data_dir / "asset_seasonality.json"
    print(f"Writing {output} ...")
    write_index(index, output)
    print(f"Done. File size: {output.stat().st_size / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
