"""Validate and publish reviewed Enbridge line facts independently of map geometry.

Route IDs provide context only. No coordinates, inferred numbered corridors,
combined capacities, live batches or available transportation are published here.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "enbridge_liquids_lines.json"
DEFAULT_OUTPUT = ROOT / "public" / "data" / "enbridge_liquids_lines.json"
DEFAULT_ROUTES = ROOT / "public" / "data" / "market_access_pipelines.geojson"
REQUIRED_MAINLINE_IDS = frozenset(f"enbridge-line-{number}" for number in
                                 ("1", "2a", "2b", "3a", "93", "4", "5", "6", "14-64", "61", "62", "65", "67", "78a", "78b"))
REQUIRED_FACTSHEET_IDS = REQUIRED_MAINLINE_IDS | frozenset(f"enbridge-line-{number}" for number in
    ("7", "8", "9", "11", "13", "17", "18", "19", "20", "21", "26", "33", "34", "36", "37", "40", "41", "42", "45", "49", "50", "55", "59", "63", "70", "72", "73", "74", "75", "76", "77", "79", "81", "82", "83", "84", "85", "86", "87", "88", "90", "91", "291", "292"))
CAPACITY_BASES = {"annual_average", "average_annual", "nameplate", "rated", "operating", "initial", "historical",
                  "section_dependent", "range", "not_published"}
REQUIRED_FIELDS = {"id", "line_number", "name", "aliases", "products", "origin", "destination", "direction",
                   "capacity_kbbl_d", "capacity_basis", "capacity_note", "status", "status_note", "diameter_note",
                   "length_note", "connections", "trading_note", "route_ids", "geometry_note", "sources",
                   "reviewed_at", "commercial_links"}
OPTIONAL_FIELDS = {"operator", "ownership_note", "capacity_label", "products_note"}
GEOMETRY_FIELDS = {"geometry", "coordinates", "features", "geojson", "wkt", "bbox", "longitude", "latitude", "lon", "lat"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _url(value: Any) -> bool:
    if not _text(value) or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password and parsed.port != 0
    except ValueError:
        return False


def _review_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _capacity(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return value > 0 and math.isfinite(value)
    except OverflowError:
        return False


def _geometry_keys(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(set(value) & GEOMETRY_FIELDS) or any(_geometry_keys(v) for v in value.values())
    return isinstance(value, list) and any(_geometry_keys(v) for v in value)


def _links_errors(values: Any, label: str, *, evidence: bool) -> list[str]:
    if not isinstance(values, list) or evidence and not values:
        return [f"{label}: explicit source-link list required"]
    errors = []
    for index, link in enumerate(values):
        if (not isinstance(link, dict) or not {"label", "url"} <= set(link)
                or set(link) - {"label", "url", "as_of", "note", "access", "access_note"}):
            errors.append(f"{label} {index}: unsupported/missing source-link fields")
            continue
        if not _text(link["label"]) or not _url(link["url"]):
            errors.append(f"{label} {index}: nonempty label and safe public HTTP(S) URL required")
        for field in ("as_of", "note", "access", "access_note"):
            if field in link and link[field] is not None and not _text(link[field]):
                errors.append(f"{label} {index}: {field} must retain a source statement or be omitted")
    return errors


def validate_catalogue(payload: Any, route_ids: set[str], required_ids: frozenset[str] = REQUIRED_FACTSHEET_IDS) -> list[str]:
    if (not isinstance(payload, dict) or set(payload) != {"schema_version", "metadata", "lines"}
            or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1
            or not isinstance(payload.get("metadata"), dict) or not isinstance(payload.get("lines"), list)):
        return ["Enbridge line catalogue requires schema_version 1, metadata and lines"]
    errors = []
    if not _review_date(payload["metadata"].get("reviewed_at")):
        errors.append("Enbridge line catalogue metadata.reviewed_at requires YYYY-MM-DD")
    if _geometry_keys(payload):
        errors.append("Enbridge line catalogue must not contain geometry or coordinates; route IDs are context only")
    seen = set()
    for index, line in enumerate(payload["lines"]):
        label = f"Enbridge line {index}"
        if not isinstance(line, dict):
            errors.append(f"{label}: line record must be an object")
            continue
        if not REQUIRED_FIELDS <= set(line) or set(line) - REQUIRED_FIELDS - OPTIONAL_FIELDS:
            errors.append(f"{label}: missing/unsupported fields {sorted(REQUIRED_FIELDS - set(line))} / {sorted(set(line) - REQUIRED_FIELDS - OPTIONAL_FIELDS)}")
        identity = line.get("id")
        if not isinstance(identity, str) or not re.fullmatch(r"(?:former-)?enbridge-[a-z0-9]+(?:-[a-z0-9]+)*", identity) or identity in seen:
            errors.append(f"{label}: missing, invalid or duplicate catalogue ID")
        else:
            seen.add(identity)
            label = identity
        number = line.get("line_number")
        if "line_number" not in line or number is not None and (not isinstance(number, str) or not re.fullmatch(r"[0-9]+[A-Z]?(?:/[0-9]+[A-Z]?)?", number)):
            errors.append(f"{label}: line_number must be a published numbered identity or explicit null")
        numbered_id = re.fullmatch(r"(?:former-)?enbridge-line-([0-9]+[ab]?(?:-[0-9]+[ab]?)?)", identity) if isinstance(identity, str) else None
        if numbered_id and number != numbered_id.group(1).upper().replace("-", "/"):
            errors.append(f"{label}: catalogue ID does not match the explicit published line_number")
        for field in (REQUIRED_FIELDS - {"id", "line_number", "capacity_kbbl_d", "aliases", "products", "connections", "route_ids", "sources", "commercial_links"}) | OPTIONAL_FIELDS:
            if field in line and not _text(line[field]):
                errors.append(f"{label}: {field} must be a nonempty source statement")
        if not _review_date(line.get("reviewed_at")):
            errors.append(f"{label}: reviewed_at requires YYYY-MM-DD")
        for field in ("aliases", "products", "connections", "route_ids"):
            values = line.get(field)
            if not isinstance(values, list) or any(not _text(v) for v in values):
                errors.append(f"{label}: {field} must be an explicit string list")
            elif len(set(values)) != len(values):
                errors.append(f"{label}: duplicate {field} values")
        if line.get("products") == [] and (line.get("status") != "unknown" or not _text(line.get("products_note"))):
            errors.append(f"{label}: unknown products require status unknown and products_note")
        contexts = line.get("route_ids")
        if isinstance(contexts, list) and all(isinstance(value, str) for value in contexts) and set(contexts) - route_ids:
            errors.append(f"{label}: unmapped route context IDs {sorted(set(contexts) - route_ids)}")
        basis, value = line.get("capacity_basis"), line.get("capacity_kbbl_d")
        if not isinstance(basis, str) or basis not in CAPACITY_BASES:
            errors.append(f"{label}: capacity basis must be explicitly supported")
        if "capacity_kbbl_d" not in line or value is not None and not _capacity(value):
            errors.append(f"{label}: capacity_kbbl_d must be positive finite numeric or explicit null")
        if value is None and basis not in {"not_published", "range", "section_dependent"}:
            errors.append(f"{label}: null capacity requires unknown or separately scoped published rating")
        if value is None and basis in {"range", "section_dependent"} and not _text(line.get("capacity_label")):
            errors.append(f"{label}: separately scoped capacity requires capacity_label")
        if value is not None and basis in {"not_published", "range", "section_dependent"}:
            errors.append(f"{label}: a single rating cannot represent unpublished or separately scoped capacities")
        errors.extend(_links_errors(line.get("sources"), f"{label} sources", evidence=True))
        errors.extend(_links_errors(line.get("commercial_links"), f"{label} commercial links", evidence=False))
    if required_ids - seen:
        errors.append(f"Enbridge catalogue missing researched published line identities {sorted(required_ids - seen)}")
    return errors


def read_json(path: Path) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path.name}: duplicate JSON key {key}")
            result[key] = value
        return result
    def finite_literal(value):
        raise ValueError(f"{path.name}: nonfinite JSON literal {value}")
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique, parse_constant=finite_literal)


def mapped_route_ids(path: Path = DEFAULT_ROUTES) -> set[str]:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("Mapped routes must be a GeoJSON FeatureCollection")
    if any(not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict)
           for feature in payload["features"]):
        raise ValueError("Mapped routes require feature property objects")
    ids = [feature["properties"].get("route_id") for feature in payload["features"]
           if feature["properties"].get("feature_kind") == "pipeline"]
    if any(not _text(value) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("Mapped pipelines require unique nonempty route IDs")
    return set(ids)


def load_catalogue(path: Path = DEFAULT_SOURCE, *, routes: Path = DEFAULT_ROUTES) -> dict[str, Any]:
    payload = read_json(path)
    errors = validate_catalogue(payload, mapped_route_ids(routes))
    if errors:
        raise ValueError("; ".join(errors))
    return payload


def publish_catalogue(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT, *, routes: Path = DEFAULT_ROUTES) -> dict[str, Any]:
    payload = load_catalogue(source, routes=routes)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(output)
    return payload


def published_catalogue_errors(published: Path = DEFAULT_OUTPUT, source: Path = DEFAULT_SOURCE, *, routes: Path = DEFAULT_ROUTES) -> list[str]:
    try:
        payload = load_catalogue(published, routes=routes)
        original = load_catalogue(source, routes=routes)
    except (OSError, ValueError, TypeError) as exc:
        return [f"Enbridge catalogue publication: {exc}"]
    return [] if payload == original else ["Published Enbridge catalogue differs from the reviewed source file"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--routes", type=Path, default=DEFAULT_ROUTES)
    args = parser.parse_args()
    payload = publish_catalogue(args.source, args.output, routes=args.routes)
    print(f"Published {len(payload['lines'])} reviewed Enbridge line/system entries; no geometry inferred")


if __name__ == "__main__":
    main()
