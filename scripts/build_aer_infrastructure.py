"""Refresh AER pipeline/installations GeoJSON and existing zoom-8 detail tiles.

Downloads official public SHP/CSV archives, cross-checks their mapped record
identities, transforms NAD83 to WGS84, and validates all selected geometry.
Builds both complete layer families in temporary staging before installing into
--data-dir. Any exception returns nonzero; the orchestrator keeps its baseline.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import math
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "pipelines": {"source_id": "aer_pipeline_spatial", "url": "https://www.aer.ca/data/pipeline/Pipelines_SHP.zip", "raw_file": "aer_pipeline_spatial.zip", "stem": "Pipelines_GCS_NAD83", "csv": "Pipelines.csv", "csv_id": "Pipeline_Licence_Segment_Id", "dbf_id": "PLLICSEGID", "csv_status": "Segment_Status", "dbf_status": "SEG_STATUS", "csv_substance": "Substance 1"},
    "installations": {"source_id": "aer_pipeline_installations_spatial", "url": "https://www.aer.ca/data/pipeline/Pipeline_Installations_SHP.zip", "raw_file": "aer_pipeline_installations_spatial.zip", "stem": "Pipeline_Installations_GCS_NAD83", "csv": "Pipeline Installations.csv", "csv_id": "Licence_ID_Installation_Number", "dbf_id": "LICINSTNO", "csv_status": "Pipeline_Installation_Status", "dbf_status": "PLINSTATUS", "csv_substance": "Substance_1"},
}
LINE_CATEGORIES = {"Oil-Well Effluent": "pipe-oilwell", "Crude Oil": "pipe-crude", "HVP Products": "pipe-hvp", "LVP Products": "pipe-lvp", "Condensate": "pipe-condensate", "Hydrocarbon Diluents": "pipe-diluent"}
INSTALL_CATEGORIES = {"Pump Station": "inst-pump", "Compressor Station": "inst-compressor", "Oil Terminal": "inst-terminal", "Tank Farm": "inst-terminal", "Meter Station": "inst-meter", "Regulator Station": "inst-meter", "Meter Regulator Stn.": "inst-meter", "Line Heater": "inst-meter"}
LINE_STATUSES = {"Operating", "Permitted"}
INSTALL_STATUSES = {"Operating", "Permitted", "Suspended"}
PIPE_FIELDS = {"licence": "LICENCE_NO", "segment_id": "PLLICSEGID", "segment_line": "LINE_NO", "company": "COMP_NAME", "status": "SEG_STATUS", "substance": "SUBSTANCE1", "from_fac": "FROM_FAC", "from_loc": "FROM_LOC", "to_fac": "TO_FAC", "to_loc": "TO_LOC", "diameter_mm": "OUT_DIAMET", "maop_kpa": "PIPE_MAOP", "material": "PIP_MATERL", "length_km": "SEG_LENGTH", "field_ctr": "FLD_CTR_NM", "joint": "JOINTMETHD", "geometry_source": "GEOM_SRCE"}
INSTALL_FIELDS = {"licence": "INSTA_LIC", "inst_id": "LICINSTNO", "company": "BA_NAME", "type": "INSTA_TYPE", "status": "PLINSTATUS", "substance": "SUBSTANCE1", "location": "INST_LOCAT", "field_ctr": "FLD_CENTRE", "power_kw": "POWER", "prime_source": "PRIME_SORC", "geometry_source": "GEOM_SRCE"}
MAX_DOWNLOAD = 300 * 1024 * 1024
MAX_EXPANDED = 1400 * 1024 * 1024
TILE_ZOOM = 8


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()
    path.write_bytes(payload)
    return len(payload)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_source(source, raw_dir, offline=False):
    path = raw_dir / source["raw_file"]
    receipt_path = path.with_suffix(".receipt.json")
    cached = read_json(receipt_path, {})
    valid_cache = bool(path.exists() and cached.get("url") == source["url"] and cached.get("sha256") == file_hash(path))
    if offline:
        if not valid_cache:
            raise ValueError(f"Offline AER source has no matching URL/hash receipt: {path.name}")
        return path, dict(cached, checked_at=now(), content_changed=False, fetch_status="cached_offline")
    headers = {"User-Agent": "WCPEInfrastructureETL/1.0 (public energy data research)"}
    if valid_cache:
        if cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]
        elif cached.get("source_last_modified"):
            headers["If-Modified-Since"] = cached["source_last_modified"]
    request = urllib.request.Request(source["url"], headers=headers)
    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".zip.part")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=45) as response, temporary.open("wb") as output:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname not in {"www.aer.ca", "static.aer.ca"}:
                raise ValueError("AER archive redirected away from the official HTTPS hosts")
            digest, count = hashlib.sha256(), 0
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > MAX_DOWNLOAD or time.monotonic() - started > 360:
                    raise ValueError("AER download exceeded the byte/time limit")
                digest.update(chunk)
                output.write(chunk)
            declared_length = response.headers.get("Content-Length")
            if count < 100 or (declared_length and count != int(declared_length)):
                raise ValueError("AER download is empty or incomplete")
            receipt = dict(source_id=source["source_id"], url=source["url"], resolved_url=response.geturl(),
                           raw_path=source["raw_file"], bytes=count, sha256=digest.hexdigest(),
                           checked_at=now(), retrieved_at=now(), etag=response.headers.get("ETag"),
                           source_last_modified=response.headers.get("Last-Modified"),
                           content_changed=cached.get("sha256") != digest.hexdigest(), fetch_status="downloaded")
        with ZipFile(temporary) as archive:
            validate_archive(archive)
        temporary.replace(path)
        write_json(receipt_path, receipt)
        return path, receipt
    except urllib.error.HTTPError as error:
        if error.code == 304 and valid_cache:
            return path, dict(cached, checked_at=now(), content_changed=False, fetch_status="not_modified")
        raise
    finally:
        temporary.unlink(missing_ok=True)


def validate_archive(archive):
    infos = archive.infolist()
    if not infos or len(infos) > 50 or sum(i.file_size for i in infos) > MAX_EXPANDED:
        raise ValueError("Unexpected AER ZIP file count or expanded size")
    names = [i.filename for i in infos]
    if len(set(names)) != len(names) or any(i.flag_bits & 1 for i in infos):
        raise ValueError("Duplicate or encrypted AER ZIP members")


def one_member(archive, basename):
    matches = [name for name in archive.namelist() if Path(name).name == basename]
    if len(matches) != 1:
        raise ValueError(f"AER archive must contain exactly one {basename}")
    return matches[0]


def normalize(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError("Non-finite AER attribute")
        return format(value, ".15g")
    return str(value).strip()


def mapped_csv_records(archive, source):
    member = one_member(archive, source["csv"])
    expected = [source["csv_id"], source["csv_status"], source["csv_substance"]]
    records = collections.Counter()
    with archive.open(member) as stream:
        reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
        if not set(expected) <= set(reader.fieldnames or []):
            raise ValueError("AER mapped CSV schema changed")
        for row in reader:
            if None in row or any(row.get(key) is None for key in expected):
                raise ValueError("Malformed AER CSV row")
            key = tuple(normalize(row[name]) for name in expected)
            if not key[0]:
                raise ValueError("AER mapped CSV has an empty source identity")
            records[key] += 1
    if not records:
        raise ValueError("AER mapped CSV is empty")
    return records


def unmapped_count(archive, source):
    member = one_member(archive, "Unmapped " + source["csv"])
    with archive.open(member) as stream:
        reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
        if source["csv_id"] not in (reader.fieldnames or []):
            raise ValueError("AER unmapped CSV schema changed")
        return sum(1 for _ in reader)


def coordinate_transform(wkt):
    from pyproj import CRS, Transformer, network
    from pyproj.aoi import AreaOfInterest
    network.set_network_enabled(False)
    source = CRS.from_wkt(wkt)
    # ESRI's NAD83 WKT uses longitude/latitude axis order; EPSG's canonical
    # declaration uses latitude/longitude. always_xy below fixes storage order.
    if not source.equals(CRS.from_epsg(4269), ignore_axis_order=True):
        raise ValueError("AER GCS_NAD83 file has an unexpected coordinate reference system")
    transform = Transformer.from_crs(source, "EPSG:4326", always_xy=True,
                                     area_of_interest=AreaOfInterest(-120.1, 48.9, -109.9, 60.1), allow_ballpark=False)
    transform.transform(-114, 53, errcheck=True)
    if transform.accuracy < 0 or transform.accuracy > 10:
        raise ValueError("No validated NAD83 to WGS84 transform is available")
    return transform


def transformed_geometry(shape, kind, transform, stats=None):
    expected = 3 if kind == "pipelines" else 1
    if shape.shapeType != expected:
        raise ValueError(f"Unexpected/null AER geometry type {shape.shapeType}")
    points, precise_points = [], []
    for x, y in shape.points:
        if not all(math.isfinite(v) for v in (x, y)) or not (-120.1 <= x <= -109.9 and 48.9 <= y <= 60.1):
            raise ValueError("AER geometry is non-finite or outside the Alberta source extent")
        lon, lat = transform.transform(x, y, errcheck=True)
        if not all(math.isfinite(v) for v in (lon, lat)):
            raise ValueError("Coordinate conversion returned a non-finite position")
        precise_points.append([lon, lat])
        points.append([round(lon, 6), round(lat, 6)])
    if kind == "installations":
        if len(points) != 1:
            raise ValueError("AER installation must have exactly one position")
        return {"type": "Point", "coordinates": points[0]}
    parts = list(shape.parts)
    if not parts or parts[0] != 0 or parts != sorted(set(parts)) or parts[-1] >= len(points):
        raise ValueError("Malformed AER line parts")
    lines = []
    for start, end in zip(parts, parts[1:] + [len(points)]):
        # Rounding must not leave consecutive duplicates or a degenerate line.
        line = []
        for point in points[start:end]:
            if not line or point != line[-1]:
                line.append(point)
        if len(line) < 2:
            # Very short legitimate source parts can collapse at display
            # precision. Preserve their transformed coordinates without rounding.
            line = []
            for point in precise_points[start:end]:
                if not line or point != line[-1]:
                    line.append(point)
            if len(line) < 2:
                if stats is not None:
                    stats["zero_length_parts_excluded"] += 1
                continue
            if stats is not None:
                stats["precision_preserved_parts"] += 1
        lines.append(line)
    if not lines:
        raise ValueError("AER line has no component with two distinct positions")
    return {"type": "LineString", "coordinates": lines[0]} if len(lines) == 1 else {"type": "MultiLineString", "coordinates": lines}


def convert_archive(path, kind, work_dir):
    import shapefile
    source = SOURCES[kind]
    fields = PIPE_FIELDS if kind == "pipelines" else INSTALL_FIELDS
    features, seen, identities = [], set(), collections.Counter()
    stats = collections.Counter()
    with ZipFile(path) as archive:
        validate_archive(archive)
        csv_records = mapped_csv_records(archive, source)
        unmapped = unmapped_count(archive, source)
        wkt = archive.read(one_member(archive, source["stem"] + ".prj")).decode("utf-8")
        transform = coordinate_transform(wkt)
        for extension in (".shp", ".shx", ".dbf"):
            member = one_member(archive, source["stem"] + extension)
            # Explicit fixed destination names; never extract caller-controlled ZIP paths.
            with archive.open(member) as incoming, (work_dir / (kind + extension)).open("wb") as target:
                shutil.copyfileobj(incoming, target, length=1024 * 1024)
        cpg = archive.read(one_member(archive, source["stem"] + ".cpg")).decode().strip()
        if cpg.upper() not in {"UTF-8", "UTF8", "65001"}:
            raise ValueError(f"Unexpected AER text encoding: {cpg}")
        with shapefile.Reader(str(work_dir / kind), encoding="utf-8") as reader:
            if not set(fields.values()) <= {item[0] for item in reader.fields[1:]}:
                raise ValueError("AER shapefile attribute schema changed")
            if reader.numRecords != sum(csv_records.values()) or reader.numShapes != reader.numRecords:
                raise ValueError("AER SHP/DBF/CSV mapped record counts do not reconcile")
            for record in reader.iterRecords(fields=list(fields.values())):
                row = record.as_dict()
                identity = normalize(row[source["dbf_id"]])
                status, substance = normalize(row[source["dbf_status"]]), normalize(row["SUBSTANCE1"])
                identities[(identity, status, substance)] += 1
                stats["mapped_source_records"] += 1
                if kind == "pipelines" and (status not in LINE_STATUSES or substance not in LINE_CATEGORIES):
                    stats["excluded_by_status_or_substance"] += 1
                    continue
                if not identity:
                    raise ValueError("AER selected feature has an empty source identity")
                props = {name: normalize(row[field]) for name, field in fields.items()}
                if kind == "pipelines":
                    length = props["length_km"]
                    if not length or float(length) < 0:
                        raise ValueError("AER selected pipeline has an invalid segment length")
                    props["length_km"] = float(length)
                if kind == "installations" and props["type"] not in INSTALL_CATEGORIES:
                    raise ValueError(f"Unmapped AER installation type {props['type']}")
                shape = reader.shape(record.oid)
                try:
                    geometry = transformed_geometry(shape, kind, transform, stats)
                except ValueError as error:
                    raise ValueError(f"AER {kind} source {identity}: {error}; first source positions {shape.points[:3]}") from error
                canonical = json.dumps([props, geometry], sort_keys=True, separators=(",", ":"))
                digest = hashlib.sha256(canonical.encode()).hexdigest()
                if digest in seen:
                    stats["exact_duplicates_excluded"] += 1
                    continue
                seen.add(digest)
                # A segment may be represented by distinct geometries with the same
                # licence identity; preserve them, while removing exact duplicates.
                features.append({"type": "Feature", "id": f"aer:{kind}:{identity}:{digest[:12]}", "properties": props, "geometry": geometry})
            if identities != csv_records:
                raise ValueError("AER SHP and CSV source identities/status/substance do not reconcile")
    if not features:
        raise ValueError("AER source has no selected mapped infrastructure")
    if kind == "pipelines" and {f["properties"]["substance"] for f in features} != set(LINE_CATEGORIES):
        raise ValueError("AER pipeline source lost an entire displayed substance class")
    stats.update(unmapped_source_records=unmapped, published_features=len(features))
    metadata = dict(source_name="AER Enhanced Pipeline Graphics File", source_url=source["url"],
                    source_crs="EPSG:4269", output_crs="EPSG:4326", coordinate_transform=transform.description,
                    transform_accuracy_m=transform.accuracy, counts=dict(stats),
                    scope="Selected mapped Operating/Permitted liquid pipeline categories." if kind == "pipelines" else "All mapped installations; category menus include Operating, Permitted and Suspended statuses.",
                    limitations=["Unmapped CSV records have no coordinates and are excluded from map geometry.",
                                 "Absence from a later source is not evidence of physical removal or closure.",
                                 "Regulator geometry includes mapping and as-planned sources; this is not a survey of current positions."])
    return {"type": "FeatureCollection", "metadata": metadata, "features": sorted(features, key=lambda f: f["id"])}


def lonlat_tile(lon, lat, zoom=TILE_ZOOM):
    n = 2 ** zoom
    rad = math.radians(max(-85.05112878, min(85.05112878, lat)))
    return (max(0, min(n - 1, math.floor((lon + 180) / 360 * n))),
            max(0, min(n - 1, math.floor((1 - math.asinh(math.tan(rad)) / math.pi) / 2 * n))))


def feature_tile_keys(feature):
    geometry = feature["geometry"]
    lines = [geometry["coordinates"]] if geometry["type"] == "LineString" else geometry["coordinates"]
    keys = set()
    for line in lines:
        xs, ys = zip(*(lonlat_tile(*point) for point in line))
        # Bounding coverage intentionally includes crossing tiles even when a
        # segment has no vertex in a tile. The UI expects complete GeoJSON lines.
        for x in range(min(xs), max(xs) + 1):
            for y in range(min(ys), max(ys) + 1):
                keys.add(f"{x}/{y}")
    if not keys or len(keys) > 120:
        raise ValueError("AER feature has an implausibly large tile extent")
    return sorted(keys)


def source_changes(current, baseline, kind):
    name = "aer_feeder_pipelines.geojson" if kind == "pipelines" else "aer_pipeline_installations.geojson"
    old = read_json(baseline / name, {}).get("features", [])
    key = "inst_id" if kind == "installations" else "segment_id"
    new_ids = {f["properties"].get(key) for f in current["features"]}
    old_ids = {f.get("properties", {}).get(key) for f in old} - {None, ""}
    result = dict(previous_feature_count=len(old), current_feature_count=len(current["features"]))
    if old_ids:
        result.update(added_source_ids=sorted(new_ids - old_ids), absent_source_ids=sorted(old_ids - new_ids),
                      retained_source_id_count=len(old_ids & new_ids),
                      absence_meaning="Not present in the latest mapped source/scope; no physical removal or closure inferred.")
    else:
        result["identity_comparison"] = "Previous pipeline snapshot omitted segment IDs; licence numbers alone cannot identify individual segments."
    return result


def publication_check(check, baseline, kind):
    previous = read_json(baseline / "aer_pipeline_index.json", {}).get("sources", {}).get(kind, {})
    if not previous.get("sha256"):
        name = "aer_feeder_pipelines.geojson" if kind == "pipelines" else "aer_pipeline_installations.geojson"
        metadata = read_json(baseline / name, {}).get("metadata", {})
        previous = {"sha256": metadata.get("source_sha256"), "source_last_modified": metadata.get("source_last_modified")}
    def modified(source):
        value = source.get("source_last_modified")
        if not value:
            return None
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            raise ValueError("AER Last-Modified timestamp lacks a timezone")
        return parsed.astimezone(timezone.utc)
    incoming_date, previous_date = modified(check), modified(previous)
    if incoming_date and incoming_date > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise ValueError("AER archive has a future Last-Modified timestamp")
    if incoming_date and previous_date and incoming_date < previous_date:
        raise ValueError("AER archive is older than the published source")
    # A cached download might never have been published if an earlier transform
    # failed. Archival eligibility must compare against the published source.
    return dict(check, download_content_changed=check.get("content_changed", False),
                content_changed=check["sha256"] != previous.get("sha256"))


def stage_outputs(stage, layers, checks):
    index = dict(version=2, generated_at=now(), builder_version=1, line_categories={}, installation_categories={},
                 sources=checks, filters={"pipeline_statuses": sorted(LINE_STATUSES), "pipeline_substances": sorted(LINE_CATEGORIES),
                                         "installation_menu_statuses": sorted(INSTALL_STATUSES)})
    for kind, name in (("pipelines", "aer_feeder_pipelines.geojson"), ("installations", "aer_pipeline_installations.geojson")):
        layers[kind]["metadata"].update(source_sha256=checks[kind]["sha256"], source_last_modified=checks[kind].get("source_last_modified"),
                                        source_retrieved_at=checks[kind]["retrieved_at"])
        write_json(stage / name, layers[kind])
    grouped = collections.defaultdict(list)
    for f in layers["pipelines"]["features"]:
        grouped[LINE_CATEGORIES[f["properties"]["substance"]]].append(f)
    for key, features in sorted(grouped.items()):
        path = f"pipelines/aer_feeder_{key}.geojson"
        count = write_json(stage / path, {"type": "FeatureCollection", "features": features})
        tiles = collections.defaultdict(list)
        for feature in features:
            for tile in feature_tile_keys(feature):
                tiles[tile].append(feature)
        total_bytes = 0
        for tile, tiled in sorted(tiles.items()):
            total_bytes += write_json(stage / f"pipeline_tiles/{key}/{TILE_ZOOM}/{tile}.geojson", {"type": "FeatureCollection", "features": tiled})
        index["line_categories"][key] = dict(path="public/data/" + path, count=len(features), bytes=count,
                    tile_template=f"public/data/pipeline_tiles/{key}/{TILE_ZOOM}/{{x}}/{{y}}.geojson", tile_zoom=TILE_ZOOM,
                    tile_count=len(tiles), tile_bytes=total_bytes, tile_keys=sorted(tiles))
    grouped.clear()
    for f in layers["installations"]["features"]:
        if f["properties"]["status"] in INSTALL_STATUSES:
            grouped[INSTALL_CATEGORIES[f["properties"]["type"]]].append(f)
    if set(grouped) != set(INSTALL_CATEGORIES.values()):
        raise ValueError("AER source lost an entire displayed installation category")
    for key, features in sorted(grouped.items()):
        path = f"pipelines/aer_install_{key}.geojson"
        count = write_json(stage / path, {"type": "FeatureCollection", "features": features})
        index["installation_categories"][key] = dict(path="public/data/" + path, count=len(features), bytes=count)
    write_json(stage / "aer_pipeline_index.json", index)
    return index


def validate_outputs(data_dir):
    """Return errors for the complete generated AER monolith/category/tile family.

    Reads only the supplied data directory. Category and tile features must equal
    their validated monolith records, including properties and geometry, so a
    missing/altered tile cannot pass merely by preserving an aggregate count.
    """
    from validate_infrastructure_layers import validate_geometries
    data_dir = Path(data_dir).resolve()
    errors = []
    expected_files = {Path("aer_feeder_pipelines.geojson"), Path("aer_pipeline_installations.geojson")}

    def data_path(relative):
        path = data_dir / relative
        if not path.resolve().is_relative_to(data_dir):
            raise ValueError(f"AER asset resolves outside its data directory: {relative}")
        return path

    def collection(relative, validate_geometry=False):
        data = read_json(data_path(relative))
        if not isinstance(data, dict) or data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
            raise ValueError(f"{relative}: expected a GeoJSON FeatureCollection")
        features = data["features"]
        if any(not isinstance(f, dict) or f.get("type") != "Feature" or not isinstance(f.get("id"), str) or not f["id"] for f in features):
            raise ValueError(f"{relative}: invalid/missing feature identity")
        by_id = {f["id"]: f for f in features}
        if len(by_id) != len(features):
            errors.append(f"{relative}: duplicate feature IDs")
        if validate_geometry:
            errors.extend(validate_geometries(str(relative), data))
        return data, by_id

    def equal_features(relative, actual, expected):
        if actual.keys() != expected.keys():
            errors.append(f"{relative}: feature coverage differs from the source/category")
        elif any(actual[key] != expected[key] for key in expected):
            errors.append(f"{relative}: feature properties or geometry differ from the source/category")

    try:
        index = read_json(data_path("aer_pipeline_index.json"))
        if not isinstance(index, dict) or index.get("version") != 2 or not index.get("builder_version"):
            raise ValueError("aer_pipeline_index.json: unsupported generated index schema")
        source_groups = {}
        for kind, name in (("pipelines", "aer_feeder_pipelines.geojson"), ("installations", "aer_pipeline_installations.geojson")):
            data, features = collection(name, validate_geometry=True)
            if not features:
                errors.append(f"{name}: empty infrastructure source")
            if data.get("metadata", {}).get("counts", {}).get("published_features") != len(features):
                errors.append(f"{name}: published feature count does not reconcile")
            if data.get("metadata", {}).get("source_sha256") != index.get("sources", {}).get(kind, {}).get("sha256"):
                errors.append(f"{name}: source hash differs from the index")
            grouped = collections.defaultdict(dict)
            for feature_id, feature in features.items():
                props, geometry = feature.get("properties") or {}, feature.get("geometry") or {}
                if kind == "pipelines":
                    if geometry.get("type") not in {"LineString", "MultiLineString"} or props.get("status") not in LINE_STATUSES or props.get("substance") not in LINE_CATEGORIES:
                        errors.append(f"{name}: invalid selected pipeline scope/type for {feature_id}")
                        continue
                    grouped[LINE_CATEGORIES[props["substance"]]][feature_id] = feature
                else:
                    if geometry.get("type") != "Point" or props.get("type") not in INSTALL_CATEGORIES:
                        errors.append(f"{name}: invalid installation scope/type for {feature_id}")
                        continue
                    if props.get("status") in INSTALL_STATUSES:
                        grouped[INSTALL_CATEGORIES[props["type"]]][feature_id] = feature
            source_groups[kind] = grouped
        for kind, bucket, categories in (("pipelines", "line_categories", set(LINE_CATEGORIES.values())),
                                         ("installations", "installation_categories", set(INSTALL_CATEGORIES.values()))):
            entries = index.get(bucket)
            if not isinstance(entries, dict) or set(entries) != categories:
                raise ValueError(f"aer_pipeline_index.json: missing/unexpected {bucket}")
            for key, entry in entries.items():
                if not isinstance(entry, dict):
                    raise ValueError(f"aer_pipeline_index.json: malformed category {key}")
                prefix = "aer_feeder" if kind == "pipelines" else "aer_install"
                relative = Path(f"pipelines/{prefix}_{key}.geojson")
                expected_files.add(relative)
                if entry.get("path") != "public/data/" + relative.as_posix():
                    raise ValueError(f"aer_pipeline_index.json: unexpected category path for {key}")
                _, actual = collection(relative)
                expected = source_groups[kind][key]
                equal_features(relative, actual, expected)
                if not expected or entry.get("count") != len(expected) or entry.get("bytes") != data_path(relative).stat().st_size:
                    errors.append(f"{relative}: category count/bytes do not reconcile")
                if kind != "pipelines":
                    continue
                template = f"public/data/pipeline_tiles/{key}/{TILE_ZOOM}/{{x}}/{{y}}.geojson"
                if entry.get("tile_template") != template or entry.get("tile_zoom") != TILE_ZOOM:
                    raise ValueError(f"aer_pipeline_index.json: unexpected tile path/zoom for {key}")
                tiles = collections.defaultdict(dict)
                for feature_id, feature in expected.items():
                    for tile in feature_tile_keys(feature):
                        tiles[tile][feature_id] = feature
                keys = entry.get("tile_keys")
                if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys) or set(keys) != set(tiles):
                    errors.append(f"{key}: tile keys do not provide complete geometry coverage")
                total_bytes = 0
                # Iterate calculated paths, never paths supplied by an untrusted index.
                for tile, expected_features in tiles.items():
                    relative = Path(f"pipeline_tiles/{key}/{TILE_ZOOM}/{tile}.geojson")
                    expected_files.add(relative)
                    _, actual = collection(relative)
                    equal_features(relative, actual, expected_features)
                    total_bytes += data_path(relative).stat().st_size
                if entry.get("tile_count") != len(tiles) or entry.get("tile_bytes") != total_bytes:
                    errors.append(f"{key}: tile count/bytes do not reconcile")
        actual_files = {Path("aer_feeder_pipelines.geojson"), Path("aer_pipeline_installations.geojson")}
        for pattern in ("pipelines/aer_feeder_*.geojson", "pipelines/aer_install_*.geojson", "pipeline_tiles/pipe-*/*/*/*.geojson"):
            actual_files.update(path.relative_to(data_dir) for path in data_dir.glob(pattern))
        if actual_files != expected_files:
            errors.append("AER category/tile file inventory differs from its complete index")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        errors.append(f"AER output validation failed: {error}")
    return errors


def install_outputs(stage, output):
    output.mkdir(parents=True, exist_ok=True)
    current_files = {p.relative_to(stage) for p in stage.rglob("*.geojson")}
    # Remove only superseded files belonging to this explicitly owned family.
    old_files = set()
    for pattern in ("pipelines/aer_feeder_*.geojson", "pipelines/aer_install_*.geojson", "pipeline_tiles/pipe-*/*/*/*.geojson"):
        old_files.update(p.relative_to(output) for p in output.glob(pattern))
    for relative in current_files:
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(stage / relative, target)
    for relative in old_files - current_files:
        (output / relative).unlink()
    # Index is installed last, after its category/tile files are complete.
    shutil.copyfile(stage / "aer_pipeline_index.json", output / "aer_pipeline_index.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, default=ROOT / "public/data")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    args.data_dir = args.data_dir.resolve()
    args.data_dir.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status="failed", checked_at=now(), checks=[], counts={}, changes={})
    try:
        with tempfile.TemporaryDirectory(prefix="aer-infrastructure-", dir=args.data_dir.parent) as directory:
            work = Path(directory)
            layers, checks = {}, {}
            for kind, source in SOURCES.items():
                path, check = download_source(source, args.raw_dir, args.offline)
                check = publication_check(check, args.baseline_dir, kind)
                report["checks"].append(check)
                checks[kind] = check
                layers[kind] = convert_archive(path, kind, work)
                report["counts"][kind] = layers[kind]["metadata"]["counts"]
                report["changes"][kind] = source_changes(layers[kind], args.baseline_dir, kind)
            stage = work / "candidate"
            index = stage_outputs(stage, layers, checks)
            report["tile_count"] = sum(c["tile_count"] for c in index["line_categories"].values())
            output_errors = validate_outputs(stage)
            if output_errors:
                raise ValueError("; ".join(output_errors[:10]))
            install_outputs(stage, args.data_dir)
        report["status"] = "ok"
    except Exception as error:
        report["error"] = str(error)
    if args.report:
        write_json(args.report, report)
    print(json.dumps({key: report[key] for key in ("status", "counts", "tile_count", "error") if key in report}))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
