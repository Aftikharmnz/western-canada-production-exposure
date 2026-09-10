"""
News-alert checker for the production-exposure app.

Runs after each AESO snapshot refresh in GitHub Actions. Detects:
  1. Power transitions at monitored sites — cogen utilization falling below
     the down-threshold (confirmed over N consecutive runs) or recovering
     above the recover-threshold. Thresholds in data/alerts/config.json.
  2. New active wildfires within radius_km of ANY mapped production asset,
     using the Government of Alberta (Alberta Wildfire) and Government of
     B.C. (BC Wildfire Service) feeds only — no satellite hotspot data.
     Escalates when a nearby fire goes Out of Control; closes out when it
     is brought under control or extinguished.

State lives in data/alerts/state.json (committed by the workflow) so alerts
fire on transitions only, never repeats. The very first run baselines
existing conditions without emailing, to avoid an alert storm.

Email: Resend API if RESEND_API_KEY is set (recipients in ALERT_EMAILS,
comma-separated). Falls back to SMTP if SMTP_HOST/SMTP_USER/SMTP_PASS are
set. With neither, alerts are printed to the log only.
"""

from __future__ import annotations

import json
import math
import html
import os
import smtplib
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "alerts" / "config.json"
STATE_PATH = ROOT / "data" / "alerts" / "state.json"
POWER_PATH = ROOT / "public" / "data" / "aeso_power_status.json"
ASSETS_PATH = ROOT / "public" / "data" / "assets.json"

AB_FIRES_URL = (
    "https://services.arcgis.com/Eb8P5h4CJk8utIBz/arcgis/rest/services/"
    "Active_Wildfires_(PROD)/FeatureServer/0/query"
)
BC_FIRES_URL = (
    "https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/"
    "BCWS_ActiveFires_PublicView/FeatureServer/0/query"
)

OOC_STATUSES = {"out of control", "ooc"}
CONTAINED_STATUSES = {"under control", "uc", "out", "being held", "bh", "extinguished"}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "western-canada-production-exposure/alerts"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    if (not isinstance(data, dict) or data.get("error") or data.get("exceededTransferLimit")
            or (data.get("properties") or {}).get("exceededTransferLimit")
            or not isinstance(data.get("features"), list)):
        raise ValueError("Fire source returned an error, truncated response, or invalid schema")
    return data


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def valid_coordinates(lat, lon):
    if lat is None or lon is None or isinstance(lat, bool) or isinstance(lon, bool):
        return None
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def normalize_fires(data, prefix, source, size_field):
    rows = []
    for feature in data["features"]:
        a = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(a, dict) or not a.get("FIRE_NUMBER") or not str(a.get("FIRE_STATUS") or "").strip():
            raise ValueError("Fire record is missing an identity or status")
        coordinates = valid_coordinates(a.get("LATITUDE"), a.get("LONGITUDE"))
        rows.append({
            "id": f"{prefix}-{a['FIRE_NUMBER']}", "source": source,
            "status": str(a["FIRE_STATUS"]).strip(), "size_ha": a.get(size_field),
            # Preserve the identity of an active fire whose coordinates are unavailable.
            # Dropping that identity would falsely retire its existing alert state.
            "lat": coordinates[0] if coordinates else None,
            "lon": coordinates[1] if coordinates else None,
        })
    return rows


def fetch_fires() -> tuple[list[dict], set[str]]:
    fires = []
    successful_sources = set()
    ab_params = urllib.parse.urlencode({
        "where": "FIRE_STATUS <> 'Extinguished'",
        "outFields": "FIRE_NUMBER,FIRE_STATUS,AREA_ESTIMATE,LATITUDE,LONGITUDE,FIRE_TYPE,GENERAL_CAUSE",
        "returnGeometry": "false", "f": "json",
    })
    try:
        data = fetch_json(f"{AB_FIRES_URL}?{ab_params}")
        rows = normalize_fires(data, "AB", "Alberta Wildfire (Gov. of Alberta)", "AREA_ESTIMATE")
        fires.extend(rows)
        successful_sources.add("AB")
    except Exception as exc:  # noqa: BLE001
        print(f"warning: Alberta Wildfire feed failed: {exc}", file=sys.stderr)

    bc_params = urllib.parse.urlencode({
        "where": "FIRE_STATUS <> 'Out'",
        "outFields": "FIRE_NUMBER,INCIDENT_NAME,FIRE_STATUS,CURRENT_SIZE,LATITUDE,LONGITUDE",
        "returnGeometry": "false", "f": "json",
    })
    try:
        data = fetch_json(f"{BC_FIRES_URL}?{bc_params}")
        rows = normalize_fires(data, "BC", "BC Wildfire Service (Gov. of B.C.)", "CURRENT_SIZE")
        fires.extend(rows)
        successful_sources.add("BC")
    except Exception as exc:  # noqa: BLE001
        print(f"warning: BC Wildfire feed failed: {exc}", file=sys.stderr)
    return fires, successful_sources


def load_asset_points() -> list[tuple[float, float, str]]:
    raw = load_json(ASSETS_PATH, None)
    if raw is None:
        return []
    if isinstance(raw, dict) and "fields" in raw:
        assets = [dict(zip(raw["fields"], row)) for row in raw["rows"]]
    else:
        assets = raw
    points = []
    for a in assets:
        coordinates = valid_coordinates(a.get("latitude"), a.get("longitude"))
        if not coordinates:
            continue
        points.append((*coordinates, str(a.get("display_name") or a.get("asset_id") or "asset")))
    return points


def build_grid(points, cell_deg=0.25):
    grid: dict[tuple[int, int], list] = {}
    for lat, lon, name in points:
        grid.setdefault((int(lat / cell_deg), int(lon / cell_deg)), []).append((lat, lon, name))
    return grid, cell_deg


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_asset(grid, cell_deg, lat, lon, radius_km):
    ci, cj = int(lat / cell_deg), int(lon / cell_deg)
    lat_cells = math.ceil(radius_km / 110.5 / cell_deg) + 1
    lon_cells = math.ceil(radius_km / (111.32 * max(0.01, abs(math.cos(math.radians(lat))))) / cell_deg) + 1
    best = None
    for di in range(-lat_cells, lat_cells + 1):
        for dj in range(-lon_cells, lon_cells + 1):
            for alat, alon, name in grid.get((ci + di, cj + dj), []):
                d = haversine_km(lat, lon, alat, alon)
                if d <= radius_km and (best is None or d < best[0]):
                    best = (d, name)
    return best


def observation_time(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None
    except (AttributeError, ValueError, TypeError):
        return None


def check_power(power, state, cfg, alerts):
    # A recent fetch time cannot establish the age of the underlying measurement.
    observed = observation_time(power.get("observed_at"))
    if observed is None:
        return
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    previous = observation_time(state.get("power_observation"))
    if age < -300 or age > 90 * 60 or (previous is not None and observed <= previous):
        return
    state["power_observation"] = observed.isoformat()
    down, up, confirm = cfg["down_threshold"], cfg["recover_threshold"], cfg["confirm_runs"]
    sites = state.setdefault("power_sites", {})
    first_run = not sites
    if previous is None or (observed - previous).total_seconds() > 90 * 60:
        for st in sites.values():
            st["runs_below"] = st["runs_above"] = 0
    seen = set()
    for s in power.get("site_cogen", []):
        u = s.get("utilization")
        key = s.get("site")
        if not key or key in seen:
            continue
        seen.add(key)
        if (s.get("net_to_grid") or s.get("complete") is False or isinstance(u, bool)
                or not isinstance(u, (int, float)) or not math.isfinite(u) or u < 0):
            if key in sites:
                sites[key]["runs_below"] = sites[key]["runs_above"] = 0
            continue
        st = sites.setdefault(key, {"status": "unknown", "runs_below": 0, "runs_above": 0})
        if st["status"] == "unknown":
            st["status"] = "reduced" if u < down else "normal"
            st["runs_below"] = st["runs_above"] = 0
            continue
        if u < down:
            st["runs_below"] += 1
            st["runs_above"] = 0
            if st["status"] != "reduced" and st["runs_below"] >= confirm:
                st["status"] = "reduced"
                alerts.append({
                    "kind": "power-down",
                    "title": f"Power down: {key} cogen at {u * 100:.0f}% of capability",
                    "detail": (f"{key} ({s['operator']}) — AESO unit {s['aeso_name']} generating "
                               f"{s['tng_mw']} MW of {s['mc_mw']} MW capability "
                               f"({u * 100:.0f}%), below the {down * 100:.0f}% alert threshold "
                               f"for {confirm} consecutive checks (~{confirm * 30} min)."),
                })
        elif u >= up:
            st["runs_above"] += 1
            st["runs_below"] = 0
            if st["status"] == "reduced" and st["runs_above"] >= confirm:
                st["status"] = "normal"
                alerts.append({
                    "kind": "power-recovered",
                    "title": f"Power recovered: {key} back to {u * 100:.0f}%",
                    "detail": (f"{key} ({s['operator']}) — cogen output back to {s['tng_mw']} MW "
                               f"of {s['mc_mw']} MW ({u * 100:.0f}%), above the "
                               f"{up * 100:.0f}% recovery threshold."),
                })
        else:
            st["runs_below"] = 0
            st["runs_above"] = 0
    for key, st in sites.items():
        if key not in seen:
            st["runs_below"] = st["runs_above"] = 0
    if first_run:
        alerts_note = "baseline established for power sites (no alerts on first run)"
        print(alerts_note, file=sys.stderr)


def check_fires(fires, grid, cell_deg, state, cfg, alerts, successful_sources=None):
    radius = cfg["radius_km"]
    successful_sources = {"AB", "BC"} if successful_sources is None else successful_sources
    known = state.setdefault("fires", {})
    baselined = set(state.get("fire_sources_baselined", ["AB", "BC"] if state.get("fires_baselined") else []))
    for f in fires:
        coordinates = valid_coordinates(f.get("lat"), f.get("lon"))
        if coordinates is None:
            continue
        hit = nearest_asset(grid, cell_deg, *coordinates, radius)
        if not hit:
            continue
        dist, asset_name = hit
        status_l = f["status"].lower()
        prev = known.get(f["id"])
        size = f" · {f['size_ha']} ha" if f.get("size_ha") not in (None, 0) else ""
        if prev is None:
            known[f["id"]] = {"status": f["status"], "asset": asset_name, "dist_km": round(dist, 1)}
            if f["id"].split("-", 1)[0] in baselined:
                alerts.append({
                    "kind": "fire-new",
                    "title": f"New fire {f['id']} {dist:.1f} km from {asset_name}",
                    "detail": (f"{f['source']}: fire {f['id']} ({f['status']}{size}) is "
                               f"{dist:.1f} km from mapped asset \"{asset_name}\" "
                               f"(alert radius {radius} km)."),
                })
        else:
            prev_status = str(prev.get("status", "")).lower()
            if status_l in OOC_STATUSES and prev_status not in OOC_STATUSES:
                alerts.append({
                    "kind": "fire-escalated",
                    "title": f"Fire {f['id']} now OUT OF CONTROL near {asset_name}",
                    "detail": (f"{f['source']}: fire {f['id']}{size} escalated to "
                               f"'{f['status']}', {prev.get('dist_km', dist):.1f} km from \"{asset_name}\"."),
                })
            elif status_l in CONTAINED_STATUSES and prev_status not in CONTAINED_STATUSES:
                alerts.append({
                    "kind": "fire-contained",
                    "title": f"Fire {f['id']} contained ({f['status']}) near {asset_name}",
                    "detail": (f"{f['source']}: fire {f['id']} near \"{asset_name}\" is now "
                               f"'{f['status']}'."),
                })
            prev["status"] = f["status"]
    # Drop fires that left the feeds (extinguished/out)
    active_ids = {f["id"] for f in fires}
    for fid in list(known.keys()):
        if fid not in active_ids and fid.split("-", 1)[0] in successful_sources:
            del known[fid]
    baselined.update(successful_sources)
    state["fire_sources_baselined"] = sorted(baselined)
    state["fires_baselined"] = bool(baselined)


def send_email(alerts, cfg) -> str:
    recipients = [e.strip() for e in os.environ.get("ALERT_EMAILS", "").split(",") if e.strip()]
    if not recipients:
        return "no ALERT_EMAILS configured — logged only"
    subject = f"[WCPE Alert] {alerts[0]['title']}" if len(alerts) == 1 else \
        f"[WCPE Alert] {len(alerts)} alerts: " + "; ".join(a["title"] for a in alerts[:3])
    app_url = cfg.get("app_url", "")
    body_html = "<h3>Western Canada Production Exposure — alerts</h3>" + "".join(
        f"<p><strong>{html.escape(a['title'])}</strong><br>{html.escape(a['detail'])}</p>" for a in alerts
    ) + f'<p style="color:#667">Checked {now_utc()}. <a href="{html.escape(app_url, quote=True)}">Open the map</a>. ' \
        "Power figures are AESO cogeneration output (a site power-status proxy, not metered load).</p>"

    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_key:
        payload = json.dumps({
            "from": os.environ.get("ALERT_FROM", "WCPE Alerts <onboarding@resend.dev>"),
            "to": recipients,
            "subject": subject,
            "html": body_html,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails", data=payload, method="POST",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            return f"sent via Resend to {len(recipients)} recipient(s): {response.status}"

    host = os.environ.get("SMTP_HOST", "").strip()
    if host:
        msg = MIMEText(body_html, "html")
        msg["Subject"] = subject
        msg["From"] = os.environ.get("ALERT_FROM", os.environ.get("SMTP_USER", ""))
        msg["To"] = ", ".join(recipients)
        with smtplib.SMTP_SSL(host, int(os.environ.get("SMTP_PORT", "465")), timeout=60) as smtp:
            smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            smtp.sendmail(msg["From"], recipients, msg.as_string())
        return f"sent via SMTP to {len(recipients)} recipient(s)"
    return "no email transport configured (set RESEND_API_KEY or SMTP_*) — logged only"


def main() -> int:
    cfg = load_json(CONFIG_PATH, {})

    if os.environ.get("ALERT_TEST", "").lower() == "true":
        print("TEST MODE: sending a delivery-check email", file=sys.stderr)
        test_alert = [{
            "kind": "test",
            "title": "Test alert — email delivery check",
            "detail": (f"This is a test of the alert pipeline sent at {now_utc()}. "
                       "If you are reading this, Resend credentials and the recipient "
                       "list are working. No real event occurred."),
        }]
        try:
            print(send_email(test_alert, cfg), file=sys.stderr)
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"error: test email failed: {exc}", file=sys.stderr)
            return 1

    power_cfg = cfg.get("power", {"down_threshold": 0.20, "recover_threshold": 0.50, "confirm_runs": 2})
    fire_cfg = cfg.get("fire", {"radius_km": 10})
    state = load_json(STATE_PATH, {})
    alerts: list[dict] = []

    power = load_json(POWER_PATH, {})
    if power:
        check_power(power, state, power_cfg, alerts)
    else:
        print("warning: power snapshot missing", file=sys.stderr)

    points = load_asset_points()
    if points:
        grid, cell = build_grid(points)
        fires, successful_sources = fetch_fires()
        print(f"assets: {len(points)}, active gov fires: {len(fires)}", file=sys.stderr)
        check_fires(fires, grid, cell, state, fire_cfg, alerts, successful_sources)
    else:
        print("warning: assets.json missing/empty — fire check skipped", file=sys.stderr)

    state["last_check"] = now_utc()

    send_failed = False
    if alerts:
        for a in alerts:
            print(f"ALERT [{a['kind']}] {a['title']}\n  {a['detail']}", file=sys.stderr)
        try:
            print(send_email(alerts, cfg), file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"error: email send failed: {exc}", file=sys.stderr)
            send_failed = True
    else:
        print("no alerts this run", file=sys.stderr)

    if send_failed:
        # Do NOT persist state: the transitions remain un-acknowledged, so the
        # next run re-detects them and retries the email instead of losing it.
        print("state not persisted; alerts will retry next run", file=sys.stderr)
        return 1

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
