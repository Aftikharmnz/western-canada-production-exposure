"""Offline regression checks for bounded official-source download retries."""

import errno
import io
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
import zipfile

import run_etl as etl


TEST_TEMP_ROOT = etl.ROOT / "data" / "processed"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


def archive_payload():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("production.csv", "year,month,oil\n2026,9,100\n")
    return output.getvalue()


def response(payload=None, error=None):
    result = MagicMock()
    result.__enter__.return_value = result
    result.headers = {"ETag": '"current"', "Last-Modified": "Sat, 10 Oct 2026 00:00:00 GMT"}
    if error is not None:
        result.read.side_effect = error
    else:
        result.read.return_value = payload
    return result


class DownloadRetriesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.target = self.root / "source.zip"
        self.url = "https://example.invalid/source.zip"
        self.payload = archive_payload()
        root_patch = patch.object(etl, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        log_patch = patch.object(etl, "log")
        log_patch.start()
        self.addCleanup(log_patch.stop)

    def test_read_timeout_then_success_replaces_cache_only_after_validation(self):
        self.target.write_bytes(b"previous cache")

        def read_timeout():
            self.assertEqual(self.target.read_bytes(), b"previous cache")
            raise TimeoutError("The read operation timed out")

        first = response()
        first.read.side_effect = read_timeout
        with patch.object(etl.urllib.request, "urlopen", side_effect=[first, response(self.payload)]) as request, \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "downloaded")
        self.assertEqual(result["attempts"], 2)
        self.assertIsNone(result["error"])
        self.assertEqual(result["etag"], '"current"')
        self.assertEqual(self.target.read_bytes(), self.payload)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.kwargs["timeout"], 180)
        sleep.assert_called_once_with(2)

    def test_permanent_url_error_retains_previous_cache_without_retry(self):
        self.target.write_bytes(b"previous cache")
        failure = urllib.error.URLError(PermissionError(errno.EACCES, "Permission denied"))
        with patch.object(etl.urllib.request, "urlopen", side_effect=failure) as request, \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 1)
        self.assertTrue(result["cached_fallback"])
        self.assertIn("Permission denied", result["error"])
        self.assertEqual(self.target.read_bytes(), b"previous cache")
        request.assert_called_once()
        sleep.assert_not_called()

    def test_exhausted_timeouts_report_failure_after_three_attempts(self):
        with patch.object(etl.urllib.request, "urlopen", side_effect=TimeoutError("timed out")) as request, \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(result["error"], "timed out")
        self.assertFalse(result["cached_fallback"])
        self.assertFalse(self.target.exists())
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    def test_http_404_is_not_retried(self):
        failure = urllib.error.HTTPError(self.url, 404, "Not Found", {}, io.BytesIO())
        with patch.object(etl.urllib.request, "urlopen", side_effect=failure) as request, \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["http_status"], 404)
        self.assertEqual(result["attempts"], 1)
        request.assert_called_once()
        sleep.assert_not_called()

    def test_html_response_does_not_retry_or_replace_cache(self):
        self.target.write_bytes(b"previous cache")
        with patch.object(etl.urllib.request, "urlopen", return_value=response(b"<html>Unavailable</html>")) as request, \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "failed")
        self.assertIn("HTML", result["error"])
        self.assertEqual(result["attempts"], 1)
        self.assertTrue(result["cached_fallback"])
        self.assertEqual(self.target.read_bytes(), b"previous cache")
        request.assert_called_once()
        sleep.assert_not_called()

    def test_transient_http_responses_are_retried(self):
        for status in (408, 429, 500, 503, 599):
            with self.subTest(status=status):
                failure = urllib.error.HTTPError(self.url, status, "Temporary failure", {}, io.BytesIO())
                with patch.object(etl.urllib.request, "urlopen", side_effect=[failure, response(self.payload)]) as request, \
                        patch.object(etl.time, "sleep") as sleep:
                    result = etl.download_url(self.url, self.target, force=True)
                self.assertEqual(result["status"], "downloaded")
                self.assertEqual(request.call_count, 2)
                sleep.assert_called_once_with(2)

    def test_url_errors_with_network_reasons_are_retried(self):
        reasons = [TimeoutError("timed out"), ConnectionResetError("connection reset"),
                   socket.gaierror(socket.EAI_AGAIN, "temporary DNS failure"),
                   OSError(errno.ENETUNREACH, "network unavailable")]
        for reason in reasons:
            with self.subTest(reason=reason):
                failure = urllib.error.URLError(reason)
                with patch.object(etl.urllib.request, "urlopen", side_effect=[failure, response(self.payload)]) as request, \
                        patch.object(etl.time, "sleep") as sleep:
                    result = etl.download_url(self.url, self.target, force=True)
                self.assertEqual(result["status"], "downloaded")
                self.assertEqual(request.call_count, 2)
                sleep.assert_called_once_with(2)

    def test_local_write_failure_is_not_retried_and_preserves_cache(self):
        self.target.write_bytes(b"previous cache")
        with patch.object(etl.urllib.request, "urlopen", return_value=response(self.payload)) as request, \
                patch.object(Path, "write_bytes", side_effect=PermissionError("Read-only filesystem")), \
                patch.object(etl.time, "sleep") as sleep:
            result = etl.download_url(self.url, self.target, force=True)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 1)
        self.assertTrue(result["cached_fallback"])
        self.assertEqual(self.target.read_bytes(), b"previous cache")
        request.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
