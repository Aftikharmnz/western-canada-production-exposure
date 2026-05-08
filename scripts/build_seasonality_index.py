"""
build_seasonality_index.py
Pre-aggregates all monthly Petrinex files into a compact lookup:
  { asset_id: { "YYYY-MM": kbbl_d, ... }, ... }
Only assets that appear in assets.json (have coordinates) are included.
Output: public/data/asset_seasonality.json  (~5-15 MB)
"""
import json, glob, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHLY_DIR = os.path.join(BASE, "public", "data", "monthly")
ASSETS_FILE = os.path.join(BASE, "public", "data", "assets.json")
OUT_FILE    = os.path.join(BASE, "public", "data", "asset_seasonality.json")

print("Loading assets...")
with open(ASSETS_FILE) as f:
    assets = json.load(f)
# Only keep assets that are actually mappable (have coordinates)
mapped_ids = {a["asset_id"] for a in assets if a.get("latitude") and a.get("longitude")}
print(f"  Mapped assets: {len(mapped_ids):,}")

files = sorted(glob.glob(os.path.join(MONTHLY_DIR, "*.json")))
print(f"Loading {len(files)} monthly files...")

# { asset_id: { "YYYY-MM": total_kbbl_d } }
index = {}

for i, fpath in enumerate(files):
    fname = os.path.basename(fpath)
    print(f"  [{i+1}/{len(files)}] {fname}", end="\r", flush=True)
    with open(fpath) as f:
        records = json.load(f)
    for r in records:
        aid = r.get("asset_id")
        if aid not in mapped_ids:
            continue
        vol = r.get("volume_kbbl_d") or 0
        if vol <= 0:
            continue
        ym = r.get("date", "")[:7]  # "YYYY-MM"
        if not ym:
            continue
        if aid not in index:
            index[aid] = {}
        index[aid][ym] = index[aid].get(ym, 0) + vol

print(f"\nAssets with any production: {len(index):,}")
total_entries = sum(len(v) for v in index.values())
print(f"Total (asset, month) entries: {total_entries:,}")

print(f"Writing {OUT_FILE} ...")
with open(OUT_FILE, "w") as f:
    json.dump(index, f, separators=(",", ":"))

size_mb = os.path.getsize(OUT_FILE) / 1024 / 1024
print(f"Done. File size: {size_mb:.1f} MB")
