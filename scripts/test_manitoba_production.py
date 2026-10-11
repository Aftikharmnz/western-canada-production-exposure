"""Manitoba production workbook header and monthly unit regressions."""
import calendar
import datetime as dt
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import openpyxl
import run_etl as etl


class ManitobaProductionTests(unittest.TestCase):
    CURRENT_HEADERS = [
        "LICENCE", "WELL_NAME", "UWI", "FIELD CODD", "FIELD NAME", "POOL CODE", "POOL NAME",
        "NAME", "DEVIATION", "UNIT", "FLUID CODE", "YEAR", "JAN", "FEB", "MAR", "APR",
        "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "MINERAL_RIGHTS", "CUMULATIVE_TO_DATE",
    ]

    @staticmethod
    def production_row(fluid="OIL", year=2026, **months):
        values = [0] * 12
        for month, value in months.items():
            values[["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(month)] = value
        return [123, "Test well", "100.03-29-016-27W1.00", 1, "Test field", "59A", "Test pool",
                "Test operator", "V", 0, fluid, year, *values, "FREEHOLD", sum(values)]

    def import_workbook(self, rows, fluid_header="FLUID CODE", underscored=False):
        headers = list(self.CURRENT_HEADERS)
        headers[10] = fluid_header
        if underscored:
            headers = [header.replace(" ", "_") for header in headers]
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        workbook_bytes = io.BytesIO()
        workbook.save(workbook_bytes)
        workbook.close()
        assets, records = {}, []

        def add_asset(**kwargs):
            asset_id = kwargs["asset_id_override"]
            assets[asset_id] = kwargs
            return asset_id

        def add_record(date, asset_id, stream, volume, sheet, column, source, **kwargs):
            records.append(dict(date=date, asset_id=asset_id, stream=stream, volume=volume,
                                source=source, scenario=kwargs["scenario"]))

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wmp_2023_2026_excel.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("wmp_2023_2026_excel.xlsx", workbook_bytes.getvalue())
            with patch.object(etl, "MANITOBA_PRODUCTION_ZIP", path), \
                 patch.object(etl, "resolve_dls_locations", return_value={}), patch.object(etl, "log"):
                etl.append_manitoba_well_production(add_asset, add_record, "2024-01")
        return assets, records

    def assert_production(self, records, expected):
        self.assertEqual(len(records), len(expected))
        actual = {row["date"]: row for row in records}
        self.assertEqual(set(actual), set(expected))
        for date, volume_m3 in expected.items():
            days = calendar.monthrange(date.year, date.month)[1]
            self.assertAlmostEqual(actual[date]["volume"], volume_m3 * etl.M3_TO_BBL / days)
            self.assertEqual(actual[date]["stream"], "Conventional crude oil")
            self.assertEqual(actual[date]["source"], "manitoba_well_production")
            self.assertEqual(actual[date]["scenario"], "actual")

    def test_current_fluid_code_header_imports_oil_and_excludes_water(self):
        assets, records = self.import_workbook([
            self.production_row(jan=31, feb=28, jul=310),
            self.production_row(fluid="H2O", jan=999, feb=999, jul=999),
        ])
        self.assert_production(records, {
            dt.date(2026, 1, 1): 31,
            dt.date(2026, 2, 1): 28,
            dt.date(2026, 7, 1): 310,
        })
        self.assertEqual(max(etl.month_end(row["date"]) for row in records), dt.date(2026, 7, 31))
        self.assertEqual(len(assets), 1)
        asset = next(iter(assets.values()))
        self.assertEqual(asset["company"], "Test operator")
        self.assertEqual(asset["province"], "Manitoba")
        self.assertIn("Field: Test field.", asset["notes"])
        self.assertIn("Pool: Test pool.", asset["notes"])

    def test_legacy_fluid_type_header_preserves_leap_month_conversion(self):
        _, records = self.import_workbook([
            self.production_row(year=2024, feb=29),
        ], fluid_header="FLUID_TYPE", underscored=True)
        self.assert_production(records, {dt.date(2024, 2, 1): 29})

    def test_spaced_fluid_type_header_remains_supported(self):
        _, records = self.import_workbook([
            self.production_row(jul=310),
        ], fluid_header="FLUID TYPE")
        self.assert_production(records, {dt.date(2026, 7, 1): 310})

    def test_fluid_code_requires_explicit_oil_value(self):
        assets, records = self.import_workbook([
            self.production_row(fluid="H2O", jul=999),
            self.production_row(fluid=1, jul=999),
            self.production_row(fluid=None, jul=999),
        ])
        self.assertEqual(records, [])
        self.assertEqual(assets, {})


if __name__ == "__main__":
    unittest.main()
