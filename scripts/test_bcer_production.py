"""BCER archive layout regressions, including renamed historical partitions."""
import calendar
import csv
import datetime as dt
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import run_etl as etl


class BcerProductionTests(unittest.TestCase):
    @staticmethod
    def production_csv(rows):
        output = io.StringIO(newline="")
        output.write('"ZONE_PRD FILE"\n')
        writer = csv.writer(output)
        writer.writerow(["Wa_num", "Prod_period", "Oil_prod_vol (m3)", "Cond_prod_vol (m3)", "UWI", "Formtn_code"])
        for period, oil, condensate in rows:
            writer.writerow(["123", period, oil, condensate, "100083208317W602", "2900"])
        return output.getvalue()

    def import_archive(self, members):
        assets, records = {}, []

        def add_asset(**kwargs):
            asset_id = kwargs["production_system"]
            assets[asset_id] = kwargs
            return asset_id

        def add_record(date, asset_id, stream, volume, sheet, column, source, **kwargs):
            records.append(dict(date=date, asset_id=asset_id, stream=stream, volume=volume,
                                source=source, scenario=kwargs["scenario"]))

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "prod_csv.zip"
            with zipfile.ZipFile(path, "w") as archive:
                for name, rows in members.items():
                    archive.writestr(name, self.production_csv(rows))
            with patch.object(etl, "BCER_PRODUCTION_ZIP", path), \
                 patch.object(etl, "load_bcer_well_index", return_value={"00123": {"Well Name": "Test well", "Oper": "Test operator"}}), \
                 patch.object(etl, "load_bcer_surface_locations", return_value={"00123": {"latitude": 56.1, "longitude": -121.2}}), \
                 patch.object(etl, "log"):
                etl.append_bcer_well_production(add_asset, add_record)
        return assets, records

    def assert_production(self, records, expected):
        actual = {(row["date"].strftime("%Y-%m"), row["stream"]): row for row in records}
        self.assertEqual(len(records), len(expected))
        self.assertEqual(set(actual), set(expected))
        for key, volume_m3 in expected.items():
            date = actual[key]["date"]
            days = calendar.monthrange(date.year, date.month)[1]
            self.assertAlmostEqual(actual[key]["volume"], volume_m3 * etl.M3_TO_BBL / days)
            self.assertEqual(actual[key]["source"], "bcer_well_production")
            self.assertEqual(actual[key]["scenario"], "actual")

    def test_legacy_two_partition_archive_keeps_history_and_current_production(self):
        assets, records = self.import_archive({
            "zone_prd_2007_to_2015.csv": [("201512", 31, 0)],
            "zone_prd_2016_to_present.csv": [("202607", 310, 31)],
        })
        self.assert_production(records, {
            ("2015-12", "Conventional crude oil"): 31,
            ("2026-07", "Conventional crude oil"): 310,
            ("2026-07", "Condensate production"): 31,
        })
        self.assertEqual(assets["conventional"]["company"], "Test operator")
        self.assertEqual(assets["conventional"]["latitude"], 56.1)

    def test_renamed_four_partitions_preserve_latest_month_and_historical_records(self):
        _, records = self.import_archive({
            "zone_prd_1954_to_2006.csv": [("200601", 999, 0)],
            "zone_prd_2007_to_2015.csv": [("201512", 31, 0)],
            "zone_prd_2016_to_2024.csv": [("202407", 62, 0)],
            "zone_prd_2025_to_present.csv": [("202607", 124, 0), ("202607", 186, 31)],
        })
        self.assert_production(records, {
            ("2015-12", "Conventional crude oil"): 31,
            ("2024-07", "Conventional crude oil"): 62,
            ("2026-07", "Conventional crude oil"): 310,
            ("2026-07", "Condensate production"): 31,
        })
        self.assertEqual(max(etl.month_end(row["date"]) for row in records), dt.date(2026, 7, 31))

    def test_combined_csv_does_not_duplicate_partition_observations(self):
        historical = [("201512", 31, 0)]
        current = [("202607", 310, 31)]
        _, records = self.import_archive({
            "zone_prd_2007_to_2015.csv": historical,
            "zone_prd_2025_to_present.csv": current,
            "zone_prd.csv": historical + current,
        })
        self.assert_production(records, {
            ("2015-12", "Conventional crude oil"): 31,
            ("2026-07", "Conventional crude oil"): 310,
            ("2026-07", "Condensate production"): 31,
        })

    def test_partition_basenames_accept_nested_paths_and_ignore_unrelated_csvs(self):
        members = {"reports/ZONE_PRD_2025_TO_PRESENT.CSV": [("202607", 31, 0)]}
        for name in ("well_index.csv", "other_zone_prd_2025_to_present.csv",
                     "zone_prd_2025_to_present_backup.csv", "zone_prd_notes.csv",
                     "zone_prd_2025_to_current.csv"):
            members[name] = [("202607", 999, 999)]
        _, records = self.import_archive(members)
        self.assert_production(records, {("2026-07", "Conventional crude oil"): 31})

    def test_combined_csv_is_supported_when_partitions_are_absent(self):
        _, records = self.import_archive({
            "reports/zone_prd.csv": [("202607", 310, 31)],
            "well_index.csv": [("202607", 999, 999)],
        })
        self.assert_production(records, {
            ("2026-07", "Conventional crude oil"): 310,
            ("2026-07", "Condensate production"): 31,
        })


if __name__ == "__main__":
    unittest.main()
