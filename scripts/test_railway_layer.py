"""Rail source request boundaries and exact inventory completeness checks."""
import io
import sys
import unittest
import urllib.parse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import build_railway_layer as railway


class RailwayRequestTests(unittest.TestCase):
    def test_relative_candidate_output_does_not_fail_after_successful_write(self):
        layer = {"metadata": {"raw_rail_segment_count": 1}, "features": []}
        with patch.object(sys, "argv", ["railway", "--output", "data/processed/railway-fixture.geojson"]), \
             patch.object(railway, "build_layer", return_value=layer), patch.object(Path, "mkdir"), \
             patch.object(Path, "write_text"), patch.object(Path, "replace"), \
             patch.object(Path, "stat", return_value=SimpleNamespace(st_size=100)), patch("builtins.print") as output:
            railway.main()
        self.assertIn("railway-fixture.geojson", output.call_args.args[0])

    def test_long_id_inventory_is_form_encoded_in_post_body(self):
        parameters = {"objectIds": ",".join(str(value) for value in range(800)), "f": "geojson"}
        response = io.BytesIO(b'{"type":"FeatureCollection","features":[]}')
        endpoint = railway.NARN_LINES_URL + "/query"
        with patch.object(railway.urllib.request, "urlopen", return_value=response) as opener:
            railway.request_json(endpoint, post_data=parameters)
        request = opener.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, endpoint)
        self.assertEqual(request.get_header("Content-type"), "application/x-www-form-urlencoded")
        self.assertEqual(urllib.parse.parse_qs(request.data.decode())["objectIds"], [parameters["objectIds"]])

    def test_bounded_post_batches_return_every_selected_id(self):
        batches = []

        def source(url, **kwargs):
            if not kwargs:
                return {"count": 5} if "returnCountOnly" in url else {"objectIdFieldName": "OBJECTID", "objectIds": [5, 1, 4, 2, 3]}
            self.assertEqual(url, railway.NARN_LINES_URL + "/query")
            ids = [int(value) for value in kwargs["post_data"]["objectIds"].split(",")]
            batches.append(ids)
            return {"type": "FeatureCollection", "features": [{"properties": {"OBJECTID": value}} for value in reversed(ids)]}

        with patch.object(railway, "request_json", side_effect=source):
            features = railway.query_rail_geojson(railway.DEFAULT_BBOX, railway.DEFAULT_RAIL_WHERE, batch_size=2)
        self.assertEqual(sorted(len(batch) for batch in batches), [1, 2, 2])
        self.assertEqual({feature["properties"]["OBJECTID"] for feature in features}, {1, 2, 3, 4, 5})

    def test_missing_duplicate_unexpected_and_truncated_ids_are_rejected(self):
        inventory = {"objectIdFieldName": "OBJECTID", "objectIds": [1, 2]}
        for values, truncated in [([1], False), ([1, 1], False), ([1, 3], False), ([1, 2], True)]:
            payload = {"type": "FeatureCollection", "features": [{"properties": {"OBJECTID": value}} for value in values],
                       "exceededTransferLimit": truncated}
            with self.subTest(values=values, truncated=truncated), \
                 patch.object(railway, "request_json", side_effect=[inventory, {"count": 2}, payload]):
                with self.assertRaisesRegex(ValueError, "truncated or changed"):
                    railway.query_rail_geojson(railway.DEFAULT_BBOX, railway.DEFAULT_RAIL_WHERE)

    def test_unbounded_batch_size_fails_before_network_access(self):
        for size in (0, 801):
            with self.subTest(size=size), patch.object(railway, "request_json") as request:
                with self.assertRaisesRegex(ValueError, "between 1 and 800"):
                    railway.query_rail_geojson(railway.DEFAULT_BBOX, railway.DEFAULT_RAIL_WHERE, batch_size=size)
                request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
