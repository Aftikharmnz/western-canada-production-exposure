"""Offline synthetic SHP/CSV regression tests for the AER infrastructure importer."""
import copy
import collections
import csv
import io
import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import shapefile
import build_aer_infrastructure as aer

WKT = 'GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'


def rows_for(kind):
    rows = []
    if kind == "pipelines":
        for index, substance in enumerate(aer.LINE_CATEGORIES):
            row = {field: "" for field in aer.PIPE_FIELDS.values()}
            row.update(LICENCE_NO="100", PLLICSEGID=str(index + 1), LINE_NO=str(index + 1), COMP_NAME="Fixture Operator",
                       SEG_STATUS="Permitted" if index == 1 else "Operating", SUBSTANCE1=substance,
                       SEG_LENGTH="1.5", OUT_DIAMET="323.9", PIPE_MAOP="9000", GEOM_SRCE="As-Built")
            rows.append(row)
    else:
        for index, inst_type in enumerate(aer.INSTALL_CATEGORIES):
            row = {field: "" for field in aer.INSTALL_FIELDS.values()}
            row.update(INSTA_LIC="200", LICINSTNO=f"200-{index + 1}", BA_NAME="Fixture Operator",
                       INSTA_TYPE=inst_type, PLINSTATUS="Operating", SUBSTANCE1="Natural Gas", POWER="0", GEOM_SRCE="Mapping")
            if inst_type == "Meter Regulator Stn.":
                row["PLINSTATUS"] = "Suspended"
            elif inst_type == "Line Heater":
                row["PLINSTATUS"] = "Abandoned"
            elif inst_type == "Oil Terminal":
                row["PLINSTATUS"] = "Permitted"
            rows.append(row)
    return rows


def write_fixture(path, kind, rows=None, mismatch=False, wrong_crs=False, null_shape=False):
    source = aer.SOURCES[kind]
    fields = aer.PIPE_FIELDS if kind == "pipelines" else aer.INSTALL_FIELDS
    rows = rows_for(kind) if rows is None else rows
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    writer = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=3 if kind == "pipelines" else 1)
    for name in fields.values():
        writer.field(name, "C", size=70)
    for index, row in enumerate(rows):
        writer.record(*(row.get(name, "") for name in fields.values()))
        if null_shape and index == 0:
            writer.null()
        elif kind == "pipelines":
            # Duplicate records intentionally also have identical geometries.
            writer.line([[[-119.7, 53.0], [-112.0, 53.0]]])
        else:
            writer.point(-114, 53)
    writer.close()
    csv_body = io.StringIO(newline="")
    columns = [source["csv_id"], source["csv_status"], source["csv_substance"]]
    csv_writer = csv.writer(csv_body)
    csv_writer.writerow(columns)
    for index, row in enumerate(rows):
        csv_writer.writerow(["wrong" if mismatch and index == 0 else row[source["dbf_id"]], row[source["dbf_status"]], row["SUBSTANCE1"]])
    with ZipFile(path, "w") as archive:
        for extension, data in [("shp", shp.getvalue()), ("shx", shx.getvalue()), ("dbf", dbf.getvalue()),
                                ("prj", (WKT.replace("North_American_1983", "WGS_1984") if wrong_crs else WKT).encode()), ("cpg", b"UTF-8")]:
            archive.writestr(f"official/{source['stem']}.{extension}", data)
        archive.writestr(f"official/{source['csv']}", csv_body.getvalue())
        archive.writestr(f"official/Unmapped {source['csv']}", ",".join(columns) + "\n9999,Operating,Natural Gas\n")
    return path


class AerInfrastructureTests(unittest.TestCase):
    def test_h2s_source_units_zero_missing_and_physical_range(self):
        for missing in (None, "", "   "):
            self.assertEqual(aer.h2s_fields(missing), {})
        self.assertEqual(aer.h2s_fields("0"), {"h2s_mol_kmol": 0.0, "h2s_pct": 0.0})
        self.assertEqual(aer.h2s_fields("34"), {"h2s_mol_kmol": 34.0, "h2s_pct": 3.4})
        self.assertEqual(aer.h2s_fields("9.99"), {"h2s_mol_kmol": 9.99, "h2s_pct": 0.999})
        self.assertEqual(aer.h2s_fields("999")["h2s_pct"], 99.9)
        self.assertEqual(aer.h2s_fields(1000)["h2s_pct"], 100.0)
        for invalid in (-0.01, "1000.01", "NaN", "Infinity", float("-inf"), "unknown", True):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                aer.h2s_fields(invalid)

    def test_source_attributes_are_preserved_and_h2s_is_converted_for_both_layers(self):
        for kind in aer.SOURCES:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
                work = Path(directory)
                rows = rows_for(kind)
                rows[0]["H2S_CONT"], rows[1]["H2S_CONT"], rows[2]["H2S_CONT"] = "34", "0", ""
                if kind == "pipelines":
                    rows[0].update(PIPE_ENVIR="River Crossing", SUBSTANCE2="Crude Oil", SUBSTANCE3="Condensate", IS_NEB="N")
                result = aer.convert_archive(write_fixture(work / "source.zip", kind, rows), kind, work)
                id_key = "segment_id" if kind == "pipelines" else "inst_id"
                by_id = {f["properties"][id_key]: f["properties"] for f in result["features"]}
                prefix = "" if kind == "pipelines" else "200-"
                nonzero, zero, missing = (by_id[prefix + str(i)] for i in (1, 2, 3))
                self.assertEqual((nonzero["h2s_mol_kmol"], nonzero["h2s_pct"]), (34, 3.4))
                self.assertEqual((zero["h2s_mol_kmol"], zero["h2s_pct"]), (0, 0))
                self.assertNotIn("h2s_mol_kmol", missing)
                self.assertNotIn("h2s_pct", missing)
                self.assertEqual(result["metadata"]["attribute_units"], aer.H2S_UNITS)
                if kind == "pipelines":
                    self.assertEqual({k: nonzero[k] for k in aer.OPTIONAL_FIELDS}, {"environ": "River Crossing", "substance2": "Crude Oil", "substance3": "Condensate", "is_neb": "N"})
                    self.assertNotIn("environ", missing)

    def test_short_parts_keep_precision_and_zero_length_parts_do_not_destroy_valid_linework(self):
        shape = shapefile.Shape(shapeType=3)
        shape.parts = [0, 2, 4]
        shape.points = [[-114, 53], [-114.1, 53.1],
                        [-114.35818545865304, 54.96933092749877], [-114.35818546044969, 54.96933081405658],
                        [-114, 53], [-114, 53]]
        stats = collections.Counter()
        geometry = aer.transformed_geometry(shape, "pipelines", aer.coordinate_transform(WKT), stats)
        self.assertEqual(geometry["type"], "MultiLineString")
        self.assertEqual(len(geometry["coordinates"]), 2)
        self.assertNotEqual(*geometry["coordinates"][1])
        self.assertEqual(stats, {"precision_preserved_parts": 1, "zero_length_parts_excluded": 1})
        shape.parts, shape.points = [0], [[-114, 53], [-114, 53]]
        with self.assertRaisesRegex(ValueError, "no component"):
            aer.transformed_geometry(shape, "pipelines", aer.coordinate_transform(WKT))

    def test_source_reconciliation_filters_and_exact_duplicate_exclusion(self):
        rows = rows_for("pipelines")
        rows.append(copy.deepcopy(rows[0]))
        excluded = copy.deepcopy(rows[0])
        excluded.update(PLLICSEGID="999", SUBSTANCE1="Natural Gas")
        rows.append(excluded)
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            path = write_fixture(work / "pipelines.zip", "pipelines", rows)
            result = aer.convert_archive(path, "pipelines", work)
            counts = result["metadata"]["counts"]
            self.assertEqual((counts["mapped_source_records"], counts["published_features"]), (8, 6))
            self.assertEqual(counts["exact_duplicates_excluded"], 1)
            self.assertEqual(counts["excluded_by_status_or_substance"], 1)
            self.assertEqual(counts["unmapped_source_records"], 1)
            self.assertEqual(len({f["id"] for f in result["features"]}), 6)
            self.assertEqual({f["properties"]["status"] for f in result["features"]}, {"Operating", "Permitted"})
            self.assertLessEqual(result["metadata"]["transform_accuracy_m"], 10)

    def test_equal_count_different_source_identity_wrong_crs_and_null_geometry_fail(self):
        for option in ("mismatch", "wrong_crs", "null_shape"):
            with self.subTest(option=option), tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
                work = Path(directory)
                path = write_fixture(work / "pipeline.zip", "pipelines", **{option: True})
                with self.assertRaises(ValueError):
                    aer.convert_archive(path, "pipelines", work)

    def test_tile_crossings_and_installation_menu_scope_are_preserved(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            layers = {}
            for kind in aer.SOURCES:
                layers[kind] = aer.convert_archive(write_fixture(work / (kind + ".zip"), kind), kind, work)
            checks = {k: dict(sha256="test", retrieved_at="2026-09-10T00:00:00Z") for k in layers}
            stage = work / "stage"
            index = aer.stage_outputs(stage, layers, checks)
            self.assertEqual(aer.validate_outputs(stage), [])
            self.assertEqual(len(layers["installations"]["features"]), 8, "Monolith keeps non-displayed statuses")
            shown = []
            for entry in index["installation_categories"].values():
                shown.extend(aer.read_json(stage / entry["path"].removeprefix("public/data/"))["features"])
            self.assertEqual(len(shown), 7)
            self.assertIn("Suspended", {f["properties"]["status"] for f in shown})
            self.assertNotIn("Abandoned", {f["properties"]["status"] for f in shown})
            feature = layers["pipelines"]["features"][0]
            start, finish = feature["geometry"]["coordinates"]
            mid = [(start[0] + finish[0]) / 2, start[1]]
            mid_tile = "/".join(map(str, aer.lonlat_tile(*mid)))
            self.assertIn(mid_tile, aer.feature_tile_keys(feature), "Tiles crossed without a vertex must still load the line")
            for key, entry in index["line_categories"].items():
                self.assertGreater(entry["tile_count"], 2)
                self.assertEqual(len(entry["tile_keys"]), entry["tile_count"])
                for tile in entry["tile_keys"]:
                    path = stage / f"pipeline_tiles/{key}/8/{tile}.geojson"
                    self.assertEqual(len(aer.read_json(path)["features"]), entry["count"])
            # Remove only stale owned files; other layer data is untouched.
            target = work / "target"
            aer.write_json(target / "pipeline_tiles/pipe-crude/8/1/1.geojson", {"stale": True})
            aer.write_json(target / "pipelines/unrelated.geojson", {"keep": True})
            aer.install_outputs(stage, target)
            self.assertFalse((target / "pipeline_tiles/pipe-crude/8/1/1.geojson").exists())
            self.assertTrue((target / "pipelines/unrelated.geojson").exists())
            self.assertEqual(aer.validate_outputs(target), [])

    def test_output_validator_rejects_count_drift_altered_geometry_and_missing_crossing_tiles(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            layers = {kind: aer.convert_archive(write_fixture(work / (kind + ".zip"), kind), kind, work) for kind in aer.SOURCES}
            checks = {kind: dict(sha256="test", retrieved_at="2026-09-10T00:00:00Z") for kind in layers}
            stage = work / "stage"
            index = aer.stage_outputs(stage, layers, checks)
            key = "pipe-crude"
            entry = index["line_categories"][key]
            middle = entry["tile_keys"][len(entry["tile_keys"]) // 2]
            tile_path = stage / f"pipeline_tiles/{key}/8/{middle}.geojson"
            original_tile = tile_path.read_bytes()
            altered = aer.read_json(tile_path)
            altered["features"][0]["geometry"]["coordinates"][0][0] = -118.7
            aer.write_json(tile_path, altered)
            # This edit preserves bytes and feature count, so aggregate checks
            # alone would miss the geometry error.
            self.assertEqual(tile_path.stat().st_size, len(original_tile))
            self.assertTrue(any("properties or geometry differ" in e for e in aer.validate_outputs(stage)))
            tile_path.write_bytes(original_tile)
            edited_index = copy.deepcopy(index)
            edited_index["line_categories"][key]["count"] += 1
            aer.write_json(stage / "aer_pipeline_index.json", edited_index)
            self.assertTrue(any("category count/bytes" in e for e in aer.validate_outputs(stage)))
            edited_index = copy.deepcopy(index)
            edited_entry = edited_index["line_categories"][key]
            edited_entry["tile_keys"].remove(middle)
            edited_entry["tile_count"] -= 1
            edited_entry["tile_bytes"] -= len(original_tile)
            tile_path.unlink()
            aer.write_json(stage / "aer_pipeline_index.json", edited_index)
            self.assertTrue(any("complete geometry coverage" in e for e in aer.validate_outputs(stage)))
            tile_path.write_bytes(original_tile)
            aer.write_json(stage / "aer_pipeline_index.json", index)
            self.assertEqual(aer.validate_outputs(stage), [])

    def test_output_validation_failure_prevents_installation(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            layers = {kind: aer.convert_archive(write_fixture(work / (kind + ".zip"), kind), kind, work) for kind in aer.SOURCES}
            argv = ["build_aer_infrastructure.py", "--data-dir", str(work / "target"), "--baseline-dir", str(work / "missing-baseline")]
            with patch("sys.argv", argv), \
                 patch.object(aer, "download_source", return_value=(work / "fixture.zip", {"sha256": "test", "retrieved_at": "2026-09-10T00:00:00Z"})), \
                 patch.object(aer, "convert_archive", side_effect=lambda path, kind, directory: layers[kind]), \
                 patch.object(aer, "validate_outputs", return_value=["invalid tile coverage"]), \
                 patch.object(aer, "install_outputs") as install, redirect_stdout(io.StringIO()):
                self.assertEqual(aer.main(), 1)
                install.assert_not_called()

    def test_output_validator_rejects_legacy_tenfold_h2s_unit_error(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            layers = {}
            for kind in aer.SOURCES:
                rows = rows_for(kind)
                rows[0]["H2S_CONT"] = "34"
                layers[kind] = aer.convert_archive(write_fixture(work / (kind + ".zip"), kind, rows), kind, work)
            # Keep every category/tile internally consistent but use the legacy
            # mistaken percentage. Validation must check the unit calculation.
            for feature in layers["pipelines"]["features"]:
                if "h2s_pct" in feature["properties"]:
                    feature["properties"]["h2s_pct"] = 34
            checks = {kind: dict(sha256="test", retrieved_at="2026-09-10T00:00:00Z") for kind in layers}
            stage = work / "stage"
            aer.stage_outputs(stage, layers, checks)
            self.assertTrue(any("H2S conversion is invalid" in error for error in aer.validate_outputs(stage)))

    def test_failure_does_not_modify_existing_candidate_files(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            work = Path(directory)
            target = work / "published"
            aer.write_json(target / "aer_pipeline_index.json", {"unchanged": True})
            fixture = write_fixture(work / "bad.zip", "pipelines", mismatch=True)
            argv = ["build_aer_infrastructure.py", "--data-dir", str(target), "--report", str(work / "report.json")]
            with patch("sys.argv", argv), patch.object(aer, "download_source", return_value=(fixture, {"sha256": "bad"})), redirect_stdout(io.StringIO()):
                self.assertEqual(aer.main(), 1)
            self.assertEqual(aer.read_json(target / "aer_pipeline_index.json"), {"unchanged": True})
            self.assertEqual(aer.read_json(work / "report.json")["status"], "failed")

    def test_cache_requires_matching_source_url_hash_and_304_never_fakes_new_bytes(self):
        source = aer.SOURCES["installations"]
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            raw = Path(directory)
            path = write_fixture(raw / source["raw_file"], "installations")
            receipt_path = path.with_suffix(".receipt.json")
            receipt = dict(url=source["url"], sha256=aer.file_hash(path), etag="reviewed", retrieved_at="2026-09-01T00:00:00Z")
            aer.write_json(receipt_path, receipt)
            _, offline = aer.download_source(source, raw, offline=True)
            self.assertFalse(offline["content_changed"])
            not_modified = urllib.error.HTTPError(source["url"], 304, "Not Modified", {}, None)
            with patch.object(aer.urllib.request, "urlopen", side_effect=not_modified):
                _, checked = aer.download_source(source, raw)
            self.assertEqual(checked["retrieved_at"], receipt["retrieved_at"])
            self.assertFalse(checked["content_changed"])
            path.write_bytes(b"broken cache")
            with self.assertRaisesRegex(ValueError, "matching URL/hash receipt"):
                aer.download_source(source, raw, offline=True)

    def test_archive_change_flag_compares_published_data_not_a_previous_failed_download(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            baseline = Path(directory)
            aer.write_json(baseline / "aer_pipeline_index.json", {"sources": {"pipelines": {"sha256": "old-published"}}})
            cached = {"sha256": "new-cache", "content_changed": False, "fetch_status": "not_modified"}
            checked = aer.publication_check(cached, baseline, "pipelines")
            self.assertTrue(checked["content_changed"], "A failed prior transform must not prevent raw-input archival")
            self.assertFalse(checked["download_content_changed"])

    def test_older_or_future_archive_cannot_replace_published_source(self):
        with tempfile.TemporaryDirectory(dir=aer.ROOT) as directory:
            baseline = Path(directory)
            aer.write_json(baseline / "aer_pipeline_index.json", {"sources": {"pipelines": {"sha256": "published", "source_last_modified": "Wed, 09 Sep 2026 01:55:16 GMT"}}})
            with self.assertRaisesRegex(ValueError, "older"):
                aer.publication_check({"sha256": "older", "source_last_modified": "Tue, 08 Sep 2026 01:55:16 GMT"}, baseline, "pipelines")
            with self.assertRaisesRegex(ValueError, "future"):
                aer.publication_check({"sha256": "future", "source_last_modified": "Wed, 01 Jan 3000 01:55:16 GMT"}, baseline, "pipelines")


if __name__ == "__main__":
    unittest.main()
