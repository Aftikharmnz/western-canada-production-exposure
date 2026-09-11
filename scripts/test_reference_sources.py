"""Offline checks for reference-source drift, dated capacity and safe publication."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import check_reference_sources as refs


class ReferenceFingerprintTests(unittest.TestCase):
    def test_pdf_change_stays_pending_and_never_advances_fact_verification(self):
        old, new = b"%PDF-1.7\nreviewed", b"%PDF-1.7\nchanged"
        source = dict(id="tariff:test", name="Test", kind="pdf", url="https://example.invalid/rate.pdf",
                      reviewed_sha256=hashlib.sha256(old).hexdigest(), facts_last_verified="2026-09-10")
        before = copy.deepcopy(source)
        unchanged = refs.check_source(source, fetcher=lambda _: old)
        changed = refs.check_source(source, unchanged, fetcher=lambda _: new)
        repeated = refs.check_source(source, changed, fetcher=lambda _: new)
        self.assertFalse(unchanged["review_required"])
        self.assertTrue(changed["review_required"])
        self.assertTrue(repeated["review_required"])
        self.assertEqual(repeated["facts_last_verified"], "2026-09-10")
        self.assertFalse(repeated["facts_automatically_updated"])
        self.assertEqual(source, before)

    def test_html_error_cannot_become_a_new_pdf_baseline(self):
        source = dict(id="tariff:test", name="Test", kind="pdf", url="https://example.invalid/rate.pdf")
        good = refs.check_source(source, fetcher=lambda _: b"%PDF-1.7\nfirst")
        failed = refs.check_source(source, good, fetcher=lambda _: b"<html>Access denied</html>")
        self.assertTrue(good["review_required"], "Unreviewed PDF is not verified by downloading it")
        self.assertEqual(failed["status"], "unavailable")
        self.assertEqual(failed["observation_baseline"], good["fingerprint"])

    def test_index_detects_new_url_and_ignores_script_nonces(self):
        source = dict(id="index", name="Carrier", kind="pdf_index", url="https://example.invalid/tariffs", link_pattern="/tariffs/")
        def page(name, nonce):
            return f'<html><body>{"Current official tariff publications. " * 4}<a href="/tariffs/{name}.pdf">Rate</a><script>nonce={nonce}</script></body></html>'.encode()
        first = refs.check_source(source, fetcher=lambda _: page("old", 1))
        same = refs.check_source(source, first, fetcher=lambda _: page("old", 2))
        changed = refs.check_source(source, same, fetcher=lambda _: page("replacement", 2))
        again = refs.check_source(source, changed, fetcher=lambda _: page("replacement", 3))
        self.assertFalse(same["review_required"])
        self.assertTrue(changed["review_required"])
        self.assertTrue(again["review_required"])
        self.assertEqual(changed["document_links"], ["https://example.invalid/tariffs/replacement.pdf"])

    def test_missing_index_links_are_unavailable_not_unchanged(self):
        source = dict(id="index", name="Carrier", kind="pdf_index", url="https://example.invalid/tariffs")
        result = refs.check_source(source, fetcher=lambda _: ("<html>Service temporarily unavailable. " * 10).encode())
        self.assertEqual(result["status"], "unavailable")


class EiaCapacityTests(unittest.TestCase):
    @staticmethod
    def rows():
        rows = [refs.EIA_HEADERS]
        for company, site, product, calendar, stream in [("REFINER", "ACTIVE", "OPERATING CAPACITY", 100, 110), ("REFINER", "IDLE", "IDLE CAPACITY", 20, 25)]:
            for day, value in (("calendar", calendar), ("stream", stream)):
                for label in (product, "TOTAL OPERABLE CAPACITY"):
                    rows.append(("PARENT", "820", "26", company, "District", "State", site, "1", label,
                                 f"Atmospheric Crude Distillation Capacity (barrels per {day} day)", value))
            rows.append(("PARENT", "820", "26", company, "District", "State", site, "1", "TOTAL OPER CAP (PROJECTED, NEXT YEAR)",
                         "Atmospheric Crude Distillation Capacity (barrels per stream day)", 9999))
        return rows

    def test_preserves_day_bases_idle_status_and_excludes_projected_capacity(self):
        data = refs.parse_eia_rows(self.rows(), 2026)
        self.assertEqual(data["as_of"], "2026-01-01")
        self.assertEqual(data["facility_count"], 2)
        active, idle = data["facilities"]
        self.assertEqual(active["capacity_bbl_calendar_d"], {"operating": 100, "operable": 100, "idle": 0})
        self.assertEqual(idle["capacity_bbl_stream_d"]["operable"], 25)
        self.assertEqual(idle["status_as_of_survey"], "idle")

    def test_rejects_duplicate_mismatched_missing_and_nonfinite_capacity(self):
        original = self.rows()
        duplicate = original + [original[1]]
        bad_total = copy.deepcopy(original)
        bad_total[2] = (*bad_total[2][:-1], 999)
        missing = copy.deepcopy(original)
        missing[1] = (*missing[1][:-1], None)
        nonfinite = copy.deepcopy(original)
        nonfinite[1] = (*nonfinite[1][:-1], float("nan"))
        for rows in (duplicate, bad_total, missing, nonfinite):
            with self.subTest(rows=rows[:2]), self.assertRaises(ValueError):
                refs.parse_eia_rows(rows, 2026)
        with self.assertRaisesRegex(ValueError, "year mismatch"):
            refs.parse_eia_rows(original, 2027)

    def test_latest_workbook_must_match_identified_survey_and_official_host(self):
        page = b'<html>Refinery Capacity Report With Data for January 1, 2026. Official annual capacity source.<a href="refcap26.xlsx">Workbook</a><a href="refcap25.xlsx">Older</a></html>'
        year, url = refs.discover_eia_workbook(page, "https://www.eia.gov/petroleum/refinerycapacity/index.php")
        self.assertEqual((year, url), (2026, "https://www.eia.gov/petroleum/refinerycapacity/refcap26.xlsx"))
        with self.assertRaisesRegex(ValueError, "host"):
            refs.discover_eia_workbook(page.replace(b'refcap26.xlsx', b'https://example.invalid/refcap26.xlsx'), "https://www.eia.gov/petroleum/refinerycapacity/index.php")

    def test_archived_workbook_receipt_matches_exact_bytes_and_rejects_corruption(self):
        payload = b"PK-test-exact-source-bytes"
        with tempfile.TemporaryDirectory(dir=refs.ROOT) as directory:
            root = Path(directory)
            with patch.object(refs, "ROOT", root):
                receipt = refs.archive_eia(payload, "https://www.eia.gov/refcap26.xlsx", root / "data/raw/reference")
                archived = root / receipt["raw_path"]
                self.assertEqual(archived.read_bytes(), payload)
                metadata = json.loads((root / receipt["raw_receipt"]).read_text())
                self.assertEqual(metadata["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(metadata["bytes"], len(payload))
                self.assertEqual(metadata["url"], "https://www.eia.gov/refcap26.xlsx")
                archived.write_bytes(b"corrupted cache")
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    refs.archive_eia(payload, metadata["url"], root / "data/raw/reference")

    def test_staging_keeps_prior_observation_for_unchanged_and_failed_refreshes(self):
        snapshot = dict(source_sha256="abc", source_url="https://www.eia.gov/refcap26.xlsx",
                        as_of="2026-01-01", retrieved_at="2026-06-01T00:00:00+00:00", facility_count=124)
        for fails in (False, True):
            with self.subTest(fails=fails), tempfile.TemporaryDirectory(dir=refs.ROOT) as directory:
                root = Path(directory)
                baseline = root / "public/data"
                candidate = root / "candidate"
                refs.atomic_json(baseline / "eia_refinery_capacity.json", snapshot)
                refs.atomic_json(baseline / "market_access_tariffs.json", {"metadata": {"last_verified": "2026-09-10"}})
                refs.atomic_json(root / "data/refinery_capacity_overrides.json", {"checked_at": "2026-09-10"})
                refs.atomic_json(root / "data/reference_source_monitors.json", {"eia_index_url": "https://www.eia.gov/index.php", "limitations": []})
                # A reused candidate must not silently preserve stale or unrelated content.
                refs.atomic_json(candidate / "eia_refinery_capacity.json", {"stale": True})
                argv = ["check_reference_sources.py", "--baseline", str(baseline / "reference_source_status.json"),
                        "--output", str(candidate / "reference_source_status.json"),
                        "--eia-output", str(candidate / "eia_refinery_capacity.json")]
                fetched = dict(snapshot, retrieved_at="2026-09-10T00:00:00+00:00")
                with patch.object(refs, "ROOT", root), patch.object(refs, "configured_sources", return_value=[]), \
                     patch.object(refs, "fetch_eia", return_value=fetched, side_effect=ValueError("upstream schema changed") if fails else None), \
                     patch("sys.argv", argv), redirect_stdout(io.StringIO()):
                    self.assertEqual(refs.main(), 0)
                self.assertEqual(refs.load_json(candidate / "eia_refinery_capacity.json"), snapshot)
                report = refs.load_json(candidate / "reference_source_status.json")
                check = report["checks"][0]
                self.assertEqual(report["failure_count"], int(fails))
                self.assertFalse(check.get("facts_automatically_updated", False))
                if fails:
                    self.assertTrue(check["preserved_previous_snapshot"])
                else:
                    self.assertEqual(check["status"], "unchanged")
                    self.assertEqual(check["source_url"], snapshot["source_url"])


if __name__ == "__main__":
    unittest.main()
