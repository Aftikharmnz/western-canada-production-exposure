"""AESO refresh failure/recovery regressions. No live requests or email delivery."""

from datetime import datetime, timezone
import http.client
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import build_aeso_power_status as power


NOW = datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc)


def report(stamp="Oct 12, 2026 12:00"):
    return f'''Current Supply Demand Report
"Last Update : {stamp}"
Alberta Total Net Generation,260
Net Actual Interchange,20
Alberta Internal Load (AIL),240
Net-To-Grid Generation,100
Dispatched Contingency Reserve (DCR),0
COGENERATION,100,80,0
OTHER,200,180,0
TOTAL,300,260,0

<center><b>Cogeneration</b></center>
ASSET,MC,TNG,DCR
Plant (A1),100,80,0

<center><b>Other</b></center>
ASSET,MC,TNG,DCR
Other (A2),200,180,0
'''


class AesoRefreshTests(unittest.TestCase):
    def setUp(self):
        clock_patch = patch.object(power, "datetime", wraps=datetime)
        self.clock = clock_patch.start()
        self.clock.now.return_value = NOW
        self.addCleanup(clock_patch.stop)
        sleep_patch = patch.object(power.time, "sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

    def test_fetch_timeout_then_success(self):
        with patch.object(power, "fetch_csd", side_effect=[TimeoutError("read timed out"), report()]) as fetch:
            data = power.build()
        self.assertEqual(fetch.call_count, 2)
        self.sleep.assert_called_once_with(2)
        self.assertEqual(data["observed_at"], "2026-10-12T18:00:00Z")
        self.assertEqual(data["aeso_asset_count"], 2)

    def test_temporary_http_errors_retry_but_permissions_errors_do_not(self):
        for status in [408, 429, 500, 502, 503, 504, 403, 404]:
            with self.subTest(status=status):
                failure = urllib.error.HTTPError(power.CSD_URL, status, "source unavailable", {}, None)
                with patch.object(power, "fetch_csd", side_effect=[failure, report()]) as fetch:
                    if status in [403, 404]:
                        with self.assertRaises(urllib.error.HTTPError):
                            power.build()
                        self.assertEqual(fetch.call_count, 1)
                    else:
                        self.assertEqual(power.build()["aeso_asset_count"], 2)
                        self.assertEqual(fetch.call_count, 2)

    def test_connection_failure_and_incomplete_read_retry(self):
        for failure in [urllib.error.URLError("temporary DNS failure"), ConnectionResetError("reset"),
                        http.client.IncompleteRead(b"partial CSV", 50)]:
            with self.subTest(error=type(failure).__name__):
                with patch.object(power, "fetch_csd", side_effect=[failure, report()]) as fetch:
                    self.assertEqual(power.build()["aeso_asset_count"], 2)
                self.assertEqual(fetch.call_count, 2)

    def test_invalid_report_retries_and_recovers(self):
        for text in ["<html>Service unavailable</html>", report().replace("Other (A2),200,180,0", ""),
                     report("Oct 12, 2026 09:00")]:
            with self.subTest(report=text[:30]):
                with patch.object(power, "fetch_csd", side_effect=[text, report()]) as fetch:
                    self.assertEqual(power.build()["aeso_asset_count"], 2)
                self.assertEqual(fetch.call_count, 2)

    def test_exhausted_downloads_are_bounded(self):
        with patch.object(power, "fetch_csd", side_effect=TimeoutError("timeout")) as fetch:
            with self.assertRaises(TimeoutError):
                power.build()
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list], [2, 4])

    def test_partial_csv_cannot_replace_last_valid_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            previous = b'{"observed_at":"2026-10-12T17:30:00Z","last_valid":true}'
            output.write_bytes(previous)
            partial = report().replace("Other (A2),200,180,0", "")
            with patch.object(power, "fetch_csd", return_value=partial):
                self.assertEqual(power.main(["--output", str(output)]), 1)
            self.assertEqual(output.read_bytes(), previous)
            self.assertFalse(output.with_suffix(".tmp").exists())

    def test_missing_system_metrics_duplicate_units_and_bad_totals_are_rejected(self):
        invalid = [report().replace("Net Actual Interchange,20\n", ""),
                   report() + "Plant again (A1),0,0,0\n",
                   report().replace("TOTAL,300,260,0", "TOTAL,900,260,0"),
                   report().replace("TOTAL,300,260,0", ""),
                   report().replace("TOTAL,300,260,0", "TOTAL,300,,0"),
                   report().replace("Other (A2),200", "Other (A2),NaN")]
        for text in invalid:
            with self.subTest(report=text[-60:]):
                with self.assertRaises(ValueError):
                    power.build_snapshot(text)

    def test_missing_generation_remains_unknown_and_measured_zero_remains_zero(self):
        sites = [{"codes": ["A1"], "site": "One", "operator": "Test", "lat": 55, "lon": -110},
                 {"codes": ["A2"], "site": "Two", "operator": "Test", "lat": 55, "lon": -110}]
        text = report().replace("Plant (A1),100,80,0", "Plant (A1),100,,0").replace("Other (A2),200,180,0", "Other (A2),200,0,0")
        with patch.object(power, "SITE_COGEN_SITES", sites):
            data = power.build_snapshot(text)
        rows = {row["site"]: row for row in data["site_cogen"]}
        self.assertIsNone(rows["One"]["tng_mw"])
        self.assertFalse(rows["One"]["complete"])
        self.assertEqual(rows["Two"]["tng_mw"], 0)
        self.assertTrue(rows["Two"]["complete"])

    def test_fuel_label_is_not_inherited_across_an_unlabelled_block(self):
        parsed = power.parse_csd(report().replace("<center><b>Other</b></center>\n", ""))
        self.assertEqual(parsed["assets"][0]["fuel"], "Cogeneration")
        self.assertEqual(parsed["assets"][1]["fuel"], "Unknown")

    def test_response_size_and_encoding_are_checked(self):
        for payload in [b"x" * (power.MAX_REPORT_BYTES + 1), b"\xffinvalid"]:
            with patch.object(power.urllib.request, "urlopen", return_value=io.BytesIO(payload)):
                with self.assertRaises(ValueError):
                    power.fetch_csd()
        with patch.object(power.urllib.request, "urlopen", return_value=io.BytesIO(b"\xef\xbb\xbf" + report().encode())) as fetch:
            self.assertTrue(power.fetch_csd().startswith("Current Supply Demand Report"))
        self.assertEqual(fetch.call_args.kwargs["timeout"], 60)

    def test_autumn_clock_change_uses_the_current_occurrence_of_the_repeated_hour(self):
        # Alberta's last autumn clock change was in 2025.
        stamp = "Nov 02, 2025 01:45"
        self.assertEqual(power.observation_time(stamp, datetime(2025, 11, 2, 7, 50, tzinfo=timezone.utc)),
                         datetime(2025, 11, 2, 7, 45, tzinfo=timezone.utc))
        self.assertEqual(power.observation_time(stamp, datetime(2025, 11, 2, 8, 50, tzinfo=timezone.utc)),
                         datetime(2025, 11, 2, 8, 45, tzinfo=timezone.utc))

    def test_alberta_remains_on_utc_minus_six_after_november_2026(self):
        for stamp, now in [("Nov 01, 2026 02:45", datetime(2026, 11, 1, 8, 45, tzinfo=timezone.utc)),
                           ("Jan 12, 2027 12:00", datetime(2027, 1, 12, 18, 0, tzinfo=timezone.utc))]:
            with self.subTest(stamp=stamp):
                self.assertEqual(power.observation_time(stamp, now), now)

    def test_nonexistent_future_and_stale_timestamps_are_rejected(self):
        for stamp, now in [("Mar 08, 2026 02:30", datetime(2026, 3, 8, 9, 30, tzinfo=timezone.utc)),
                           ("Oct 12, 2026 12:30", NOW), ("Oct 12, 2026 09:00", NOW)]:
            with self.subTest(stamp=stamp):
                with self.assertRaises(ValueError):
                    power.observation_time(stamp, now)

    def test_older_source_observation_does_not_overwrite_newer_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            previous = b'{"observed_at":"2026-10-12T18:01:00Z"}'
            output.write_bytes(previous)
            with self.assertRaises(RuntimeError):
                power.write_snapshot(power.build_snapshot(report()), output)
            self.assertEqual(output.read_bytes(), previous)

    def test_write_failure_retains_previous_snapshot_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            previous = b'{"observed_at":"2026-10-12T17:30:00Z"}'
            output.write_bytes(previous)
            with patch.object(Path, "replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    power.write_snapshot(power.build_snapshot(report()), output)
            self.assertEqual(output.read_bytes(), previous)
            self.assertFalse(output.with_suffix(".tmp").exists())

    def test_valid_snapshot_is_written_and_summary_records_source_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            summary = Path(directory) / "summary.md"
            with patch.object(power, "fetch_csd", return_value=report()), \
                    patch.dict(power.os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}):
                self.assertEqual(power.main(["--output", str(output)]), 0)
            self.assertEqual(json.loads(output.read_text())["observed_at"], "2026-10-12T18:00:00Z")
            self.assertIn("2026-10-12T18:00:00Z", summary.read_text())
            self.assertIn("Validated 2 generation units", summary.read_text())


if __name__ == "__main__":
    unittest.main()
