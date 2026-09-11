"""Regression tests for production units, source identity and data integrity."""
import datetime as dt
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import run_etl as etl
import production_refresh as refresh
import official_source_discovery as discovery


class ProductionIntegrityTests(unittest.TestCase):
    def test_bcer_geometry_refresh_requires_complete_counted_pages(self):
        feature = dict(type="Feature", properties={}, geometry=None)
        for last_page, expected in [([feature], "downloaded"), ([], "failed")]:
            responses = [dict(count=3), dict(type="FeatureCollection", features=[feature, feature]), dict(type="FeatureCollection", features=last_page)]
            with self.subTest(status=expected), patch.object(Path, "mkdir"), patch.object(etl, "write_json_file") as writer, \
                 patch.object(etl.urllib.request, "urlopen", side_effect=[io.BytesIO(json.dumps(row).encode()) for row in responses]):
                result = etl.download_bcer_well_surface_points(force=True)
                self.assertEqual(result["status"], expected)
                if expected == "downloaded":
                    self.assertEqual(len(writer.call_args.args[1]["features"]), 3)
                else:
                    writer.assert_not_called()

    def test_actual_compact_asset_schema_round_trips_without_optional_metadata(self):
        asset = etl.Asset("site", "01-01-001-01W4", "petrinex_ab_conventional_vol", "AB", "conventional", "dls_site", "Operator", "Alberta", 51.5, -113.5,
                          coordinate_method="ags_ats_v4_1_web_converter", location_confidence="medium", geometry_kind="dls_centroid")
        payload = etl.compact_asset_payload([vars(asset)])
        self.assertNotIn("source_name", payload["fields"])
        restored = refresh.asset_from_public_row(etl, refresh.asset_payload_rows(payload)[0])
        self.assertEqual(restored.source_name, etl.source_name(asset.source_id))
        self.assertEqual(restored.geometry_kind, "dls_centroid")
        self.assertIn(("Alberta", "01-01-001-01W4"), refresh.seed_published_dls(etl, {restored.asset_id: restored}))

    def test_weekly_scan_only_adds_changed_historical_petrinex_tokens(self):
        periods = ["2024-01", "2026-04", "2026-05", "2026-06", "2026-07"]
        source = "petrinex_ab_conventional_vol"
        found = [dict(period=period, updated_at="new", timestamp_timezone="unspecified", url="https://www.petrinex.gov.ab.ca/PublicData?Jurisdiction=AB") for period in periods]
        baseline = dict(source_coverage=[dict(source_id=source, scenario="actual", first_date="2024-01-31", last_date="2026-07-31")],
                        source_state=dict(files={}, publication_tokens={f"{source}:{period}": dict(updated_at="old" if period == "2024-01" else "new") for period in periods}))
        args = SimpleNamespace(offline=False, history_start=None, update_months=3, full_revision_scan=True)
        with patch.object(discovery, "discover_petrinex_months", return_value=found):
            rows, _ = refresh.collect_inputs(etl, args, {"petrinex-ab"}, baseline)
        self.assertEqual({row["period"] for row in rows if row.get("period")}, {"2024-01", "2026-05", "2026-06", "2026-07"})
        args.full_revision_scan = False
        with patch.object(discovery, "discover_petrinex_months", return_value=found):
            rows, _ = refresh.collect_inputs(etl, args, {"petrinex-ab"}, baseline)
        self.assertEqual({row["period"] for row in rows if row.get("period")}, {"2026-05", "2026-06", "2026-07"})
        self.assertEqual(args.publication_tokens[f"{source}:2024-01"]["updated_at"], "old")

    def test_fingerprint_match_skips_parse_and_offline_is_not_a_web_check(self):
        with tempfile.NamedTemporaryFile(dir=etl.ROOT, suffix=".json", delete=False) as temporary:
            path = Path(temporary.name)
            temporary.write(b"official source bytes")
        try:
            fingerprint = refresh.sha256_file(path)
            descriptor = dict(source_id="aer_st53", raw_file=path.name, url="https://example.invalid/report.json", current=True)
            prior = {path.name: dict(sha256=fingerprint)}
            args = SimpleNamespace(offline=False, full_revision_scan=False)
            with patch.object(etl, "RAW_DIR", etl.ROOT), patch.object(etl, "download_url", return_value=dict(status="downloaded", error=None)):
                live = refresh.check_inputs(etl, args, [descriptor], prior)[0]
                args.offline = True
                offline = refresh.check_inputs(etl, args, [descriptor], prior)[0]
            self.assertFalse(live["content_changed"])
            self.assertEqual(live["sha256"], fingerprint)
            self.assertEqual(live["checked_at"], etl.RUN_DATE.isoformat())
            self.assertIsNone(offline["checked_at"])
            self.assertEqual(offline["mode"], "offline")
        finally:
            path.unlink(missing_ok=True)

    def test_seed_rejects_workbook_history_forecasts_and_saskatchewan_st39(self):
        assets = {"ab": {"province": "Alberta", "asset_kind": "in_situ_scheme"},
                  "sk": {"province": "Saskatchewan", "asset_kind": "upgrader"}}
        record = dict(asset_id="ab", source_id="aer_st53", scenario="actual", workbook_sheet="In-Situ (All Sites)")
        self.assertFalse(refresh.keep_official_record(record, assets))
        record["workbook_sheet"] = "Official aer_st53 current XLS"
        self.assertTrue(refresh.keep_official_record(record, assets))
        self.assertFalse(refresh.keep_official_record({**record, "scenario": "forecast"}, assets, True))
        self.assertFalse(refresh.keep_official_record({**record, "asset_id": "sk", "source_id": "aer_st39"}, assets, True))

    def test_partition_replacement_is_idempotent_and_removes_deleted_wells(self):
        def row(aid, month, value):
            return dict(asset_id=aid, date=month + "-30", source_id="source", stream="oil", volume_bbl_d=value * 1000, volume_kbbl_d=value)
        old = [row("deleted", "2026-06", 10), row("retained_history", "2026-04", 20)]
        new = [row("reported_zero", "2026-06", 0)]
        once = refresh.replace_partitions(old, new, {"source"}, {"2026-06"})
        twice = refresh.replace_partitions(once, new, {"source"}, {"2026-06"})
        self.assertEqual(once, twice)
        self.assertEqual({row["asset_id"] for row in twice}, {"retained_history", "reported_zero"})

    def test_current_report_regression_and_dropped_product_fail_closed(self):
        old = [dict(source_id="source", stream="oil", date="2026-06-30"),
               dict(source_id="source", stream="condensate", date="2026-06-30")]
        with self.assertRaisesRegex(ValueError, "dropped previously published"):
            refresh.guard_source_replacement(old, old[:1], {"source"}, {"2026-06"})
        with self.assertRaisesRegex(ValueError, "coverage regressed"):
            refresh.guard_source_replacement(old[:1], [dict(source_id="source", stream="oil", date="2026-05-31")], {"source"}, {"2026-05"}, True)
        with self.assertRaisesRegex(ValueError, "Active official product streams"):
            refresh.guard_source_replacement(old, [dict(source_id="source", stream="oil", date="2026-07-31")], {"source"}, {"2026-07"}, active_streams=True)
        historical = dict(source_id="source", stream="oil", date="2024-01-31")
        refresh.guard_source_replacement(old + [historical], [historical], {"source"}, {"2024-01"}, active_streams=True)

    def test_cold_runner_keeps_published_higher_confidence_dls_coordinates(self):
        assets = {"site": etl.Asset("site", "01-01-001-01W4", "petrinex_ab_conventional_vol", "AB", "conventional", "dls_site", "Operator", "Alberta", 51.5, -113.5,
                                    coordinate_method="ags_ats_v4_1_web_converter", location_confidence="medium", location_basis="well_dls_current_link", geometry_kind="dls_centroid")}
        add_asset, _ = refresh.make_callbacks(etl, assets, [])
        add_asset(asset_id_override="site", display_name="01-01-001-01W4", source_id="petrinex_ab_conventional_vol", production_system="conventional", company="Operator",
                  asset_kind="dls_site", province="Alberta", latitude=50.0, longitude=-110.0, coordinate_method="approx_dls_centroid", geometry_kind="dls_centroid")
        self.assertEqual((assets["site"].latitude, assets["site"].longitude), (51.5, -113.5))
        with patch.object(etl, "BASELINE_DLS_CACHE", refresh.seed_published_dls(etl, assets)), patch.object(etl, "load_dls_cache") as private_cache:
            result = etl.resolve_dls_locations([dict(province="Alberta", dls="01-01-001-01W4", volume_bbl_d=1)], 0)
        private_cache.assert_not_called()
        self.assertEqual(float(result["Alberta", "01-01-001-01W4"]["latitude"]), 51.5)

    def test_callbacks_reject_forecast_rows(self):
        _, add_record = refresh.make_callbacks(etl, {}, [])
        with self.assertRaisesRegex(ValueError, "Only directly sourced actual"):
            add_record(dt.date(2026, 6, 1), "a", "oil", 1, "report", "row", "aer_st53", scenario="forecast")

    def test_unchanged_successful_download_has_no_transform_work(self):
        baseline = dict(dataset_mode=refresh.DATASET_MODE, pipeline_version=refresh.PIPELINE_VERSION)
        checks = [dict(source_id="aer_st53", status="downloaded", raw_path="aer_st53_current.xls", sha256="a" * 64, content_changed=False)]
        result_path = etl.PROCESSED_DIR / "fixture-result.json"
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "read_text", return_value=json.dumps(baseline)), \
             patch.object(Path, "mkdir"), patch.object(etl, "write_json_file") as writer, patch.object(etl, "write_web_exports") as exporter, \
             patch.object(refresh, "collect_inputs", return_value=([], [])), patch.object(refresh, "check_inputs", return_value=checks), \
             patch.object(refresh, "load_baseline") as loader:
            status = refresh.main(etl, ["--output-dir", str(etl.PROCESSED_DIR / "fixture-candidate"), "--result-json", str(result_path), "--sources", "aer"])
        self.assertEqual(status, 0)
        loader.assert_not_called()
        exporter.assert_not_called()
        writer.assert_called_once()
        result = writer.call_args.args[1]
        self.assertEqual(result["status"], "noop")
        self.assertEqual(result["checks"], checks)

    def test_failed_published_input_never_writes_a_candidate(self):
        baseline = dict(dataset_mode=refresh.DATASET_MODE, pipeline_version=refresh.PIPELINE_VERSION)
        checks = [dict(source_id="aer_st53", status="failed", raw_path="aer_st53_current.xls", error="HTTP 500", content_changed=False)]
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "read_text", return_value=json.dumps(baseline)), \
             patch.object(Path, "mkdir"), patch.object(etl, "write_json_file"), patch.object(etl, "write_web_exports") as exporter, \
             patch.object(refresh, "collect_inputs", return_value=([], [])), patch.object(refresh, "check_inputs", return_value=checks), \
             patch.object(refresh, "load_baseline") as loader:
            status = refresh.main(etl, ["--output-dir", str(etl.PROCESSED_DIR / "fixture-candidate"), "--sources", "aer"])
        self.assertEqual(status, 1)
        loader.assert_not_called()
        exporter.assert_not_called()

    def test_date_strings_do_not_use_format_length_as_input_length(self):
        self.assertEqual(etl.as_date("2026-07-31"), dt.date(2026, 7, 31))
        self.assertEqual(etl.as_date("2026-07"), dt.date(2026, 7, 1))
        self.assertEqual(etl.as_date("2026-07-31 00:00:00"), dt.date(2026, 7, 31))

    def test_numeric_input_rejects_infinite_values(self):
        for value in (float("inf"), float("-inf"), "Infinity", "NaN"):
            self.assertIsNone(etl.as_float(value))
        self.assertEqual(etl.as_float("1,234.5"), 1234.5)

    def test_approval_ids_keep_distinct_st39_facilities(self):
        self.assertEqual(etl.approval_root("ABOS0093231"), "93231")
        self.assertEqual(etl.approval_root("10097AAAA"), "10097")
        self.assertNotEqual(etl.approval_root("ABOS0093231"), etl.approval_root("ABOS0077189"))

    def test_conventional_crude_excludes_primary_bitumen_wells(self):
        self.assertTrue(etl.is_bitumen_well({"well_status_fluid": "CR-BIT"}))
        self.assertFalse(etl.is_bitumen_well({"well_status_fluid": "CR-OIL"}))
        self.assertFalse(etl.is_bitumen_well({}))

    def test_fast_reader_preserves_only_supported_liquid_activities(self):
        source = "ActivityID,ProductID,Volume\nPROD,OIL,12\nREC,OIL,99\nPROD,GAS,33\nPROC,C5-SP,2\nFRAC,C5-SP,3\n"
        import csv
        with patch.object(etl, "open_nested_petrinex_csv", return_value=csv.DictReader(io.StringIO(source))):
            rows = list(etl.iter_petrinex_liquids_rows(Path("unused.zip")))
        self.assertEqual([row["Volume"] for row in rows], ["12", "2", "3"])

    def test_new_positive_st39_facility_cannot_be_silently_dropped(self):
        row = dict(approval="ABOS0999999", stream="Synthetic crude oil", value=10)
        with patch.object(etl, "extract_aer_current", side_effect=lambda source: [row] if source == "aer_st39" else []):
            with self.assertRaisesRegex(ValueError, "requires approval mapping"):
                etl.overlay_official_aer_current({}, [], None, None, {})

    def test_manitoba_accepts_current_spaced_workbook_headers(self):
        workbook = MagicMock()
        sheet = MagicMock()
        sheet.iter_rows.return_value = iter([
            ["LICENCE", "WELL NAME", "UWI", "NAME", "FLUID TYPE", "YEAR", "JAN"],
            ["123", "Example Well", "100.03-29-016-27W1.00", "Operator", "OIL", 2024, 31.0],
        ])
        workbook.worksheets = [sheet]
        archive = MagicMock()
        archive.__enter__.return_value.namelist.return_value = ["production.xlsx"]
        archive.__enter__.return_value.read.return_value = b"fixture"
        added = []
        with patch.object(etl, "MANITOBA_PRODUCTION_ZIP", MagicMock()), \
             patch.object(etl._zipfile, "ZipFile", return_value=archive), \
             patch.object(etl.openpyxl, "load_workbook", return_value=workbook), \
             patch.object(etl, "resolve_dls_locations", return_value={}):
            etl.append_manitoba_well_production(lambda **kwargs: "mb", lambda *args, **kwargs: added.append(args), "2024-01")
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0][0], dt.date(2024, 1, 1))
        self.assertAlmostEqual(added[0][3], etl.M3_TO_BBL)

    def test_html_response_preserves_last_good_cache(self):
        # A clean checkout has no ignored data/processed cache directory.
        with tempfile.NamedTemporaryFile(dir=etl.ROOT, suffix=".zip", delete=False) as temporary:
            target = Path(temporary.name)
            temporary.write(b"last good cache")
        try:
            with patch.object(etl.urllib.request, "urlopen", return_value=io.BytesIO(b"<!DOCTYPE html><html>Error</html>")):
                result = etl.download_url("https://example.invalid/report.zip", target, force=True)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["cached_fallback"])
            self.assertEqual(target.read_bytes(), b"last good cache")
        finally:
            target.unlink(missing_ok=True)

    def test_opening_month_requires_every_regular_source(self):
        records = []
        for date in ("2026-04-30", "2026-05-31"):
            for source, stream in (("aer_st53", "In-situ bitumen"), ("aer_st39", "Mined bitumen gross"),
                                   ("aer_st39", "Synthetic crude oil"), ("ndic", "Conventional crude oil")):
                records.append(dict(date=date, source_id=source, source_name=source, stream=stream,
                                    scenario="actual", volume_kbbl_d=1000, asset_id=source + stream))
        records.append(dict(date="2026-04-30", source_id="petrinex_ab", source_name="AB", stream="Conventional crude oil",
                            scenario="actual", volume_kbbl_d=700, asset_id="ab"))
        self.assertEqual(etl.derive_default_map_date(records, "2026-05-31"), "2026-04-30")

    def test_official_overlay_units_forecasts_zeros_and_provincial_scope(self):
        assets = {
            "ab": etl.Asset("ab", "Cold Lake", "aer_st53", "ST53", "in_situ", "in_situ_scheme", "Imperial Oil", "Alberta", None, None),
            "sk": etl.Asset("sk", "Lloydminster", "aer_st39", "ST39", "synthetic", "upgrader", "Cenovus", "Saskatchewan", None, None),
        }
        records = [dict(asset_id="ab", source_id="aer_st53", period="2024-02", scenario="forecast", volume_bbl_d=9999),
                   dict(asset_id="sk", source_id="aer_st39", period="2024-02", scenario="actual", volume_bbl_d=123)]

        def add_asset(**kwargs):
            aid = kwargs.pop("asset_id_override")
            if aid not in assets:
                kwargs.setdefault("province", "Alberta")
                assets[aid] = etl.Asset(asset_id=aid, source_name="test", **kwargs)
            return aid

        def add_record(date, aid, stream, value, sheet, column, source, scenario):
            records.append(dict(asset_id=aid, source_id=source, stream=stream, period=date.strftime("%Y-%m"),
                                volume_bbl_d=value, scenario=scenario))

        source_rows = {
            "aer_st53": [dict(operator="Imperial Oil Resources Limited", facility="Cold Lake", approval="8558III", area="Cold Lake",
                             recovery="Commercial-CSS", stream="In-situ bitumen", period=period, value=value, units="m3/d")
                         for period, value in (("2024-02", 100), ("2024-03", 0))],
            "aer_st39": [dict(operator="Canadian Natural Resources Limited", facility="Horizon", approval="ABOS0093231", area="",
                             recovery="", stream="Mined bitumen gross", period="2024-02", value=2900, units="m3/month")],
        }
        with patch.object(etl, "extract_aer_current", side_effect=lambda source: source_rows[source]), \
             patch.object(etl, "official_approval_location", return_value={}), \
             patch.object(etl, "resolve_oil_sands_asset_location", return_value={}):
            etl.overlay_official_aer_current(assets, records, add_asset, add_record, {})
        self.assertEqual(len(records), 4)
        self.assertTrue(all(r["scenario"] == "actual" for r in records))
        self.assertEqual(next(r["volume_bbl_d"] for r in records if r["asset_id"] == "sk"), 123)
        self.assertEqual(next(r["volume_bbl_d"] for r in records if r["period"] == "2024-03"), 0)
        for row in records:
            if row["asset_id"] != "sk" and row["period"] == "2024-02":
                self.assertAlmostEqual(row["volume_bbl_d"], 628.981077)


if __name__ == "__main__":
    unittest.main()
