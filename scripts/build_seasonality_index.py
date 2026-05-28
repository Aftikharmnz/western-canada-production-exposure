"""
build_seasonality_index.py
Pre-aggregates all production records into a compact seasonality lookup:
  { asset_id: { "YYYY-MM": kbbl_d, ... }, ... }

Sources:
  1. public/data/monthly_production.json  -- base records (oil sands, upgraders, NGL)
  2. public/data/monthly/on_demand_*.json -- AB/SK Petrinex, BC BCER, NDIC, Manitoba, Montana wells

Output: public/data/asset_seasonality.json
"""
import glob
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHLY_DIR = os.path.join(BASE, "public", "data", "monthly")
BASE_PROD_FILE = os.path.join(BASE, "public", "data", "monthly_production.json")
ASSETS_FILE = os.path.join(BASE, "public", "data", "assets.json")
OUT_FILE = os.path.join(BASE, "public", "data", "asset_seasonality.json")

print("Loading assets...")
with open(ASSETS_FILE) as f:
    assets = json.load(f)
if isinstance(assets, dict) and "fields" in assets and "rows" in assets:
    asset_fields = assets["fields"]
    asset_rows = [dict(zip(asset_fields, row)) for row in assets["rows"]]
else:
    asset_rows = assets
asset_id_by_ref = {idx: a["asset_id"] for idx, a in enumerate(asset_rows)}
mapped_ids = {a["asset_id"] for a in asset_rows if a.get("latitude") and a.get("longitude")}
print("  Mapped assets: {:,}".format(len(mapped_ids)))

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


print("Loading base records from monthly_production.json ...")
with open(BASE_PROD_FILE) as f:
    base_records = json.load(f)
for r in base_records:
    add_entry(r.get("asset_id"), r.get("date", "")[:7], r.get("volume_kbbl_d"))
print("  Base records: {:,}  ->  index assets so far: {:,}".format(len(base_records), len(index)))

files = sorted(glob.glob(os.path.join(MONTHLY_DIR, "*.json")))
print("Loading {} on-demand monthly files...".format(len(files)))
for i, fpath in enumerate(files):
    fname = os.path.basename(fpath)
    print("  [{}/{}] {}".format(i + 1, len(files), fname), end="\r", flush=True)
    with open(fpath) as f:
        payload = json.load(f)
    if isinstance(payload, dict) and "rows" in payload:
        groups = [payload]
    elif isinstance(payload, list) and payload and isinstance(payload[0], dict) and "rows" in payload[0]:
        groups = payload
    elif isinstance(payload, list):
        groups = []
        for r in payload:
            add_entry(r.get("asset_id"), r.get("date", "")[:7], r.get("volume_kbbl_d"))
    else:
        groups = []

    for group in groups:
        ym_str = group.get("date", "")[:7]
        for row in group.get("rows", []):
            if len(row) >= 2:
                aid = asset_id_by_ref.get(row[0]) if isinstance(row[0], int) else row[0]
                add_entry(aid, ym_str, row[1])

print()
print("Assets with any production: {:,}".format(len(index)))
total_entries = sum(len(v) for v in index.values())
print("Total (asset, month) entries: {:,}".format(total_entries))
insitu = sum(1 for k in index if "aer_st53" in k)
mined = sum(1 for k in index if "aer_st39" in k)
bc = sum(1 for k in index if "bcer" in k)
nd = sum(1 for k in index if "ndic" in k)
sk = sum(1 for k in index if "petrinex_sk" in k)
mb = sum(1 for k in index if "manitoba" in k)
mt = sum(1 for k in index if "montana_bogc" in k)
conv = sum(1 for k in index if "conventional" in k)
print(
    "  In-situ: {:,}  Mined/upgrader: {:,}  BC BCER: {:,}  NDIC: {:,}  SK: {:,}  MB: {:,}  MT: {:,}  Conventional-tagged: {:,}".format(
        insitu, mined, bc, nd, sk, mb, mt, conv
    )
)

print("Writing {} ...".format(OUT_FILE))
tmp_file = OUT_FILE + ".tmp"
with open(tmp_file, "w") as f:
    json.dump(index, f, separators=(",", ":"))
os.replace(tmp_file, OUT_FILE)

size_mb = os.path.getsize(OUT_FILE) / 1024 / 1024
print("Done. File size: {:.1f} MB".format(size_mb))
