"""Offline identity and partition checks for named EIA product pipeline groups."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import build_market_access_pipelines as pipelines
import validate_infrastructure_layers as validation


LAYER = {"editingInfo": {"dataLastEditDate": 1751382805254, "schemaLastEditDate": 1781028432315}}


def source(fid, operator, name, coordinates=None):
    return {"type": "Feature", "properties": {"FID": fid, "Opername": operator, "Pipename": name},
            "geometry": {"type": "LineString", "coordinates": coordinates or [[-80, 40], [-81, 41]]}}


class ProductPipelineNetworksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = pipelines.load_route_facts(pipelines.DEFAULT_ROUTE_FACTS)

    def build(self, features, facts=None, layer=None):
        return pipelines.build_product_network_features(features, LAYER if layer is None else layer,
                                                        self.facts if facts is None else facts)

    def test_buckeye_and_colonial_are_distinct_at_identical_coordinates(self):
        features, metadata = self.build([source(1, "BUCKEYE PARTNERS", "Buckeye"),
                                         source(2, "COLONIALPIPELINE CO", "Colonial")])
        by_id = {row["properties"]["route_id"]: row["properties"] for row in features}
        buckeye, colonial = by_id["us-products-buckeye"], by_id["us-products-colonial"]
        self.assertNotEqual(buckeye["color"], colonial["color"])
        self.assertEqual(buckeye["source_feature_ids"], [1])
        self.assertEqual(colonial["source_feature_ids"], [2])
        self.assertEqual(buckeye["source_operator_names"], ["BUCKEYE PARTNERS"])
        self.assertEqual(metadata["source_feature_count"], 2)
        self.assertTrue(all(row["properties"]["default_visible"] is False for row in features))

    def test_distinct_published_network_names_and_operators_stay_separate(self):
        rows = [source(1, "BUCKEYE PARTNERS", "Buckeye"), source(2, "BUCKEYE PARTNERS", "Laurel Pipeline"),
                source(3, "KINDER MORGAN", "Plantation"), source(4, "KINDER MORGAN", "SFPP_NORTH"),
                source(5, "KINDER MORGAN", "SFPP_SOUTH"), source(6, "Other operator", "Buckeye")]
        features, metadata = self.build(rows)
        self.assertEqual(len(features), 6)
        self.assertEqual(len({row["properties"]["route_id"] for row in features}), 6)
        self.assertEqual(metadata["grouping_fields"], ["Opername", "Pipename"])
        self.assertEqual(sorted(fid for feature in features for fid in feature["properties"]["source_feature_ids"]), list(range(1, 7)))
        shuffled, _ = self.build(list(reversed(rows)))
        self.assertEqual([row["properties"]["route_id"] for row in features],
                         [row["properties"]["route_id"] for row in shuffled])

    def test_source_data_edit_is_distinct_from_later_schema_edit(self):
        features, metadata = self.build([source(1, "Unknown owner", "Named line")])
        self.assertIn("Underlying inventory date unavailable", features[0]["properties"]["source_as_of"])
        self.assertIn("hosted-copy service data edit 2025-07-01", features[0]["properties"]["source_as_of"])
        self.assertTrue(metadata["hosted_copy_data_edit_at"].startswith("2025-07-01"))
        self.assertTrue(metadata["hosted_copy_schema_edit_at"].startswith("2026-06-09"))
        self.assertIsNone(metadata["underlying_inventory_date"])
        missing_date, missing_metadata = self.build([source(1, None, None)], layer={})
        self.assertIn("unavailable", missing_date[0]["properties"]["source_as_of"].lower())
        self.assertIsNone(missing_metadata["hosted_copy_data_edit_at"])

    def test_unknown_source_names_do_not_infer_an_operator_capacity_or_endpoints(self):
        features, _ = self.build([source(1, None, None)], facts={})
        properties = features[0]["properties"]
        self.assertIn("Unknown pipeline name", properties["route_name"])
        self.assertIn("Unknown source operator", properties["operator"])
        self.assertEqual(properties["source_operator_names"], [])
        self.assertEqual(properties["review_status"], "publisher_snapshot_only")
        details = properties["pipeline_details"]
        self.assertIsNone(details["capacity_kbbl_d"])
        self.assertIn("Not supplied", details["origin"])
        self.assertIn("Not supplied", details["destination"])
        self.assertNotIn("verified_at", details)

    def test_reviewed_alias_does_not_replace_historical_publisher_name(self):
        features, _ = self.build([source(1, "MIDSTREAM PARTNERS", "Magellan"),
                                 source(2, "NUSTAR ENERGY", "Valley Pipeline")])
        by_name = {row["properties"]["source_pipeline_names"][0]: row["properties"] for row in features}
        self.assertEqual(by_name["Magellan"]["operator"], "ONEOK (Magellan)")
        self.assertEqual(by_name["Magellan"]["source_operator_names"], ["MIDSTREAM PARTNERS"])
        self.assertIn("Sunoco", by_name["Valley Pipeline"]["operator"])
        self.assertEqual(by_name["Valley Pipeline"]["source_operator_names"], ["NUSTAR ENERGY"])
        self.assertEqual(by_name["Magellan"]["pipeline_details"]["verified_at"], "2026-10-10")

    def test_slug_collisions_have_distinct_stable_ids(self):
        self.assertNotEqual(pipelines.product_network_id("Owner", "A-B"), pipelines.product_network_id("Owner", "A B"))

    def test_operator_geometry_uses_exact_names_and_retains_archived_ids_only_as_reconciliation(self):
        archived, _ = self.build([source(1, "BUCKEYE PARTNERS", "Buckeye"),
                                  source(2, "BUCKEYE PARTNERS", "Laurel Pipeline"),
                                  source(3, "WEST SHORE PIPELINE CO", "West Shore Pipeine")])
        operator = []
        for oid, name in enumerate(["BUCKEYE PIPE LINE", "LAUREL PIPE LINE", "WEST SHORE PIPE LINE", "WOOD RIVER PIPE LINE"], 10):
            operator.append({"type": "Feature", "properties": {"objectid": oid, "name": name, "products": "Refined products"},
                             "geometry": {"type": "LineString", "coordinates": [[-90, 35], [-91, 36]]}})
        metadata = pipelines.apply_buckeye_operator_geometry(archived, operator, {"editingInfo": {"lastEditDate": 1678121617684}})
        self.assertEqual(metadata["replaced_archived_group_count"], 3)
        self.assertEqual(metadata["additional_network_count"], 1)
        buckeye = next(row for row in archived if row["properties"]["route_id"] == "us-products-buckeye")
        self.assertEqual(buckeye["geometry"]["coordinates"], [[-90, 35], [-91, 36]])
        self.assertEqual(buckeye["properties"]["source_feature_ids"], [1])
        self.assertEqual(buckeye["properties"]["geometry_source_feature_ids"], [10])
        self.assertEqual(buckeye["properties"]["geometry_source_url"], pipelines.BUCKEYE_PRODUCTS_URL)
        self.assertIn("inventory date not supplied", buckeye["properties"]["source_as_of"])
        extra = next(row for row in archived if row["properties"]["route_id"].startswith("operator-products-"))
        self.assertEqual(extra["properties"]["source_feature_ids"], [])
        self.assertEqual(extra["properties"]["geometry_source_feature_ids"], [13])

    def test_duplicate_source_ids_and_unusable_geometry_reject_partition(self):
        rows = [source(1, "Owner", "One"), source(1, "Owner", "Other")]
        with self.assertRaisesRegex(ValueError, "unique"):
            self.build(rows)
        bad = source(1, "Owner", "One")
        bad["geometry"] = None
        with self.assertRaisesRegex(ValueError, "geometry"):
            self.build([bad])

    def test_incomplete_source_count_causes_refresh_warning(self):
        with patch.object(pipelines, "ROUTES", []), patch.object(pipelines, "MARKET_HUBS", []), \
                patch.object(pipelines, "load_route_facts", return_value={}), \
                patch.object(pipelines, "request_json", side_effect=[LAYER, {"count": 2}]), \
                patch.object(pipelines, "query_arcgis_geojson", return_value=[source(1, "Owner", "One")]):
            output = pipelines.build_feature_collection(include_remote=True)
        self.assertEqual(output["features"], [])
        self.assertIn("count mismatch", output["metadata"]["warnings"][0])

    def test_inventory_prefers_canonical_publisher_when_accessible(self):
        with patch.object(pipelines, "request_json", side_effect=[copy.deepcopy(LAYER), {"count": 1}]), \
                patch.object(pipelines, "query_arcgis_geojson", return_value=[source(1, "Owner", "One")]) as query:
            features, metadata = pipelines.fetch_product_inventory()
        query.assert_called_once_with(pipelines.EIA_CANONICAL_PRODUCTS_URL, "1=1")
        self.assertFalse(metadata["_is_hosted_copy"])
        self.assertIsNone(metadata["_canonical_access_error"])
        self.assertEqual(len(features), 1)

    def test_unavailable_canonical_service_falls_back_with_explicit_copy_owner(self):
        with patch.object(pipelines, "request_json", side_effect=[ValueError("499 Token Required"),
                    copy.deepcopy(LAYER), {"owner": "Federal_User_Community"}, {"count": 1}]), \
                patch.object(pipelines, "query_arcgis_geojson", return_value=[source(1, "Owner", "One")]) as query:
            _, metadata = pipelines.fetch_product_inventory()
        query.assert_called_once_with(pipelines.EIA_PRODUCTS_URL, "1=1")
        self.assertTrue(metadata["_is_hosted_copy"])
        self.assertEqual(metadata["_publisher"], "Federal_User_Community")
        self.assertIn("Token Required", metadata["_canonical_access_error"])

    def test_validator_rejects_duplicate_missing_and_catch_all_members(self):
        features, metadata = self.build([source(1, "BUCKEYE PARTNERS", "Buckeye"),
                                         source(2, "COLONIALPIPELINE CO", "Colonial")])
        collection = {"features": features, "metadata": {"product_networks": metadata}}
        self.assertEqual(validation.validate_product_networks(collection), [])
        duplicate = copy.deepcopy(collection)
        duplicate["features"][1]["properties"]["source_feature_ids"] = [1]
        self.assertTrue(any("more than once" in message for message in validation.validate_product_networks(duplicate)))
        missing = copy.deepcopy(collection)
        missing["features"].pop()
        self.assertTrue(any("expected 2" in message for message in validation.validate_product_networks(missing)))
        catch_all = copy.deepcopy(collection)
        catch_all["features"][0]["properties"]["route_id"] = "us-products-reference"
        self.assertTrue(any("must not be selectable" in message for message in validation.validate_product_networks(catch_all)))

    def test_shipped_products_partition_preserves_every_live_source_record_once(self):
        collection = json.loads((pipelines.DEFAULT_OUTPUT).read_text(encoding="utf-8"))
        self.assertEqual(validation.validate_product_networks(collection), [])
        metadata = collection["metadata"]["product_networks"]
        self.assertEqual(metadata["source_feature_count"], 329)
        self.assertEqual(metadata["network_count"], 118)
        self.assertNotIn("us-products-reference", [row["properties"].get("route_id") for row in collection["features"]])


if __name__ == "__main__":
    unittest.main()
