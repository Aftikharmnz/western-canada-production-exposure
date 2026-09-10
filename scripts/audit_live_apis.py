"""Read-only public API checks. Writes no source data and sends no alerts."""
from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def endpoints():
    source = (ROOT / "src/main.js").read_text(encoding="utf-8")
    for name in ["CWFIS_URL", "BC_FIRES_URL", "ALBERTA_FIRES_URL", "ALBERTA_MUNICIPAL_URL", "ALBERTA_MUTUAL_AID_URL"]:
        expression = re.search(rf"const {name}\s*=([\s\S]*?);", source).group(1)
        yield name, "".join(json.loads(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', expression)), "geojson"
    now = datetime.now(timezone.utc)
    for variable in ["WindDir", "WindSpeed"]:
        params = urllib.parse.urlencode({"f": "json", "bbox": "-114,55,-110,59", "variable": variable,
            "datetime": f"{(now-timedelta(hours=1)).isoformat()}/{(now+timedelta(hours=3)).isoformat()}", "limit": 700})
        yield "ECCC_" + variable, "https://api.weather.gc.ca/collections/prognos-rdps-realtime/items?" + params, "geojson"
    yield "Open-Meteo", "https://api.open-meteo.com/v1/forecast?latitude=57&longitude=-112&current=wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=UTC", "weather"
    yield "Leaflet", "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", "javascript"
    for layer in ["World_Topo_Map", "Canvas/World_Dark_Gray_Base", "Canvas/World_Dark_Gray_Reference"]:
        yield layer, f"https://server.arcgisonline.com/ArcGIS/rest/services/{layer}/MapServer/tile/3/2/1", "tile"


def check(endpoint):
    name, url, kind = endpoint
    result = {"name": name, "url": url}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "WCPE-data-audit/1.0", "Origin": "https://aftikharmnz.github.io"})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read()
            result.update(http_status=response.status, content_type=response.headers.get("Content-Type"), cors=response.headers.get("Access-Control-Allow-Origin"))
        if kind in ("geojson", "weather"):
            data = json.loads(payload)
            if data.get("error"):
                raise ValueError(str(data.get("reason") or data["error"]))
            if data.get("exceededTransferLimit") or data.get("properties", {}).get("exceededTransferLimit"):
                raise ValueError("Truncated response")
            if kind == "geojson":
                if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
                    raise ValueError("Invalid FeatureCollection")
                result["feature_count"] = len(data["features"])
                result["sample_fields"] = sorted(data["features"][0].get("properties", {})) if data["features"] else []
                if name.startswith("ECCC_"):
                    result["units"] = sorted({str(f.get("properties", {}).get("unit")) for f in data["features"]})
            elif not data.get("current") or not data.get("current_units"):
                raise ValueError("Weather values or units missing")
        elif kind == "tile" and not result["content_type"].startswith("image/"):
            raise ValueError("Invalid map tile")
        elif kind == "javascript" and b"L.version" not in payload and b"1.9.4" not in payload:
            raise ValueError("Unexpected Leaflet response")
        result["status"] = "ok"
    except Exception as exc:
        result.update(status="unavailable", error=str(exc))
    return result


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        checks = list(pool.map(check, endpoints()))
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "scope": "Browser runtime APIs and basemaps. ETL and infrastructure services are documented in the production/infrastructure audits.", "checks": checks}
    (ROOT / "public/data/api_health.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for row in checks:
        print(row["name"], row["status"], row.get("feature_count", ""), row.get("units", ""), row.get("error", ""))
    return int(any(c["status"] != "ok" for c in checks))


if __name__ == "__main__":
    raise SystemExit(main())
