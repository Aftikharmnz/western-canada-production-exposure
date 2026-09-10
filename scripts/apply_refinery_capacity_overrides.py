#!/usr/bin/env python3
"""Apply reviewed crude capacities and operating status, preserving source evidence.

Run after build_refinery_geojson.R. Uses only local reviewed facts, no live scraping.
An IIR plant release newer than the review is left unchanged for renewed review.
"""
import argparse
import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply_overrides(data, review):
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("Expected refinery FeatureCollection")
    checked = review["checked_at"]
    properties = {}
    for feature in data["features"]:
        p = feature["properties"]
        key = str(p["plant_id"])
        if key in properties:
            raise ValueError(f"Duplicate refinery plant ID: {key}")
        properties[key] = p
    applied, skipped = [], []
    for item in review["overrides"]:
        key = str(item["plant_id"])
        p = properties.get(key)
        if not p or p.get("plant_name") != item["plant_name"]:
            raise ValueError(f"Missing/mismatched refinery identity: {key}")
        capacity = item["capacity_bbl_d"]
        if isinstance(capacity, bool) or not isinstance(capacity, (int, float)) or not math.isfinite(capacity) or capacity <= 0:
            raise ValueError(f"Invalid reviewed capacity: {key}")
        if not item["source_url"].startswith("https://") or not item["basis"]:
            raise ValueError(f"Missing source or capacity basis: {key}")
        if str(p.get("release_date") or "")[:10] > checked:
            skipped.append(key)
            continue
        p.setdefault("original_iir_crude_capacity", {
            "crud_capacity_bbl_d": p.get("crud_capacity_bbl_d"),
            "crud_capacity_kbbl_d": p.get("crud_capacity_kbbl_d"),
            "release_date": p.get("release_date"),
        })
        p["crud_capacity_bbl_d"] = capacity
        p["crud_capacity_kbbl_d"] = capacity / 1000
        p["capacity_source_name"] = item["source_name"]
        p["capacity_source_url"] = item["source_url"]
        p["capacity_checked_at"] = checked
        p["capacity_effective_as_of"] = item.get("effective_as_of")
        p["capacity_basis_note"] = item["basis"] + ". Individual process-unit and original plant-capacity rows retain their IIR values."
        applied.append(key)
    for item in review.get("unresolved", []):
        p = properties.get(str(item["plant_id"]))
        if p:
            p["capacity_review_note"] = item["note"]
            p["capacity_review_sources"] = item["sources"]
    data["capacity_review"] = {
        "checked_at": checked,
        "overrides_applied": len(applied),
        "source_file": "data/refinery_capacity_overrides.json",
        "note": review["note"],
        "newer_source_ids_skipped": skipped,
    }
    status_applied, status_skipped = [], []
    for item in review.get("status_overrides", []):
        key = str(item["plant_id"])
        p = properties.get(key)
        if not p or p.get("plant_name") != item["plant_name"]:
            raise ValueError(f"Missing/mismatched refinery status identity: {key}")
        if not item["source_url"].startswith("https://") or not item["effective_as_of"] or not item["note"]:
            raise ValueError(f"Missing reviewed status source/date: {key}")
        if not item["plant_status_desc"].startswith("Idle ("):
            raise ValueError(f"Unreviewed status override: {key}")
        if str(p.get("release_date") or "")[:10] > checked:
            status_skipped.append(key)
            continue
        p.setdefault("original_iir_plant_status", {
            "plant_status_desc": p.get("plant_status_desc"),
            "release_date": p.get("release_date"),
        })
        p["plant_status_desc"] = item["plant_status_desc"]
        p["status_source_name"] = item["source_name"]
        p["status_source_url"] = item["source_url"]
        p["status_checked_at"] = checked
        p["status_effective_as_of"] = item["effective_as_of"]
        p["status_review_note"] = item["note"]
        p["status_review_sources"] = [item[k] for k in ("source_url", "supporting_url", "conflicting_undated_url") if item.get(k)]
        p["eia_idle_capacity"] = {
            "as_of": item.get("eia_status_as_of", item["effective_as_of"]),
            "bbl_calendar_d": item["eia_idle_capacity_bbl_calendar_d"],
            "bbl_stream_d": item["eia_idle_capacity_bbl_stream_d"],
        }
        status_applied.append(key)
    data["status_review"] = {
        "checked_at": checked,
        "overrides_applied": len(status_applied),
        "source_file": "data/refinery_capacity_overrides.json",
        "note": "Dated status confirmations do not establish real-time operations; announced restarts are not completed restarts. Original IIR unit rows are retained, but inactive plant status excludes their modeled capacity and products.",
        "newer_source_ids_skipped": status_skipped,
    }
    return applied, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "public/data/refineries.geojson")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overrides", type=Path, default=ROOT / "data/refinery_capacity_overrides.json")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    review = json.loads(args.overrides.read_text(encoding="utf-8"))
    applied, skipped = apply_overrides(data, review)
    # Verify that a repeated run preserves both content and original IIR values.
    repeated = copy.deepcopy(data)
    apply_overrides(repeated, review)
    if repeated != data:
        raise ValueError("Refinery reconciliation must be idempotent")
    output = args.output or args.input
    output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Applied {len(applied)} refinery capacity and {data['status_review']['overrides_applied']} status overrides; skipped {len(skipped)} newer capacity records and {len(data['status_review']['newer_source_ids_skipped'])} newer status records.")


if __name__ == "__main__":
    main()
