"""Release-boundary regressions; no live requests, commits, pushes or alerts."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import archive_elt_sources as archive
import elt_pipeline as pipeline
import publish_data_update as publish


class ReleaseBoundaryTests(unittest.TestCase):
    def test_infrastructure_refresh_metadata_does_not_advance_data_update(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            baseline, work = root / "published", root / "work"
            baseline.mkdir()
            pipeline.write_json(baseline / "manifest.json", {})
            pipeline.write_json(baseline / "elt_status.json", {"infrastructure": {"last_data_update": "2026-09-01"}})
            feature = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[-113, 52], [-112, 53]]},
                       "properties": {"status": "Operating", "checked_at": "asset observation date"}}
            layer = {"type": "FeatureCollection", "metadata": {"generated_at": "old", "source_retrieved_at": "old",
                     "source_last_modified": "old", "source_sha256": "old", "attribute_units": {"h2s_pct": "mole percent"}},
                     "features": [feature]}
            for name in pipeline.INFRASTRUCTURE_GEOJSON_FILES:
                pipeline.write_json(baseline / name, layer)
            index = {"generated_at": "old", "builder_version": 2, "sources": {"pipelines": {
                "url": "https://www.aer.ca/data/pipeline/Pipelines_SHP.zip", "sha256": "old", "bytes": 10,
                "checked_at": "old", "retrieved_at": "old", "source_last_modified": "old", "etag": "old",
                "content_changed": True, "download_content_changed": True, "fetch_status": "downloaded"}}}
            pipeline.write_json(baseline / "aer_pipeline_index.json", index)
            def refresh(script, arguments, logs, timeout):
                candidate = work / "candidate"
                if script == "build_aer_infrastructure.py":
                    updated = copy.deepcopy(index)
                    updated["generated_at"] = "new"
                    receipt = updated["sources"]["pipelines"]
                    receipt.update({key: "new" for key in pipeline.AER_REFRESH_RECEIPT_FIELDS})
                    pipeline.write_json(candidate / "aer_pipeline_index.json", updated)
                    names = {"aer_feeder_pipelines.geojson", "aer_pipeline_installations.geojson"}
                elif script == "build_market_access_pipelines.py":
                    self.assertEqual(arguments[arguments.index("--aer-feeder-input") + 1], str(candidate / "aer_feeder_pipelines.geojson"))
                    names = {"market_access_pipelines.geojson"}
                elif script == "build_railway_layer.py":
                    names = {"railways.geojson"}
                else:
                    return
                for name in names:
                    updated = copy.deepcopy(layer)
                    updated["metadata"].update({key: "new" for key in pipeline.GEOJSON_REFRESH_METADATA})
                    pipeline.write_json(candidate / name, updated)
            arguments = ["elt_pipeline", "--mode", "infrastructure", "--baseline-dir", str(baseline), "--work-dir", str(work), "--skip-references"]
            with patch("sys.argv", arguments), patch.object(pipeline, "run_script", side_effect=refresh), \
                 patch.object(pipeline.subprocess, "check_output", return_value="abc123"):
                self.assertEqual(pipeline.main(), 0)
            status = pipeline.read_json(work / "candidate/elt_status.json")["infrastructure"]
            self.assertEqual(status["status"], "unchanged")
            self.assertEqual(status["last_data_update"], "2026-09-01")
            self.assertIsNotNone(status["checked_at"])
            self.assertFalse(pipeline.read_json(work / "pipeline_result.json")["data_changed"])

    def test_infrastructure_geometry_properties_and_meaningful_metadata_are_changes(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            baseline, candidate = root / "before", root / "after"
            layer = {"type": "FeatureCollection", "metadata": {"generated_at": "old", "attribute_units": {"h2s_pct": "incorrect"}},
                     "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-113, 52]},
                                   "properties": {"h2s_pct": 1, "checked_at": "asset observation"}}]}
            name = "aer_pipeline_installations.geojson"
            pipeline.write_json(baseline / name, layer)
            edits = [lambda value: value["features"][0]["geometry"].update(coordinates=[-112, 53]),
                     lambda value: value["features"][0]["properties"].update(h2s_pct=0.1),
                     lambda value: value["features"][0]["properties"].update(checked_at="new asset observation"),
                     lambda value: value["metadata"]["attribute_units"].update(h2s_pct="mole percent")]
            for edit in edits:
                updated = copy.deepcopy(layer)
                edit(updated)
                pipeline.write_json(candidate / name, updated)
                self.assertTrue(pipeline.infrastructure_data_changed(baseline, candidate, [name]))
            index_name = "aer_pipeline_index.json"
            pipeline.write_json(baseline / index_name, {"builder_version": 1, "sources": {}})
            pipeline.write_json(candidate / index_name, {"builder_version": 2, "sources": {}})
            self.assertTrue(pipeline.infrastructure_data_changed(baseline, candidate, [index_name]))
            self.assertTrue(pipeline.infrastructure_data_changed(baseline, candidate, ["pipeline_tiles/new.geojson"]))
            (candidate / name).unlink()
            self.assertTrue(pipeline.infrastructure_data_changed(baseline, candidate, [name]))

    def test_geojson_digest_streams_features_without_decoding_the_geometry_array(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            path = Path(directory) / "large.geojson"
            layer = {"type": "FeatureCollection", "metadata": {"generated_at": "old", "note": 'text with "features": [] ' * 5000},
                     "features": [{"properties": {"long_field": "x" * 200000}, "geometry": None}]}
            pipeline.write_json(path, layer)
            with patch.object(pipeline.json, "loads", side_effect=AssertionError("Geometry must not be loaded as one JSON object")):
                before = pipeline.infrastructure_geojson_digest(path)
                layer["metadata"]["generated_at"] = "new"
                pipeline.write_json(path, layer)
                self.assertEqual(before, pipeline.infrastructure_geojson_digest(path))

    def test_failed_check_does_not_advance_last_good_ingestion(self):
        previous = {"production": {"last_data_update": "2026-09-01"}}
        result = pipeline.release_status(previous, mode="production", timestamp="2026-09-10", data_changed=True,
                                         failed=True, warnings=[], run_url=None, manifest={})
        self.assertEqual(result["production"]["last_data_update"], "2026-09-01")
        self.assertEqual(result["production"]["status"], "failed")
        self.assertEqual(previous["production"]["last_data_update"], "2026-09-01")

    def test_publication_rejects_arbitrary_paths(self):
        for name in ("../index.html", "/public/data/x", "src/main.js", "HANDOFF_STATICRYPT.md", "public/data/../../.env", "public/data/..\\..\\.env", "public/data//x"):
            self.assertFalse(publish.allowed_path(name), name)
        self.assertTrue(publish.allowed_path("public/data/monthly/on_demand_2026-07-31.json"))
        self.assertTrue(publish.allowed_path("data/alerts/state.json"))

    def test_concurrent_aeso_is_preserved_but_source_or_parser_conflicts_block(self):
        candidate = {"public/data/manifest.json", "public/data/assets.json"}
        self.assertEqual(publish.conflicting_changes({"public/data/aeso_power_status.json", "data/alerts/state.json"}, candidate), set())
        self.assertEqual(publish.conflicting_changes({"public/data/manifest.json"}, candidate), {"public/data/manifest.json"})
        self.assertEqual(publish.conflicting_changes({"scripts/run_etl.py"}, candidate), {"scripts/run_etl.py"})
        self.assertEqual(publish.conflicting_changes({"data/pipeline_route_facts.json"}, candidate), {"data/pipeline_route_facts.json"})

    def test_failed_candidate_promotes_only_failure_status(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            baseline, work = root / "published", root / "work"
            baseline.mkdir()
            (baseline / "manifest.json").write_text('{"latest_actual_date":"2026-07-31"}')
            (baseline / "assets.json").write_text('"last-good"')
            def fail(_script, _arguments, _logs, timeout):
                (work / "candidate/assets.json").write_text('"bad-candidate"')
                raise RuntimeError("Rejected schema")
            arguments = ["elt_pipeline", "--baseline-dir", str(baseline), "--work-dir", str(work), "--offline", "--promote"]
            with patch("sys.argv", arguments), patch.object(pipeline, "run_script", side_effect=fail), \
                 patch.object(pipeline.subprocess, "check_output", return_value="abc123"):
                self.assertEqual(pipeline.main(), 1)
            self.assertEqual((baseline / "assets.json").read_text(), '"last-good"')
            self.assertEqual(json.loads((baseline / "elt_status.json").read_text())["production"]["status"], "failed")
            self.assertEqual(json.loads((work / "pipeline_result.json").read_text())["changed_paths"], ["public/data/elt_status.json"])

    def test_raw_archive_requires_checksum_and_stays_within_raw_root(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            source = root / "official.xlsx"
            source.write_bytes(b"official fixture")
            receipt = {"raw_path": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "url": "https://agency.example/report.xlsx", "status": "downloaded", "content_changed": True}
            result = {"status": "success", "checks": [receipt]}
            manifest = archive.package_sources(result, root / "archive", root)
            self.assertEqual(len(manifest["source_files"]), 1)
            with zipfile.ZipFile(root / "archive/official-inputs-001.zip") as bundle:
                self.assertEqual(bundle.read(source.name), source.read_bytes())
            source.write_bytes(b"unvalidated revision")
            with self.assertRaisesRegex(ValueError, "receipt"):
                archive.reviewed_inputs(result, root)
            receipt["raw_path"] = "../outside.xlsx"
            with self.assertRaisesRegex(ValueError, "escaped"):
                archive.reviewed_inputs(result, root)

    def test_partial_promotion_cannot_authorize_a_release(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            baseline, work = root / "published", root / "work"
            baseline.mkdir()
            (baseline / "manifest.json").write_text('{}')
            arguments = ["elt_pipeline", "--baseline-dir", str(baseline), "--work-dir", str(work), "--offline", "--promote"]
            with patch("sys.argv", arguments), patch.object(pipeline, "run_script"), \
                 patch.object(pipeline.subprocess, "check_output", return_value="abc123"), \
                 patch.object(pipeline, "promote_files", side_effect=OSError("Disk full during replacement")):
                with self.assertRaises(OSError):
                    pipeline.main()
            self.assertFalse((work / "pipeline_result.json").exists(), "No success receipt may authorize publication of a partial checkout")

    def test_unchanged_or_failed_sources_are_not_archived_as_new_inputs(self):
        check = {"raw_path": "missing.zip", "sha256": "unused", "url": "https://agency.example/source", "content_changed": False}
        self.assertEqual(archive.reviewed_inputs({"status": "success", "checks": [check]}), [])
        check["content_changed"] = True
        self.assertEqual(archive.reviewed_inputs({"status": "failed", "checks": [check]}), [])

    def test_promote_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipeline.ROOT) as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "escaped"):
                pipeline.promote_files(root / "published", root / "candidate", ["../outside"])


if __name__ == "__main__":
    unittest.main()
