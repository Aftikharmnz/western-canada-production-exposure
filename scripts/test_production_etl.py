"""Regression tests for production units, source identity and data integrity."""
import datetime as dt
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import run_etl as etl


class ProductionIntegrityTests(unittest.TestCase):
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
