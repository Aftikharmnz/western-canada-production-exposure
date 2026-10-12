"""Publication guards for facility identity, source evidence and storage units."""
import copy
import unittest

from validate_infrastructure_layers import validate_terminal_inventory


class TerminalInventoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.feature = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-112, 53]},
                        "properties": {"feature_kind": "terminal", "facility_id": "official-1", "name": "Named facility",
                                       "category": "crude-storage", "review_status": "operator_verified",
                                       "operator": "Published operator", "reviewed_at": "2026-10-10", "source_as_of": None,
                                       "facility_role": "unknown", "facility_role_note": "Facility role has not been reviewed",
                                       "stored_products": [], "handled_products": [], "storage_capacities": [], "detail_sources": [],
                                       "source_url": "https://operator.example/facility", "coordinate_source_url": "https://regulator.example/1",
                                       "location_confidence": "medium", "location_note": "Published facility centroid; not surveyed"}}

    def validate(self, *features):
        return validate_terminal_inventory({"features": list(features)})

    def test_unknown_source_date_does_not_prevent_an_evidenced_identity_review(self):
        self.assertEqual(self.validate(self.feature), [])

    def test_identical_name_or_place_is_not_a_unique_identity(self):
        second = copy.deepcopy(self.feature)
        self.assertTrue(any("duplicate" in e for e in self.validate(self.feature, second)))
        second["properties"]["facility_id"] = "official-2"
        self.assertEqual(self.validate(self.feature, second), [])

    def test_unverified_inventory_does_not_require_a_synthetic_review_date(self):
        p = self.feature["properties"]
        p.update(review_status="historical_unverified", reviewed_at=None, operator=None)
        self.assertEqual(self.validate(self.feature), [])

    def test_verified_claim_and_location_need_their_own_evidence(self):
        for field, value in (("reviewed_at", None), ("operator", None), ("coordinate_source_url", None),
                             ("source_url", "javascript:bad()"), ("location_note", ""), ("location_confidence", "surveyed")):
            feature = copy.deepcopy(self.feature)
            feature["properties"][field] = value
            with self.subTest(field=field):
                self.assertTrue(self.validate(feature))

    def test_storage_units_cannot_be_inferred_from_a_naked_value(self):
        p = self.feature["properties"]
        p["storage_capacity_bbl"] = 160000
        self.assertTrue(any("basis note" in e for e in self.validate(self.feature)))
        p["storage_capacity_note"] = "Operator publishes tank capacity in barrels; website date unspecified"
        self.assertEqual(self.validate(self.feature), [])
        for invalid in (0, True, -1, float("nan"), float("inf"), "160000"):
            p["storage_capacity_bbl"] = invalid
            with self.subTest(value=invalid):
                self.assertTrue(self.validate(self.feature))


if __name__ == "__main__":
    unittest.main()
