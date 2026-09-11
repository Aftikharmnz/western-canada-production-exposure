"""Regression checks for data-loss protection and independently verified tariffs."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_market_access_pipelines as pipelines
import build_market_access_tariffs as tariffs
import build_railway_layer as railways


class InfrastructureRefreshTests(unittest.TestCase):
    def test_route_details_are_joined_by_id_and_preserved_across_geometry_refreshes(self):
        route = pipelines.ROUTES[0]
        fact = {"origin": "Reviewed origin", "destination": "Reviewed destination", "product": "Crude oil", "capacity_kbbl_d": 100.5,
                "capacity_basis": "system capacity", "capacity_note": "Dated operator evidence", "source_name": "Operator",
                "source_url": "https://operator.example/capacity", "verified_at": "2026-09-11"}
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipelines.ROOT) as directory:
            path = Path(directory) / "facts.json"
            path.write_text(json.dumps({"schema_version": 1, "routes": {route["route_id"]: fact}}), encoding="utf-8")
            with patch.object(pipelines, "ROUTES", [route]), patch.object(pipelines, "MARKET_HUBS", []):
                for coordinates in ([[0, 0], [1, 1]], [[0, 0], [2, 2]]):
                    feature = {"type": "Feature", "properties": {"route_id": route["route_id"], "source_summary": "Official test geometry",
                               "commodity": "Stale product", "direction": "Stale direction"},
                               "geometry": {"type": "LineString", "coordinates": coordinates}}
                    with patch.object(pipelines, "route_feature", return_value=(feature, [])):
                        output = pipelines.build_feature_collection(include_remote=False, route_facts=path)
                    self.assertEqual(output["features"][0]["properties"]["pipeline_details"], fact)
                    self.assertEqual(output["features"][0]["properties"]["commodity"], fact["product"])
                    self.assertEqual(output["features"][0]["properties"]["direction"], "Reviewed origin → Reviewed destination")
                    self.assertEqual(output["features"][0]["geometry"]["coordinates"], coordinates)

    def test_route_facts_reject_missing_routes_invalid_capacity_and_untrusted_url_schemes(self):
        fact = {"origin": "Origin", "destination": "Destination", "product": "Crude oil", "capacity_kbbl_d": None,
                "capacity_basis": "unavailable", "capacity_note": "No defensible single system capacity", "source_name": "Operator",
                "source_url": "https://operator.example/source", "verified_at": "2026-09-11", "as_of": "Operator disclosure for 2025"}
        payload = {"schema_version": 1, "routes": {route["route_id"]: copy.deepcopy(fact) for route in pipelines.ROUTES}}
        route_id = pipelines.ROUTES[0]["route_id"]
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipelines.ROOT) as directory:
            path = Path(directory) / "facts.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIsNone(pipelines.load_route_facts(path)[route_id]["capacity_kbbl_d"])
            for field, invalid in [("capacity_kbbl_d", -1), ("capacity_kbbl_d", 0), ("capacity_kbbl_d", True),
                                   ("capacity_kbbl_d", float("nan")), ("source_url", "javascript:alert(1)"),
                                   ("route_source_url", "file:///private/source"), ("verified_at", "2026-13-01"),
                                   ("origin", ""), ("product", ""), ("unknown", "unexpected")]:
                edited = copy.deepcopy(payload)
                edited["routes"][route_id][field] = invalid
                path.write_text(json.dumps(edited), encoding="utf-8")
                with self.subTest(field=field, value=invalid), self.assertRaises(ValueError):
                    pipelines.load_route_facts(path)
            edited = copy.deepcopy(payload)
            del edited["routes"][route_id]
            path.write_text(json.dumps(edited), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing"):
                pipelines.load_route_facts(path)
            path.write_text('{"schema_version":1,"schema_version":1,"routes":{}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                pipelines.load_route_facts(path)
            path.unlink()
            with patch.object(pipelines, "query_arcgis_geojson") as request, self.assertRaises(FileNotFoundError):
                pipelines.build_feature_collection(include_remote=True, route_facts=path)
            request.assert_not_called()

    def test_market_access_uses_candidate_aer_geometry_and_keeps_public_provenance(self):
        with tempfile.TemporaryDirectory(prefix="elt-test-", dir=pipelines.ROOT) as directory:
            candidate = Path(directory) / "aer_feeder_pipelines.geojson"
            coordinates = [[-113.1, 52.1], [-113.2, 52.2]]
            candidate.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature",
                "properties": {"licence": "64941", "status": "Operating"},
                "geometry": {"type": "LineString", "coordinates": coordinates}}]}), encoding="utf-8")
            route = next(route for route in pipelines.ROUTES if route["route_id"] == "rangeland-aurora-glacier")
            feature, warnings = pipelines.route_feature(route, include_remote=False, aer_feeder_input=candidate)
            self.assertEqual(warnings, [])
            self.assertEqual(feature["geometry"]["coordinates"], coordinates)
            self.assertIn("public/data/aer_feeder_pipelines.geojson", feature["properties"]["source_urls"])
            self.assertNotIn(str(candidate), feature["properties"]["source_urls"])
            # The candidate argument does not mutate the default route inputs.
            self.assertEqual(route["parts"][0]["local_geojson"], pipelines.AER_FEEDER_PIPELINES)

    def test_rail_batches_reject_missing_source_ids(self):
        ids = {"objectIds": [1, 2], "objectIdFieldName": "OBJECTID"}
        partial = {"type": "FeatureCollection", "features": [{"properties": {"OBJECTID": 1}}]}
        with patch.object(railways, "request_json", side_effect=[ids, {"count": 2}, partial]):
            with self.assertRaisesRegex(ValueError, "truncated or changed"):
                railways.query_rail_geojson(railways.DEFAULT_BBOX, railways.DEFAULT_RAIL_WHERE)

    def test_rail_batches_preserve_all_selected_source_ids(self):
        ids = {"objectIds": [2, 1], "objectIdFieldName": "OBJECTID"}
        complete = {"type": "FeatureCollection", "features": [{"properties": {"OBJECTID": i}} for i in (1, 2)]}
        with patch.object(railways, "request_json", side_effect=[ids, {"count": 2}, complete]):
            self.assertEqual(len(railways.query_rail_geojson(railways.DEFAULT_BBOX, railways.DEFAULT_RAIL_WHERE)), 2)

    def test_arcgis_json_error_does_not_become_an_empty_network(self):
        for builder in (pipelines, railways):
            with self.subTest(builder=builder.__name__):
                with patch.object(builder, "request_json", return_value={"error": {"code": 400, "message": "Invalid query"}}):
                    with self.assertRaises(ValueError):
                        builder.query_arcgis_geojson("https://example.test/0", **({"where": "1=1"}))

    def test_pipeline_pagination_handles_missing_transfer_flag(self):
        page = {"type": "FeatureCollection", "features": [{"id": 1}, {"id": 2}]}
        last = {"type": "FeatureCollection", "features": [{"id": 3}]}
        with patch.object(pipelines, "request_json", side_effect=[page, last]) as query:
            self.assertEqual(len(pipelines.query_arcgis_geojson("https://example.test/0", "1=1", page_size=2)), 3)
            self.assertEqual(query.call_count, 2)

    def test_partial_refresh_preserves_previous_file(self):
        partial = {"metadata": {"warnings": ["upstream error"]}, "features": []}
        with patch("sys.argv", ["builder"]), patch.object(pipelines, "build_feature_collection", return_value=partial), patch.object(Path, "write_text") as write, patch.object(Path, "replace") as replace:
            self.assertEqual(pipelines.main(), 1)
            write.assert_not_called()
            replace.assert_not_called()

    def test_test_only_build_cannot_replace_production(self):
        with patch("sys.argv", ["builder", "--local-only"]):
            with self.assertRaises(SystemExit):
                pipelines.main()


class CurrentTariffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tariffs.build_tariffs()
        cls.rows = cls.data["tariffs"]

    def find(self, **criteria):
        rows = [r for r in self.rows if all(r.get(k) == v for k, v in criteria.items())]
        self.assertEqual(len(rows), 1, criteria)
        return rows[0]

    def test_keystone_september_rate_and_separate_currency(self):
        row = self.find(document_id="keystone84", destination_hub_id="cushing", product="Heavy crude")
        self.assertEqual(row["total_per_bbl"], 6.750)
        self.assertEqual(row["effective"], "2026-09-01")
        self.assertEqual(row["additional_costs"][0]["currency"], "CAD")
        self.assertEqual(row["additional_costs"][0]["value"], 0.042)
        self.assertIsNone(row["total_with_default_adders"])
        self.assertTrue(row["source_url"].endswith("#page=4"))

    def test_mainline_retains_both_billing_currencies(self):
        row = self.find(document_id="enbridge5", origin_hub_id="edmonton", destination_hub_id="superior", product="Heavy crude")
        self.assertEqual((row["cad_component_m3"], row["usd_component_m3"]), (11.2418, 10.5945))
        self.assertIsNone(row["total"])
        self.assertEqual(row["currency"], "mixed")

    def test_express_two_year_2025_table_is_not_a_2013_table(self):
        row = self.find(document_id="express207", destination_hub_id="wood_river", service="Committed international joint rate - 2025 Open Season, 2 years", product="Petroleum")
        self.assertEqual(row["total"], 45.8715)
        self.assertEqual(row["total_with_default_adders"], 45.9215)
        self.assertFalse(any("5 to 9" in r["service"] or "5-9" in r["service"] for r in self.rows))
        local = self.find(document_id="express_cer_204", destination_hub_id="hardisty", product="Light crude")
        self.assertIsNone(local["total_with_default_adders"])

    def test_spearhead_committed_total_includes_adders_once(self):
        row = self.find(document_id="enbridge9", origin_hub_id="edmonton", product="Heavy crude", service="TSA Committed for 2 Year Term")
        self.assertEqual(row["total"], 7.4820)
        self.assertEqual(row["base_before_included_costs"], 7.4)
        self.assertAlmostEqual(sum(c["value"] for c in row["included_costs"]), 0.082)
        self.assertIsNone(row["total_with_default_adders"])

    def test_trans_mountain_component_labels_and_sums(self):
        row = self.find(document_id="trans_mountain_123", destination_hub_id="kamloops", service="Uncommitted", product="Light crude / refined petroleum")
        components = {c["name"]: c["value"] for c in row["included_costs"]}
        self.assertEqual(components["First Nations consultation and accommodation"], 0.6181)
        self.assertEqual(components["GHG offset costs"], 0.0375)
        self.assertEqual(components["Revenue sharing"], -0.6590)
        self.assertAlmostEqual(sum(components.values()), row["variable"], delta=0.00011)
        puget = self.find(document_id="trans_mountain_puget_416", destination_hub_id="anacortes")
        self.assertEqual(puget["total"], 0.5729)

    def test_snapshot_cardinality_and_current_effective_filings(self):
        self.assertEqual(len(self.rows), 893)
        self.assertTrue(all(r["effective"] <= self.data["metadata"]["last_verified"] for r in self.rows))
        self.assertEqual(self.data["metadata"]["next_known_change"], "2026-10-01")
        self.assertTrue(all(r["status"] == "current" for r in self.rows))


if __name__ == "__main__":
    unittest.main()
