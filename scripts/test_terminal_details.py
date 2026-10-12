"""Exact facility joins and explicitly sourced, independently scoped terminal facts."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

import terminal_inventory as inventory
from validate_infrastructure_layers import validate_terminal_inventory


def detail(facility_id="source:1"):
    return {"facility_id": facility_id, "identity_match_note": "Exact reviewed source ID and street address",
            "facility_role": "both", "facility_role_note": "Operator explicitly describes storage and transfer services",
            "stored_products": ["Crude oil"], "handled_products": ["Crude oil", "Condensate"],
            "storage_capacities": [], "detail_sources": [{"label": "Operator facility page", "url": "https://operator.example/site"}]}


def capacity(value=100, unit="bbl", scope="Named facility tank storage"):
    return {"value": value, "unit": unit, "scope": scope, "basis": "published_total",
            "source_url": "https://operator.example/site", "reviewed_at": "2026-10-11",
            "note": "Published nameplate total, not currently available capacity"}


def source_file(records, name="details.json", **updates):
    payload = {"schema_version": 1, "reviewed_at": "2026-10-11", "facilities": records, **updates}
    path = Mock(spec=Path)
    path.name = name
    path.read_text.return_value = json.dumps(payload)
    return path


def terminal(facility_id="source:1", **updates):
    props = {"facility_id": facility_id, "category": "crude-storage", "name": "Shared facility name",
             "operator": "Original publisher identity", "review_status": "historical_unverified",
             "reviewed_at": "2026-10-10", "source_as_of": "2020-01", "coordinate_source_id": "Source FID 1",
             "source_url": "https://inventory.example/1", "coordinate_source_url": "https://coordinates.example/1",
             "location_confidence": "unknown", "location_note": "Historical point, not a surveyed boundary", **updates}
    return inventory.feature(props, [-112, 53])


class TerminalDetailTests(unittest.TestCase):
    def test_unknown_role_and_unpublished_capacity_do_not_follow_commodity_or_inventory_category(self):
        feature = terminal(facility_type="Storage and distribution", commodity="Crude oil", review_status="operator_verified")
        result = inventory.apply_terminal_details([feature], ())
        p = result[0]["properties"]
        self.assertEqual(p["facility_role"], "unknown")
        self.assertTrue(p["facility_role_note"])
        self.assertEqual((p["stored_products"], p["handled_products"], p["storage_capacities"]), ([], [], []))
        self.assertNotIn("available_capacity", p)
        self.assertEqual(validate_terminal_inventory({"features": result}), [])

    def test_exact_id_review_preserves_source_identity_geometry_country_and_category(self):
        original = terminal(country="CA")
        row = detail()
        row.update(services="Truck loading", modes="Truck", pipeline_connections="Named line from operator evidence")
        reviewed = inventory.apply_terminal_details([original], (source_file([row]),))
        p = reviewed[0]["properties"]
        self.assertEqual(p["facility_role"], "both")
        self.assertEqual(p["details_reviewed_at"], "2026-10-11")
        for key in ("facility_id", "operator", "coordinate_source_id", "review_status", "reviewed_at", "source_as_of", "country", "category"):
            self.assertEqual(p[key], original["properties"][key])
        self.assertIs(reviewed[0]["geometry"], original["geometry"])
        self.assertEqual(original["properties"]["facility_role"], "unknown", "Enrichment must not mutate source facts")
        self.assertEqual(p["modes"], "Truck")
        self.assertEqual(validate_terminal_inventory({"features": reviewed}), [])

    def test_same_name_does_not_match_different_facility_id(self):
        with self.assertRaisesRegex(ValueError, "Unmatched.*source:2"):
            inventory.apply_terminal_details([terminal()], (source_file([detail("source:2")]),))

    def test_duplicate_ids_within_and_across_detail_files_are_rejected(self):
        for paths in ((source_file([detail(), detail()]),), (source_file([detail()], "ca.json"), source_file([detail()], "us.json"))):
            with self.subTest(count=len(paths)), self.assertRaisesRegex(ValueError, "duplicate reviewed facility ID"):
                inventory.load_terminal_details(paths)
        with self.assertRaisesRegex(ValueError, "unique nonempty"):
            inventory.apply_terminal_details([terminal(), terminal()], ())

    def test_capacity_observations_keep_units_scopes_and_basis_without_summing_or_conversion(self):
        row = detail()
        row["storage_capacities"] = [capacity(100), capacity(80, "bbl", "Working tank capacity"), capacity(200, "m3", "Separate cavern")]
        row["storage_capacities"][1]["basis"] = "working"
        result = inventory.apply_terminal_details([terminal()], (source_file([row]),))
        self.assertEqual(result[0]["properties"]["storage_capacities"], row["storage_capacities"])
        self.assertNotIn("storage_capacity_bbl", result[0]["properties"])
        self.assertEqual(inventory.apply_terminal_details([terminal()], (source_file([row]),)), result)

    def test_each_supported_capacity_unit_is_explicit_and_retained(self):
        for unit in ("bbl", "m3", "tonnes", "gal", "L"):
            row = detail()
            row["storage_capacities"] = [capacity(123.5, unit)]
            with self.subTest(unit=unit):
                result = inventory.apply_terminal_details([terminal()], (source_file([row]),))
                self.assertEqual(result[0]["properties"]["storage_capacities"][0]["value"], 123.5)
                self.assertEqual(result[0]["properties"]["storage_capacities"][0]["unit"], unit)

    def test_missing_capacity_is_unknown_while_zero_negative_boolean_and_nonfinite_values_fail(self):
        self.assertEqual(inventory.load_terminal_details((source_file([detail()]),))["source:1"]["storage_capacities"], [])
        for value in (0, -1, True, "100", None, float("nan"), float("inf"), 10 ** 400):
            row = detail()
            row["storage_capacities"] = [capacity(value)]
            with self.subTest(value=repr(value)[:30]), self.assertRaisesRegex(ValueError, "positive, finite"):
                inventory.load_terminal_details((source_file([row]),))

    def test_capacity_requires_scope_basis_units_dates_notes_and_safe_source(self):
        for key, value in (("unit", "barrels/day"), ("unit", []), ("scope", ""), ("basis", "available"), ("basis", []),
                           ("note", ""), ("source_url", "javascript:bad()"), ("source_url", "https://user:password@example.org/"),
                           ("source_url", "https://example.org\\evil"), ("source_url", "https://exa mple.org/"),
                           ("reviewed_at", "2026-02-30"), ("reviewed_at", "20261011"), ("source_as_of", "2023-13")):
            row = detail()
            row["storage_capacities"] = [{**capacity(), key: value}]
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                inventory.load_terminal_details((source_file([row]),))

    def test_published_dates_allow_year_month_day_or_unknown_without_fabrication(self):
        for source_date in (None, "2023", "2023-03", "2023-03-06"):
            row = detail()
            row["storage_capacities"] = [{**capacity(), "source_as_of": source_date}]
            row["detail_sources"][0]["as_of"] = source_date
            with self.subTest(date=source_date):
                self.assertEqual(inventory.load_terminal_details((source_file([row]),))["source:1"]["storage_capacities"][0]["source_as_of"], source_date)

    def test_role_and_identity_claims_require_their_own_detail_source(self):
        for edit in ({"facility_role": "tank farm"}, {"facility_role": []}, {"facility_role_note": ""},
                     {"identity_match_note": ""}, {"detail_sources": []}, {"stored_products": "Crude oil"},
                     {"handled_products": [""]}, {"detail_sources": [{"label": "Unsafe", "url": "data:text/html,bad"}]},
                     {"modes": ""}, {"operator": "Replacement identity"}):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                inventory.load_terminal_details((source_file([{**detail(), **edit}]),))
        for update in ({"schema_version": True}, {"schema_version": 2}, {"reviewed_at": "2026-10"}):
            with self.subTest(update=update), self.assertRaisesRegex(ValueError, "invalid terminal details"):
                inventory.load_terminal_details((source_file([detail()], **update),))

    def test_legacy_explicit_capacity_is_preserved_but_an_empty_review_array_is_authoritative(self):
        original = terminal(storage_capacity_bbl=264000, storage_capacity_note="Operator published site storage in barrels; basis unspecified")
        result = inventory.apply_terminal_details([original], ())
        c = result[0]["properties"]["storage_capacities"][0]
        self.assertEqual((c["value"], c["unit"], c["basis"]), (264000, "bbl", "unspecified"))
        self.assertEqual(c["reviewed_at"], "2026-10-10")
        self.assertIn("Reported site", c["scope"])
        reviewed = inventory.apply_terminal_details([original], (source_file([detail()]),))[0]["properties"]
        self.assertEqual(reviewed["storage_capacities"], [])
        self.assertNotIn("storage_capacity_bbl", reviewed)
        self.assertNotIn("storage_capacity_note", reviewed)

    def test_rail_geometry_and_distinct_source_ids_are_unchanged_by_detail_join(self):
        rail = {"type": "Feature", "properties": {"feature_kind": "rail_line", "source_feature_ids": [12, 34]},
                "geometry": {"type": "MultiLineString", "coordinates": [[[-112, 53], [-111, 54]]]}}
        untouched = copy.deepcopy(rail)
        features = [rail, terminal("source:1"), terminal("source:2")]
        result = inventory.apply_terminal_details(features, (source_file([detail()]),))
        self.assertIs(result[0], rail)
        self.assertEqual(result[0], untouched)
        self.assertEqual([f["properties"]["facility_id"] for f in result[1:]], ["source:1", "source:2"])
        self.assertEqual(result[2]["properties"]["facility_role"], "unknown")

    def test_committed_reviews_match_existing_source_ids_and_preserve_the_published_inventory(self):
        data = json.loads((inventory.ROOT / "public" / "data" / "railways.geojson").read_text(encoding="utf-8"))
        records = inventory.load_terminal_details()
        self.assertTrue(records, "The reviewed detail files must contain source-backed facility records")
        result = inventory.apply_terminal_details(data["features"])
        before = [f for f in data["features"] if f["properties"].get("feature_kind") == "terminal"]
        after = [f for f in result if f["properties"].get("feature_kind") == "terminal"]
        self.assertEqual([f["properties"]["facility_id"] for f in before], [f["properties"]["facility_id"] for f in after])
        self.assertEqual(len(before), 1790, "Enrichment must not create or merge inventory observations")
        for original, enriched in zip(data["features"], result):
            self.assertIs(original["geometry"], enriched["geometry"])
            if original["properties"].get("feature_kind") == "rail_line":
                self.assertIs(original, enriched)
            else:
                for key in ("facility_id", "coordinate_source_id", "reported_name", "reported_operator", "country", "category"):
                    self.assertEqual(original["properties"].get(key), enriched["properties"].get(key))
        self.assertEqual(validate_terminal_inventory({"features": result}), [])

    def test_publication_validator_rejects_missing_roles_and_unsafe_normalized_details(self):
        output = inventory.apply_terminal_details([terminal()], (source_file([detail()]),))
        for field in ("facility_role", "facility_role_note", "stored_products", "storage_capacities", "detail_sources"):
            changed = copy.deepcopy(output)
            changed[0]["properties"].pop(field)
            with self.subTest(field=field):
                self.assertTrue(validate_terminal_inventory({"features": changed}))
        changed = copy.deepcopy(output)
        changed[0]["properties"]["storage_capacities"] = [capacity(0)]
        self.assertTrue(validate_terminal_inventory({"features": changed}))


if __name__ == "__main__":
    unittest.main()
