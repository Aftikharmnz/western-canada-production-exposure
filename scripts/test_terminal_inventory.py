"""Checks for terminal identity, country scope, and honest location evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_railway_layer as railway
import terminal_inventory as inventory
from validate_infrastructure_layers import validate_terminal_inventory


class TerminalInventoryTests(unittest.TestCase):
    def test_buckeye_operator_points_exclude_foreign_sites_and_do_not_infer_capacity_units(self):
        features, excluded = inventory.buckeye_features()
        self.assertEqual((len(features), excluded), (128, 2))
        properties = [f["properties"] for f in features]
        self.assertEqual({p["country"] for p in properties}, {"US"})
        self.assertTrue(any(p["state"] == "PR" for p in properties))
        self.assertFalse(any(p["reported_name"] in {"BBH Terminal", "St. Lucia Terminal"} for p in properties))
        self.assertFalse(any("storage_capacity_bbl" in p for p in properties))
        self.assertTrue(all(p["coordinate_as_of"] == "2023-03-06" for p in properties))
        self.assertTrue(all(p["status"].startswith("Unknown") for p in properties))
        texas = next(f for f in features if f["properties"]["facility_id"] == "buckeye-map:1:321")
        self.assertEqual(texas["geometry"]["coordinates"], [-97.49952, 27.82939])
        self.assertEqual(texas["properties"]["category"], "crude-storage")
        self.assertIn("records.tceq.texas.gov", texas["properties"]["source_url"])

    def test_colonial_addresses_remain_low_confidence_not_assumed_tank_centroids(self):
        features = inventory.colonial_features()
        self.assertEqual({f["properties"]["city"] for f in features}, {"Austell", "Charlotte", "Chattanooga"})
        for f in features:
            p = f["properties"]
            self.assertEqual(p["location_confidence"], "low")
            self.assertIn("street-address interpolation", p["location_note"])
            self.assertIn("not an operator-published tank location", p["location_note"])
            self.assertIn("geocoding.geo.census.gov", p["coordinate_source_url"])
            self.assertGreater(p["storage_capacity_bbl"], 0)
            self.assertIn("page undated", p["storage_capacity_note"])

    def test_changed_census_coordinates_cannot_silently_replace_reviewed_location(self):
        real = json.loads(inventory.REVIEWS.read_text(encoding="utf-8"))
        altered = copy.deepcopy(real)
        altered["colonial"][0]["coordinates"] = [-84.6, 33.8]
        fake = unittest.mock.Mock()
        fake.read_text.return_value = json.dumps(altered)
        with patch.object(inventory, "REVIEWS", fake):
            with self.assertRaisesRegex(ValueError, "does not match reviewed Census"):
                inventory.colonial_features()

    def test_canadian_existing_identity_replacements_correct_points_without_duplicates(self):
        features = railway.canadian_terminal_features()
        self.assertEqual(len(features), 88)
        by_id = {f["properties"]["facility_id"]: f for f in features}
        self.assertEqual(len(by_id), 88)
        self.assertEqual(by_id["npri:3905"]["geometry"]["coordinates"], [-122.88435, 49.27958])
        self.assertEqual(by_id["npri:32940"]["geometry"]["coordinates"], [-111.18358, 52.6396])
        self.assertEqual(by_id["npri:11890"]["properties"]["category"], "ngl-storage")
        self.assertIn("Sarnia", by_id["npri:11890"]["properties"]["search_aliases"])
        self.assertNotIn("npri:6907", by_id)
        self.assertFalse(any(f["properties"]["name"] == "Keyera Edmonton Terminal / Alberta Diluent & Crude Terminals (ADT/ACT)" for f in features))
        self.assertTrue(any(f["properties"]["name"] == "Keyera Edmonton NGL Terminal" for f in features))
        self.assertTrue(any("Decommission" in f["properties"].get("status", "") for f in features))
        self.assertTrue(all(f["properties"].get("status") != "Operational" for f in features))

    def test_archive_operator_identity_and_source_dates_are_not_rewritten_as_current(self):
        raw = next(f for f in inventory.snapshot("eia_products_archive")["data"]["features"]
                   if "BUCKEYE" in f["properties"]["Company"])
        feature = railway.normalize_product_terminal(raw)
        p = feature["properties"]
        self.assertEqual(p["reported_operator"], raw["properties"]["Company"])
        self.assertEqual(p["source_as_of"], "2020-01")
        self.assertEqual(p["review_status"], "inventory_only")
        self.assertIn("Unknown", p["status"])
        self.assertIn("FGr1D95XCGALKXqM", p["canonical_source_url"])
        self.assertIn("wx8u046p68e0iGuj", p["coordinate_source_url"])
        crude = railway.normalize_crude_terminal(inventory.snapshot("eia_crude_rail_archive")["data"]["features"][0])
        self.assertIsNone(crude["properties"].get("source_as_of"))
        self.assertIn("University of Minnesota copy", crude["properties"]["source"])

    def test_grandstaff_office_point_does_not_inherit_commercial_subset_capacity(self):
        f = inventory.us_storage_features()[0]
        p = f["properties"]
        self.assertEqual(f["geometry"]["coordinates"], [-96.75041, 36.00081])
        self.assertEqual(p["category"], "crude-storage")
        self.assertIn("office", p["location_accuracy"])
        self.assertIn("DRAFT", p["location_note"])
        self.assertIn("current operator not reverified", p["operator"])
        self.assertNotIn("storage_capacity_bbl", p)
        self.assertIn("commercial storage capacity is not applied", p["location_note"])

    def test_truncated_and_duplicate_snapshot_ids_fail_before_output_creation(self):
        original = inventory.snapshot("buckeye_propane_terminals")
        for edit in (lambda p: p["data"]["features"].pop(),
                     lambda p: p["data"].update(exceededTransferLimit=True),
                     lambda p: p["data"]["features"].__setitem__(1, copy.deepcopy(p["data"]["features"][0]))):
            payload = copy.deepcopy(original)
            edit(payload)
            with tempfile.TemporaryDirectory() as directory:
                Path(directory, "buckeye_propane_terminals.json").write_text(json.dumps(payload), encoding="utf-8")
                with patch.object(inventory, "SOURCES", Path(directory)), self.assertRaises(ValueError):
                    inventory.snapshot("buckeye_propane_terminals")

    def test_terminal_rebuild_preserves_rail_geometry_and_old_distinct_inventory_observations(self):
        line = {"type": "Feature", "properties": {"feature_kind": "rail_line", "category": "rail", "name": "Existing line"},
                "geometry": {"type": "MultiLineString", "coordinates": [[[-97, 35], [-97.1, 35.2]]]}}
        original = {"features": [line], "metadata": {"rail_where": railway.DEFAULT_RAIL_WHERE, "bbox": list(railway.DEFAULT_BBOX),
                    "raw_rail_segment_count": 1, "raw_rail_source_row_count": 2, "generated_at": "2026-01-01T00:00:00Z"}}
        with patch.object(railway, "query_rail_geojson") as network, patch("builtins.print"):
            output = railway.build_layer(railway.DEFAULT_BBOX, railway.DEFAULT_RAIL_WHERE, "1=1", "1=1", original)
        network.assert_not_called()
        self.assertEqual(output["features"][0], line)
        self.assertEqual(output["metadata"]["rail_geometry_generated_at"], "2026-01-01T00:00:00Z")
        terminals = [f for f in output["features"] if f["properties"]["feature_kind"] == "terminal"]
        self.assertEqual(len(terminals), 1790)
        self.assertEqual(sum(f["properties"]["facility_id"].startswith("eia-products-archive:") for f in terminals), 1476)
        self.assertEqual(sum(f["properties"]["facility_id"].startswith("buckeye-map:") for f in terminals), 128)
        self.assertEqual(validate_terminal_inventory(output), [])

    def test_null_island_nonfinite_and_boolean_reviewed_points_are_rejected(self):
        for coordinates in ([0, 0], (0, 0), [True, 36], [-96, float("nan")], [-181, 35]):
            with self.subTest(coordinates=coordinates):
                self.assertFalse(inventory.valid_point(coordinates))


if __name__ == "__main__":
    unittest.main()
