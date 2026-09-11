"""Offline checks for official publication discovery and AER report contracts."""
import csv
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import openpyxl

from official_source_discovery import discover_aer_files, discover_report, parse_petrinex_months

TEST_TEMP_ROOT = Path(__file__).resolve().parents[1] / "data" / "processed"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class OfficialSourceDiscoveryTests(unittest.TestCase):
    def test_aer_follows_published_links_and_filters_history(self):
        html = '''<a href="/documents/sts/ST53/ST53_Current.xls">Current</a>
        <a href="/documents/sts/ST53/ST53_2017-12.xls">2017</a>
        <a href="/prd/documents/sts/ST53/ST53_2027.xls">2027</a>
        <a href="https://example.com/ST53_2028.xls">Untrusted mirror</a>'''
        rows = discover_report("aer_st53", html, "2020-01")
        self.assertEqual([r["raw_file"] for r in rows], ["aer_st53_2027.xls", "aer_st53_current.xls"])
        self.assertTrue(all(r["url"].startswith("https://www.aer.ca/") for r in rows))

    def test_missing_or_changed_current_contract_fails(self):
        for html in ("maintenance", '<a href="/ST39-2025.xls">2025</a>',
                     '<a href="https://www.aer.ca.evil.invalid/ST39.xls">Current</a>'):
            with self.subTest(html=html), self.assertRaises(ValueError):
                discover_report("aer_st39", html)

    def test_latest_published_quarter_is_dynamic(self):
        rows = discover_report("aer_st44", '''<a href="/prd/documents/sts/ST44_2027-Q1.xlsx">1</a>
        <a href="https://static.aer.ca/prd/documents/sts/ST44_2026-Q4.xlsx">4</a>''')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["publication_period"], "2027-Q1")
        self.assertEqual(rows[0]["raw_file"], "aer_st44_current.xlsx")

    def test_manitoba_rollover_and_archive_overlap(self):
        html = '''<a href="wmp_2023_2026_excel.zip">Excel</a>
        <a href="wmp_2027_2030_excel.zip">Excel</a>
        <a href="wmp_2027_2030_pdf.zip">PDF</a>
        <a href="wmp_2017_2020_excel.zip">Excel</a>'''
        rows = discover_report("manitoba_well_production", html)
        self.assertEqual(rows[0]["end_year"], 2030)
        self.assertEqual(len(rows), 1)
        rows = discover_report("manitoba_well_production", html, "2024-01")
        self.assertEqual([r["end_year"] for r in rows], [2026, 2030])

    def test_cached_publications_order_current_last(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            for name in ("aer_st39_current.xls", "aer_st39_2025.xls", "aer_st39_2017.xls", "aer_st39_workbook.xls"):
                (root / name).touch()
            self.assertEqual([p.name for p in discover_aer_files(root, "aer_st39")],
                             ["aer_st39_2017.xls", "aer_st39_2025.xls", "aer_st39_current.xls"])

    def test_petrinex_uses_enabled_publications_and_revision_tokens(self):
        def row(period, disabled="", timestamp="2027-03-05 01:02:03"):
            return f'''<tr data-file-type="Vol_{period}-AB"><td data-col-type="CheckBox">
            <input type="checkbox" data-control-element="Vol_{period}-AB" {disabled}>
            <input type="hidden" name="VolumetricFiles[0].FileName" value="Vol_{period}-AB">
            <input type="hidden" name="VolumetricFiles[0].FileCategory" value="Volumetric">
            </td><td data-col-type="Timestamp">{timestamp}</td></tr>'''
        rows = parse_petrinex_months("AB", row("2027-01") + row("2027-02", "disabled"))
        self.assertEqual([r["period"] for r in rows], ["2027-01"])
        self.assertEqual(rows[0]["updated_at"], "2027-03-05 01:02:03")
        for html in ("unexpected event", row("2027-01", timestamp=""), row("2027-01").replace("-AB", "-SK"), row("2027-01").replace("Volumetric", "Infrastructure")):
            with self.subTest(html=html), self.assertRaises(ValueError):
                parse_petrinex_months("AB", html)


class AerExtractionContracts(unittest.TestCase):
    """Small synthetic regulator-shaped fixtures, not copyrighted report copies."""
    rscript = shutil.which("Rscript")

    def run_extraction(self, root, kind, workbook):
        source, output = root / f"{kind}.xlsx", root / f"{kind}.csv"
        workbook.save(source)
        result = subprocess.run([self.rscript, str(Path(__file__).with_name("extract_aer_current.R")),
                                 kind, str(source), str(output)], capture_output=True, text=True, timeout=30)
        rows = []
        if result.returncode == 0:
            with output.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        return result, rows

    @unittest.skipUnless(rscript, "R/readxl integration fixture requires Rscript")
    def test_st53_issue_month_units_zero_and_invalid_values(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.title = "BITUMEN"
            sheet.cell(1, 1, "ST-53 2027 Alberta In Situ Oil Sands Summary")
            sheet.cell(2, 1, "January 2027")
            sheet.cell(3, 6, "Crude Bitumen Production Rates Per Calendar Day (m³)")
            for col, value in enumerate(["Operator", "Scheme Name", "Area", "Approval Number", "Recovery Method", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1):
                sheet.cell(4, col, value)
            for row, value in ((5, 0), (6, 12.5)):
                sheet.cell(row, 1, "Example Operator")
                sheet.cell(row, 4, str(1000 + row))
                sheet.cell(row, 6, value)
                sheet.cell(row, 7, 999)  # Numeric template/forecast beyond the published issue.
            result, rows = self.run_extraction(root, "st53", wb)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([r["period"] for r in rows], ["2027-01", "2027-01"])
            self.assertEqual([float(r["value"]) for r in rows], [0, 12.5])
            self.assertTrue(all(r["units"] == "m3/d" for r in rows))
            sheet.cell(6, 6, "not a number")
            result, _ = self.run_extraction(root, "st53", wb)
            self.assertNotEqual(result.returncode, 0)
            sheet.cell(6, 6, 12.5)
            sheet.cell(3, 6, "Crude Bitumen Production Rates Per Calendar Day (barrels)")
            result, _ = self.run_extraction(root, "st53", wb)
            self.assertNotEqual(result.returncode, 0)

    @unittest.skipUnless(rscript, "R/readxl integration fixture requires Rscript")
    def test_st39_monthly_units_zero_and_schema_drift(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as directory:
            root = Path(directory)
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.title = "VAR0800-ST39Extracts_xls"
            sheet.cell(1, 1, "VAR0800")
            sheet.cell(2, 14, "Production Month/Year: February 2027")
            sheet.cell(4, 1, "Example Operator - ABOS0012345 EXAMPLE MINE")
            sheet.cell(6, 1, "Crude Bitumen (m³)")
            for col, month in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 2):
                sheet.cell(7, col, month)
            sheet.cell(7, 14, "2027")
            sheet.cell(10, 1, "Production")
            sheet.cell(10, 2, 0)
            sheet.cell(10, 3, 31)
            sheet.cell(10, 4, 999)
            result, rows = self.run_extraction(root, "st39", wb)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([r["period"] for r in rows], ["2027-01", "2027-02"])
            self.assertTrue(all(r["units"] == "m3/month" for r in rows))
            sheet.cell(7, 3, "Mar")
            result, _ = self.run_extraction(root, "st39", wb)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
