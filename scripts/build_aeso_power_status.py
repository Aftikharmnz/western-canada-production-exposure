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
    python -m pip install -r scripts/requirements-aeso.txt
    python scripts/build_aeso_power_status.py

In CI this runs on a 30-minute GitHub Actions schedule
(.github/workflows/refresh-aeso-power.yml), so the published site updates
automatically with no manual steps.
"""

from __future__ import annotations

import argparse
import csv
import http.client
import io
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "data" / "aeso_power_status.json"
# AESO's legacy public CSV endpoint does not negotiate HTTPS (verified 2026-09).
# No credentials are transmitted. Validate schema and observation age before publishing.
CSD_URL = "http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet?contentType=csv"
MAX_REPORT_BYTES = 512 * 1024
MAX_ATTEMPTS = 3
RETRY_HTTP_CODES = {408, 429, 500, 502, 503, 504}
SYSTEM_FIELDS = {
    "Alberta Internal Load (AIL)", "Alberta Total Net Generation",
    "Net Actual Interchange", "Net-To-Grid Generation",
    "Dispatched Contingency Reserve (DCR)",
}
# Use the pinned database rather than a runner's potentially older system rules.
# Alberta stays on UTC-6 from November 2026; stale rules would misdate the report.
with files("tzdata.zoneinfo").joinpath("America/Edmonton").open("rb") as zone_file:
    OBSERVATION_ZONE = ZoneInfo.from_file(zone_file, key="America/Edmonton")

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
        payload = response.read(MAX_REPORT_BYTES + 1)
    if len(payload) > MAX_REPORT_BYTES:
        raise ValueError("AESO response exceeds the report size limit")
    return payload.decode("utf-8-sig")


def to_num(value: str):
    try:
        number = float(str(value).strip().replace(",", ""))
        return number if math.isfinite(number) else None
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
            # Some AESO CSV blocks omit their HTML fuel heading. A blank block
            # boundary must not label subsequent wind/hydro units as gas steam.
            section = None
            continue
        cell = row[0].strip()
        m = re.match(r"^<center><b>(.+?)</b></center>$", cell)
        if m:
            section = m.group(1).strip()
            continue
        if cell.startswith("Last Update"):
            stamp = ",".join(part for part in row if part.strip()).strip()
            last_update = stamp.split(":", 1)[1].strip() if ":" in stamp else stamp
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
                    "mc_mw": to_num(row[1]),
                    "tng_mw": to_num(row[2]),
                    "dcr_mw": to_num(row[3]),
                    "net_to_grid": "*" in cell,
                })
            elif cell.isupper():
                groups.append({"group": cell.title(), "mc_mw": to_num(row[1]), "tng_mw": to_num(row[2])})
    return {"system": system, "last_update": last_update, "groups": groups, "assets": assets}


def validate_report(parsed: dict) -> None:
    if (not parsed["assets"] or not parsed["last_update"]
            or not SYSTEM_FIELDS.issubset(parsed["system"])):
        raise ValueError("AESO response is incomplete; preserving the last valid snapshot")
    codes = [row["code"] for row in parsed["assets"]]
    if len(codes) != len(set(codes)):
        raise ValueError("AESO response has duplicate unit codes")
    groups = {row["group"]: row for row in parsed["groups"]}
    if len(groups) != len(parsed["groups"]) or "Total" not in groups:
        raise ValueError("AESO fuel summary is missing or duplicated")
    capacities = [row["mc_mw"] for row in parsed["assets"]]
    total = groups["Total"]["mc_mw"]
    if (total is None or total <= 0 or any(mc is None or mc < 0 for mc in capacities)
            or not math.isclose(sum(capacities), total, rel_tol=1e-6, abs_tol=1)):
        raise ValueError("AESO unit capacities do not match the report total; response may be truncated")
    if any(row["mc_mw"] is None or row["tng_mw"] is None for row in groups.values()):
        raise ValueError("AESO fuel summary contains missing readings")


def observation_time(stamp: str, now: datetime) -> datetime:
    wall = datetime.strptime(stamp, "%b %d, %Y %H:%M")
    zone = OBSERVATION_ZONE
    candidates = []
    for fold in (0, 1):
        observed = wall.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
        # Reject nonexistent local times during the spring clock change.
        if observed.astimezone(zone).replace(tzinfo=None) != wall:
            continue
        age = (now - observed).total_seconds()
        if -300 <= age <= 90 * 60:
            candidates.append(observed)
    if not candidates:
        raise ValueError("AESO report is stale or future-dated; preserving the last valid snapshot")
    # The source omits its UTC offset. During the autumn repeated hour use the
    # nearest plausible occurrence instead of making fresh data an hour older.
    return min(candidates, key=lambda observed: abs((now - observed).total_seconds()))


def build_snapshot(text: str) -> dict:
    parsed = parse_csd(text)
    validate_report(parsed)
    now = datetime.now(timezone.utc)
    observed = observation_time(parsed["last_update"], now)
    by_code = {a["code"]: a for a in parsed["assets"]}

    site_cogen = []
    for entry in SITE_COGEN_SITES:
        units = [by_code[c] for c in entry["codes"] if c in by_code]
        complete = len(units) == len(entry["codes"]) and all(
            u["mc_mw"] is not None and u["mc_mw"] > 0 and u["tng_mw"] is not None
            and (u["tng_mw"] >= 0 or u["net_to_grid"]) for u in units)
        mc = sum(u["mc_mw"] for u in units) if complete else None
        tng = sum(u["tng_mw"] for u in units) if complete else None
        site_cogen.append({
            "aeso_code": "+".join(entry["codes"]),
            "aeso_name": " + ".join(u["name"] for u in units) or "AESO reading unavailable",
            "site": entry["site"],
            "operator": entry["operator"],
            "asset_names": entry.get("asset_names") or [],
            "lat": entry["lat"],
            "lon": entry["lon"],
            "mc_mw": mc,
            "tng_mw": tng,
            "utilization": round(tng / mc, 3) if mc else None,
            "net_to_grid": any(u["net_to_grid"] for u in units),
            "complete": complete,
            "atco_heritage": bool(entry.get("atco")),
        })
    site_cogen.sort(key=lambda x: -(x["tng_mw"] or 0))

    atco_fleet = []
    for code, label in ATCO_FLEET_CODES.items():
        a = by_code.get(code)
        if not a:
            continue
        atco_fleet.append({
            "aeso_code": code, "name": label, "fuel": a["fuel"],
            "mc_mw": a["mc_mw"], "tng_mw": a["tng_mw"],
            "utilization": round(a["tng_mw"] / a["mc_mw"], 3) if a["mc_mw"] and a["tng_mw"] is not None else None,
        })
    atco_fleet.sort(key=lambda x: -(x["tng_mw"] or 0))

    sysm = parsed["system"]
    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "observed_at": observed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": CSD_URL,
        "aeso_last_update": parsed["last_update"],
        "aeso_asset_count": len(parsed["assets"]),
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


def build() -> dict:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return build_snapshot(fetch_csd())
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY_HTTP_CODES:
                raise
            failure = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                http.client.HTTPException, ValueError, csv.Error) as exc:
            failure = exc
        if attempt == MAX_ATTEMPTS:
            raise failure
        delay = 2 ** attempt
        print(f"warning: AESO attempt {attempt}/{MAX_ATTEMPTS} failed: {failure}; retrying in {delay}s", file=sys.stderr)
        time.sleep(delay)
    raise RuntimeError("AESO download attempts exhausted")


def write_snapshot(data: dict, output: Path) -> None:
    # A stale source replica must not move the published observation backwards.
    if output.exists():
        try:
            previous = json.loads(output.read_text(encoding="utf-8"))
            previous_stamp = previous.get("observed_at") if isinstance(previous, dict) else None
            if previous_stamp and datetime.fromisoformat(previous_stamp.replace("Z", "+00:00")) > datetime.fromisoformat(data["observed_at"].replace("Z", "+00:00")):
                raise RuntimeError("AESO observation predates the published snapshot; preserving the newer reading")
        except (ValueError, TypeError, AttributeError):
            # An unreadable previous JSON can be replaced by a validated report.
            pass
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    try:
        data = build()
        write_snapshot(data, args.output)
    except (OSError, ValueError, RuntimeError, http.client.HTTPException, csv.Error) as exc:
        print(f"error: AESO refresh failed: {exc}. The last valid snapshot has been retained.", file=sys.stderr)
        if summary:
            with open(summary, "a", encoding="utf-8") as file:
                file.write(f"### AESO power refresh\n\nFailed: {exc}. The last valid snapshot was retained.\n")
        return 1
    print(f"Wrote {args.output.name}: {len(data['site_cogen'])} site cogens, "
          f"{len(data['atco_fleet'])} ATCO-fleet units, AIL {data['system']['alberta_internal_load_mw']} MW", file=sys.stderr)
    if summary:
        missing = sum(not row["complete"] for row in data["site_cogen"])
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"### AESO power refresh\n\nSource observation: {data['observed_at']}. "
                       f"Validated {data['aeso_asset_count']} generation units. "
                       f"{missing} site readings are incomplete and remain unknown.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
