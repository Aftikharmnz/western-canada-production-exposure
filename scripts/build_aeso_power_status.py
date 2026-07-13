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

# AESO asset code -> production-site link (coordinates from the app's own
# asset registry; cogen output is a power-status proxy for the site).
SITE_COGEN_LINKS: dict[str, dict] = {
    "SCR1": {"site": "Suncor Base Plant", "operator": "Suncor", "lat": 56.9464, "lon": -111.2969},
    "SCR5": {"site": "Suncor Base Plant (Poplar Creek)", "operator": "Suncor / TransAlta", "lat": 56.9390, "lon": -111.3200},
    "SCR6": {"site": "Firebag SAGD", "operator": "Suncor", "lat": 57.2308, "lon": -110.8666},
    "FH1":  {"site": "Fort Hills Mine", "operator": "Suncor", "lat": 57.4246, "lon": -111.5231},
    "MKRC": {"site": "MacKay River SAGD (Suncor)", "operator": "Suncor", "lat": 57.0500, "lon": -111.9200},
    "CNR5": {"site": "CNRL Horizon Mine/Upgrader", "operator": "CNRL", "lat": 57.3503, "lon": -111.8130},
    "SCL1": {"site": "Syncrude Mildred Lake", "operator": "Syncrude JV", "lat": 57.0564, "lon": -111.7109},
    "MKR1": {"site": "Muskeg River Mine", "operator": "Heartland (ex-ATCO) / AOSP", "lat": 57.2375, "lon": -111.5221, "atco": True},
    "IOR3": {"site": "Kearl Mine", "operator": "Imperial Oil", "lat": 57.3567, "lon": -111.0995},
    "IOR1": {"site": "Cold Lake (Mahkeses)", "operator": "Imperial Oil", "lat": 54.6619, "lon": -110.4221},
    "IOR2": {"site": "Cold Lake (Nabiye)", "operator": "Imperial Oil", "lat": 54.7000, "lon": -110.3600},
    "IOR4": {"site": "Strathcona Refinery", "operator": "Imperial Oil", "lat": 53.4920, "lon": -113.3600},
    "CL01": {"site": "Christina Lake SAGD (Cenovus)", "operator": "Cenovus", "lat": 55.5560, "lon": -110.8159},
    "EC04": {"site": "Foster Creek SAGD", "operator": "Cenovus", "lat": 55.0804, "lon": -110.6417},
    "MEG1": {"site": "Christina Lake SAGD (MEG)", "operator": "MEG Energy", "lat": 55.6681, "lon": -110.7497},
    "NX01": {"site": "Long Lake Upgrader", "operator": "CNOOC/Nexen", "lat": 56.4117, "lon": -110.9376},
    "NX02": {"site": "Long Lake SAGD", "operator": "CNOOC/Nexen", "lat": 56.3625, "lon": -110.9607},
    "PR1":  {"site": "Primrose / Wolf Lake", "operator": "CNRL", "lat": 54.7931, "lon": -110.6100},
    "PEC1": {"site": "Lindbergh SAGD", "operator": "Strathcona Resources", "lat": 54.0558, "lon": -110.5836},
    "APS1": {"site": "Scotford Upgrader (H2/cogen)", "operator": "Air Products / Shell Scotford", "lat": 53.7942, "lon": -113.1088},
    "ALS1": {"site": "Scotford (Air Liquide)", "operator": "Air Liquide / Shell Scotford", "lat": 53.8010, "lon": -113.0950},
}

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
    for code, link in SITE_COGEN_LINKS.items():
        a = by_code.get(code)
        if not a:
            continue
        mc, tng = a["mc_mw"], a["tng_mw"]
        site_cogen.append({
            "aeso_code": code,
            "aeso_name": a["name"],
            "site": link["site"],
            "operator": link["operator"],
            "lat": link["lat"],
            "lon": link["lon"],
            "mc_mw": mc,
            "tng_mw": tng,
            "utilization": round(tng / mc, 3) if mc else None,
            "atco_heritage": bool(link.get("atco")),
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
