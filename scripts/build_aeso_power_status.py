"""
Build the AESO/ATCO power-status snapshot for the map's Power overlay.

Fetches the public AESO Current Supply Demand (CSD) report — no API key —
and writes public/data/aeso_power_status.json with:
  - system-level grid metrics (Alberta load, generation, interchange)
  - generation totals by fuel group
  - oil-sands / refining site cogeneration units linked to map coordinates
    (generation as a power-status proxy for the site)
  - the ATCO-heritage (Heartland Generation) merchant fleet

Run locally:
    python scripts/build_aeso_power_status.py

In CI this runs on a 30-minute GitHub Actions schedule
(.github/workflows/refresh-aeso-power.yml), so the published site updates
automatically with no manual steps.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "data" / "aeso_power_status.json"
CSD_URL = "http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet?contentType=csv"

# Production-site links. Each site may aggregate several AESO cogen units
# (e.g. Suncor Base Plant + Poplar Creek). `asset_names` are display names in
# the app's assets.json — the front end snaps the halo to that asset marker's
# exact coordinates so the ring sits around the site's circle on the map;
# lat/lon here are fallbacks only.
SITE_COGEN_SITES: list[dict] = [
    {"codes": ["SCR1", "SCR5"], "site": "Suncor Base Plant", "operator": "Suncor",
     "asset_names": ["Suncor Base Plant Upgrader"], "lat": 56.9464, "lon": -111.2969},
    {"codes": ["SCR6"], "site": "Firebag SAGD", "operator": "Suncor",
     "asset_names": ["Firebag"], "lat": 57.2308, "lon": -110.8666},
    {"codes": ["FH1"], "site": "Fort Hills Mine", "operator": "Suncor",
     "asset_names": ["Fort Hills Mine"], "lat": 57.4246, "lon": -111.5231},
    {"codes": ["MKRC"], "site": "MacKay River SAGD", "operator": "Suncor (cogen)",
     "asset_names": ["MacKay River"], "lat": 56.8291, "lon": -112.1825},
    {"codes": ["CNR5"], "site": "CNRL Horizon", "operator": "CNRL",
     "asset_names": ["CNRL Horizon", "Horizon Upgrader"], "lat": 57.3503, "lon": -111.8130},
    {"codes": ["SCL1"], "site": "Syncrude Mildred Lake", "operator": "Syncrude JV",
     "asset_names": ["Syncrude Mildred Lake Upgrader", "Syncrude Mildred Lake"], "lat": 57.0627, "lon": -111.5383},
    {"codes": ["MKR1"], "site": "Muskeg River Mine", "operator": "Heartland (ex-ATCO) / AOSP",
     "asset_names": ["Muskeg River Mine"], "lat": 57.2375, "lon": -111.5221, "atco": True},
    {"codes": ["IOR3"], "site": "Kearl Mine", "operator": "Imperial Oil",
     "asset_names": ["Kearl Mine"], "lat": 57.3567, "lon": -111.0995},
    {"codes": ["IOR1", "IOR2"], "site": "Cold Lake (Imperial)", "operator": "Imperial Oil",
     "asset_names": ["Cold Lake"], "lat": 54.6619, "lon": -110.4221},
    {"codes": ["IOR4"], "site": "Strathcona Refinery", "operator": "Imperial Oil",
     "asset_names": [], "lat": 53.4920, "lon": -113.3600},
    {"codes": ["CL01"], "site": "Christina Lake SAGD (Cenovus)", "operator": "Cenovus",
     "asset_names": ["Christina Lake"], "lat": 55.5560, "lon": -110.8159},
    {"codes": ["EC04"], "site": "Foster Creek SAGD", "operator": "Cenovus",
     "asset_names": ["Foster Creek"], "lat": 55.0804, "lon": -110.6417},
    {"codes": ["MEG1"], "site": "Christina Lake SAGD (MEG)", "operator": "MEG Energy",
     "asset_names": ["Christina Lake (MEG)"], "lat": 55.6681, "lon": -110.7497},
    {"codes": ["NX01"], "site": "Long Lake Upgrader", "operator": "CNOOC/Nexen",
     "asset_names": ["Long Lake Upgrader"], "lat": 56.4117, "lon": -110.9376},
    {"codes": ["NX02"], "site": "Long Lake SAGD", "operator": "CNOOC/Nexen",
     "asset_names": ["Long Lake"], "lat": 56.3625, "lon": -110.9607},
    {"codes": ["PR1"], "site": "Primrose / Wolf Lake", "operator": "CNRL",
     "asset_names": ["Primrose and Wolf Lake"], "lat": 54.7931, "lon": -110.6100},
    {"codes": ["PEC1"], "site": "Lindbergh SAGD", "operator": "Strathcona Resources",
     "asset_names": ["Lindbergh"], "lat": 54.0558, "lon": -110.5836},
    {"codes": ["APS1", "ALS1"], "site": "Shell Scotford complex", "operator": "Shell / Air Products / Air Liquide",
     "asset_names": ["Scotford Upgrader"], "lat": 53.7942, "lon": -113.1088},
]

# ATCO-heritage merchant fleet (operated by Heartland Generation since 2019).
ATCO_FLEET_CODES = {
    "BR4": "Battle River #4", "BR5": "Battle River #5",
    "SH1": "Sheerness #1", "SH2": "Sheerness #2",
    "HRM": "H.R. Milner", "PH1": "Poplar Hill #1",
    "RB5": "Rainbow #5", "VVW1": "Valley View 1", "VVW2": "Valley View 2",
}

ASSET_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<code>[A-Z0-9]+)\)[\*\^]*$")


def fetch_csd() -> str:
    req = urllib.request.Request(CSD_URL, headers={"User-Agent": "western-canada-production-exposure/power-status"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def to_num(value: str):
    try:
        return float(value) if "." in value else int(value)
    except (TypeError, ValueError):
        return None


def parse_csd(text: str) -> dict:
    rows = list(csv.reader(io.StringIO(text)))
    system: dict[str, float] = {}
    last_update = None
    groups: list[dict] = []
    assets: list[dict] = []
    section = None

    for row in rows:
        if not row or not row[0].strip():
            continue
        cell = row[0].strip()
        m = re.match(r"^<center><b>(.+?)</b></center>$", cell)
        if m:
            section = m.group(1).strip()
            continue
        if cell.startswith("Last Update"):
            last_update = cell.split(":", 1)[1].strip() if ":" in cell else cell
            continue
        if len(row) == 2 and to_num(row[1]) is not None:
            system[cell] = to_num(row[1])
            continue
        if len(row) == 4:
            if cell == "ASSET":
                continue
            am = ASSET_RE.match(cell)
            if am:
                assets.append({
                    "name": am.group("name"),
                    "code": am.group("code"),
                    "fuel": section or "Unknown",
                    "mc_mw": to_num(row[1]) or 0,
                    "tng_mw": to_num(row[2]) or 0,
                    "dcr_mw": to_num(row[3]) or 0,
                })
            elif cell.isupper():
                groups.append({"group": cell.title(), "mc_mw": to_num(row[1]) or 0, "tng_mw": to_num(row[2]) or 0})
    return {"system": system, "last_update": last_update, "groups": groups, "assets": assets}


def build() -> dict:
    parsed = parse_csd(fetch_csd())
    by_code = {a["code"]: a for a in parsed["assets"]}

    site_cogen = []
    for entry in SITE_COGEN_SITES:
        units = [by_code[c] for c in entry["codes"] if c in by_code]
        if not units:
            continue
        mc = sum(u["mc_mw"] for u in units)
        tng = sum(u["tng_mw"] for u in units)
        site_cogen.append({
            "aeso_code": "+".join(u["code"] for u in units),
            "aeso_name": " + ".join(u["name"] for u in units),
            "site": entry["site"],
            "operator": entry["operator"],
            "asset_names": entry.get("asset_names") or [],
            "lat": entry["lat"],
            "lon": entry["lon"],
            "mc_mw": mc,
            "tng_mw": tng,
            "utilization": round(tng / mc, 3) if mc else None,
            "atco_heritage": bool(entry.get("atco")),
        })
    site_cogen.sort(key=lambda x: -x["tng_mw"])

    atco_fleet = []
    for code, label in ATCO_FLEET_CODES.items():
        a = by_code.get(code)
        if not a:
            continue
        atco_fleet.append({
            "aeso_code": code, "name": label, "fuel": a["fuel"],
            "mc_mw": a["mc_mw"], "tng_mw": a["tng_mw"],
            "utilization": round(a["tng_mw"] / a["mc_mw"], 3) if a["mc_mw"] else None,
        })
    atco_fleet.sort(key=lambda x: -x["tng_mw"])

    sysm = parsed["system"]
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": CSD_URL,
        "aeso_last_update": parsed["last_update"],
        "system": {
            "alberta_internal_load_mw": sysm.get("Alberta Internal Load (AIL)"),
            "total_net_generation_mw": sysm.get("Alberta Total Net Generation"),
            "net_actual_interchange_mw": sysm.get("Net Actual Interchange"),
            "net_to_grid_generation_mw": sysm.get("Net-To-Grid Generation"),
            "dispatched_contingency_reserve_mw": sysm.get("Dispatched Contingency Reserve (DCR)"),
        },
        "groups": parsed["groups"],
        "site_cogen": site_cogen,
        "atco_fleet": atco_fleet,
        "notes": [
            "Site cogeneration output (TNG vs max capability MC) is a public power-status proxy for the linked production site, not metered facility consumption.",
            "ATCO-heritage fleet units are operated by Heartland Generation following the 2019 ATCO Power sale.",
        ],
    }


def main() -> int:
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(data['site_cogen'])} site cogens, "
          f"{len(data['atco_fleet'])} ATCO-fleet units, AIL {data['system']['alberta_internal_load_mw']} MW", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
