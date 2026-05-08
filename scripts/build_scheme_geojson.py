"""
Convert cached AER GCS_NAD83 scheme-approval shapefiles to app GeoJSON.

This intentionally avoids heavyweight GIS dependencies so it can run inside the
bundled workspace Python. The source zip already contains GCS_NAD83 lon/lat
shapefiles, so no projection transform is needed.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ZIP = ROOT / "data" / "raw" / "aer_scheme_approval_spatial.zip"
OUTPUT = ROOT / "public" / "data" / "aer_scheme_approvals.geojson"

LAYERS = [
    {
        "folder": "In Situ Oil Sands Scheme Approvals",
        "stem": "In Situ Oil Sands Scheme Approval_GCS_NAD83",
        "kind": "in_situ_scheme",
        "label": "In-situ scheme approval",
    },
    {
        "folder": "Mineable Oil Sands Scheme Approvals",
        "stem": "Mineable Oil Sands Scheme Approval_GCS_NAD83",
        "kind": "mineable_scheme",
        "label": "Mineable scheme approval",
    },
]


def read_dbf(zip_file: ZipFile, name: str) -> list[dict[str, str]]:
    data = zip_file.read(name)
    num_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]

    fields: list[tuple[str, str, int, int]] = []
    offset = 32
    while offset < header_len - 1:
        field = data[offset : offset + 32]
        if field[0] == 0x0D:
            break
        name_raw = field[:11].split(b"\x00", 1)[0]
        field_name = name_raw.decode("latin1", errors="ignore").strip()
        field_type = chr(field[11])
        field_len = field[16]
        field_dec = field[17]
        fields.append((field_name, field_type, field_len, field_dec))
        offset += 32

    records: list[dict[str, str]] = []
    offset = header_len
    for _ in range(num_records):
        row = data[offset : offset + record_len]
        offset += record_len
        if not row or row[0:1] == b"*":
            continue
        cursor = 1
        item: dict[str, str] = {}
        for field_name, field_type, field_len, _field_dec in fields:
            raw = row[cursor : cursor + field_len]
            cursor += field_len
            text = raw.decode("latin1", errors="ignore").strip()
            if field_type == "D" and len(text) == 8:
                text = f"{text[:4]}-{text[4:6]}-{text[6:]}"
            item[field_name] = text
        records.append(item)
    return records


def simplify_ring(points: list[list[float]], min_delta: float = 0.0007) -> list[list[float]]:
    """Light coordinate thinning; keeps vertices when movement is material."""
    if len(points) <= 12:
        return points
    kept = [points[0]]
    last_x, last_y = points[0]
    for x, y in points[1:-1]:
        if abs(x - last_x) >= min_delta or abs(y - last_y) >= min_delta:
            kept.append([x, y])
            last_x, last_y = x, y
    kept.append(points[-1])
    if kept[0] != kept[-1]:
        kept.append(kept[0])
    return kept


def read_polygon_shapes(zip_file: ZipFile, name: str) -> list[dict]:
    data = zip_file.read(name)
    offset = 100
    shapes: list[dict] = []
    while offset + 8 <= len(data):
        _record_number, content_words = struct.unpack(">2i", data[offset : offset + 8])
        offset += 8
        content_len = content_words * 2
        content = data[offset : offset + content_len]
        offset += content_len
        if len(content) < 44:
            continue
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type == 0:
            shapes.append({"type": None, "coordinates": []})
            continue
        if shape_type != 5:
            raise ValueError(f"Unsupported shape type {shape_type} in {name}")
        num_parts = struct.unpack("<i", content[36:40])[0]
        num_points = struct.unpack("<i", content[40:44])[0]
        parts_offset = 44
        points_offset = parts_offset + num_parts * 4
        parts = list(struct.unpack(f"<{num_parts}i", content[parts_offset:points_offset]))
        points_raw = struct.unpack(f"<{num_points * 2}d", content[points_offset : points_offset + num_points * 16])
        points = [[round(points_raw[i], 6), round(points_raw[i + 1], 6)] for i in range(0, len(points_raw), 2)]
        rings = []
        for idx, start in enumerate(parts):
            end = parts[idx + 1] if idx + 1 < len(parts) else num_points
            ring = points[start:end]
            if len(ring) < 4:
                continue
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            rings.append(simplify_ring(ring))
        if not rings:
            shapes.append({"type": None, "coordinates": []})
        elif len(rings) == 1:
            shapes.append({"type": "Polygon", "coordinates": rings})
        else:
            # Treat each part as its own polygon. That is robust for map display
            # and avoids huge invalid single polygons across disjoint approvals.
            shapes.append({"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]})
    return shapes


def clean_props(row: dict[str, str], layer: dict[str, str]) -> dict[str, str]:
    name = row.get("SCHE_NAME") or row.get("GEO_FIELD") or row.get("SCHEME_NO") or layer["label"]
    return {
        "name": name,
        "kind": layer["kind"],
        "layer": layer["label"],
        "scheme_no": row.get("SCHEME_NO", ""),
        "scheme_type": row.get("SCHEME_TYP", ""),
        "status": row.get("SCH_STATUS", ""),
        "holder": row.get("APP_HOLDER", ""),
        "field": row.get("PROD_FIELD") or row.get("GEO_FIELD", ""),
        "pool": row.get("PROD_POOL") or row.get("GEO_POOL", ""),
        "source": "AER Scheme Approval Spatial Data",
    }


def build() -> dict:
    if not SOURCE_ZIP.exists():
        raise FileNotFoundError(f"Missing {SOURCE_ZIP}")
    features = []
    with ZipFile(SOURCE_ZIP) as z:
        names = set(z.namelist())
        for layer in LAYERS:
            base = f"Shapefiles/{layer['folder']}/{layer['stem']}"
            shp = f"{base}.shp"
            dbf = f"{base}.dbf"
            if shp not in names or dbf not in names:
                raise FileNotFoundError(f"Missing {shp} or {dbf} in {SOURCE_ZIP}")
            shapes = read_polygon_shapes(z, shp)
            rows = read_dbf(z, dbf)
            for shape, row in zip(shapes, rows):
                if not shape["type"]:
                    continue
                features.append(
                    {
                        "type": "Feature",
                        "properties": clean_props(row, layer),
                        "geometry": shape,
                    }
                )
    return {
        "type": "FeatureCollection",
        "name": "AER scheme approval footprints",
        "features": features,
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = build()
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(payload['features'])} features")


if __name__ == "__main__":
    main()
