"""
compact_monthly.py
------------------
Converts existing monthly Petrinex JSON files from the verbose array-of-objects
format into a compact header + rows format.

Before (per record, repeated 30,000+ times):
  {"date":"2026-01-31","period":"2026-01","asset_id":"...","source_id":"...",
   "source_name":"...","stream":"...","volume_bbl_d":0.123,"volume_kbbl_d":0.000123,
   "units":"bbl/d","scenario":"actual","workbook_sheet":"...","workbook_column":"..."}

After (shared fields stored once, rows are just [asset_id, volume_kbbl_d]):
  {"date":"2026-01-31","source_id":"petrinex_ab_conventional_vol",
   "stream":"Conventional crude oil","scenario":"actual",
   "rows":[["asset_id_1",0.000123],["asset_id_2",0.456],...]}

Run from the project root:
    python scripts/compact_monthly.py
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
MONTHLY_DIR = ROOT / "public" / "data" / "monthly"


def compact_file(path: Path) -> tuple[int, int]:
    """
    Convert a single monthly file to compact format.
    Returns (original_bytes, new_bytes).
    """
    raw = path.read_bytes()
    original_size = len(raw)

    data = json.loads(raw)

    # Already compact format — skip
    if isinstance(data, dict) and "rows" in data:
        return original_size, original_size

    if not isinstance(data, list) or not data:
        return original_size, original_size

    # Group records by (source_id, stream, scenario) in case a file has mixed sources
    groups: dict[tuple, list] = defaultdict(list)
    for record in data:
        key = (
            record.get("source_id", ""),
            record.get("stream", ""),
            record.get("scenario", "actual"),
        )
        vol = record.get("volume_kbbl_d", 0.0)
        # Skip zero / effectively-zero volumes to save further space
        if vol is not None and vol > 0.0:
            groups[key].append([record["asset_id"], round(float(vol), 6)])

    date_val = data[0].get("date", path.stem.replace("petrinex_ab_", ""))

    if len(groups) == 1:
        # Common case: single source/stream/scenario — flat compact object
        (source_id, stream, scenario), rows = next(iter(groups.items()))
        compact = {
            "date": date_val,
            "source_id": source_id,
            "stream": stream,
            "scenario": scenario,
            "rows": rows,
        }
    else:
        # Multiple groups (rare) — array of compact group objects
        compact = [
            {
                "date": date_val,
                "source_id": source_id,
                "stream": stream,
                "scenario": scenario,
                "rows": rows,
            }
            for (source_id, stream, scenario), rows in groups.items()
        ]

    out = json.dumps(compact, separators=(",", ":"), ensure_ascii=False)
    path.write_text(out, encoding="utf-8")
    return original_size, len(out.encode())


def main():
    if not MONTHLY_DIR.exists():
        print(f"Monthly directory not found: {MONTHLY_DIR}")
        sys.exit(1)

    files = sorted(MONTHLY_DIR.glob("*.json"))
    if not files:
        print("No monthly JSON files found.")
        sys.exit(0)

    print(f"Compacting {len(files)} monthly files in {MONTHLY_DIR}\n")

    total_before = 0
    total_after = 0

    for f in files:
        before, after = compact_file(f)
        total_before += before
        total_after += after
        saved_pct = (1 - after / before) * 100 if before > 0 else 0
        print(f"  {f.name}  {before/1024/1024:.1f} MB → {after/1024/1024:.1f} MB  ({saved_pct:.0f}% smaller)")

    print(f"\nTotal: {total_before/1024/1024:.1f} MB → {total_after/1024/1024:.1f} MB  "
          f"({(1 - total_after/total_before)*100:.0f}% reduction)")
    print("\nDone. Run 'git add -f public/data/monthly/' and commit to push the compacted files.")


if __name__ == "__main__":
    main()
