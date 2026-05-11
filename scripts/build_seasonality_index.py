"""
build_seasonality_index.py
Pre-aggregates all monthly Petrinex files into a compact lookup:
  { asset_id: { "YYYY-MM": kbbl_d, ... }, ... }
Handles compact format: [{"date":...,"rows":[[aid,vol],...]}]
and legacy format:      [{"asset_id":...,"volume_kbbl_d":...,"date":...}]
Output: public/data/asset_seasonality.json
"""
import json, glob, os

BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHLY_DIR = os.path.join(BASE, "public", "data", "monthly")
ASSETS_FILE = os.path.join(BASE, "public", "data", "assets.json")
OUT_FILE    = os.path.join(BASE, "public", "data", "asset_seasonality.json")

print("Loading assets...")
with open(ASSETS_FILE) as f:
    assets = json.load(f)
mapped_ids = {a["asset_id"] for a in assets if a.get("latitude") and a.get("longitude")}
print(f"  Mapped assets: {len(mapped_ids):,}")

files = sorted(glob.glob(os.path.join(MONTHLY_DIR, "*.json")))
print(f"Loading {len(files)} monthly files...")

index = {}

def add_entry(aid, ym_str, vol):
    if not aid or aid not in mapped_ids:
        return
    if not vol or vol <= 0:
        return
    if not ym_str:
        return
    if aid not in index:
        index[aid] = {}
    index[aid][ym_str] = index[aid].get(ym_str, 0) + vol

for i, fpath in enumerate(files):
    fname = os.path.basename(fpath)
    print(f"  [{i+1}/{len(files)}] {fname}", end="\r", flush=True)
    with open(fpath) as f:
        records = json.load(f)
    for r in records:
        if "rows" in r:
            ym_str = r.get("date", "")[:7]
            for row in r.get("rows", []):
                if len(row) >= 2:
                    add_entry(row[0], ym_str, row[1])
        else:
            add_entry(r.get("asset_id"), r.get("date", "")[:7], r.get("volume_kbbl_d"))

print()
print(f"Assets with any production: {len(index):,}")
total_entries = sum(len(v) for v in index.values())
print(f"Total (asset, month) entries: {total_entries:,}")
conv = sum(1 for k in index if "conventional" in k)
c5   = sum(1 for k in index if "pentanes_plus" in k)
cond = sum(1 for k in index if "condensate" in k)
print(f"  Conventional: {conv:,}  Pentanes plus: {c5:,}  Condensate: {cond:,}")

print(f"Writing {OUT_FILE} ...")
with open(OUT_FILE, "w") as f:
    json.dump(index, f, separators=(",", ":"))

size_mb = os.path.getsize(OUT_FILE) / 1024 / 1024
print(f"Done. File size: {size_mb:.1f} MB")
