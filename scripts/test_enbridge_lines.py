"""Reviewed line identities stay independent of grouped geometry and live flow."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import enbridge_lines as catalogue
import build_market_access_pipelines as pipelines
import validate_infrastructure_layers as infrastructure


def line_record(identity="enbridge-line-1", number="1"):
    return dict(id=identity, line_number=number, name=f"Enbridge Line {number}", aliases=[],
                products=["Crude oil"], origin="Published origin", destination="Published destination",
                direction="Published flow direction", capacity_kbbl_d=300,
                capacity_basis="annual_average", capacity_note="Published rating excludes restrictions; not available capacity.",
                status="Operating", status_note="Operator publication; current throughput unknown.",
                diameter_note="Published diameter", length_note="Published length", connections=[],
                trading_note="Commodity eligibility is not a current batch schedule.",
                route_ids=["enbridge-mainline-lakehead"], geometry_note="Grouped context does not locate this individual line.",
                sources=[dict(label="Operator configuration", url="https://www.enbridge.com/configuration.pdf", as_of="Q1 2026")],
                reviewed_at="2026-10-11", commercial_links=[])


def catalogue_fixture():
    return dict(schema_version=1, metadata=dict(reviewed_at="2026-10-11"),
                lines=[line_record(identity, identity.removeprefix("enbridge-line-").upper().replace("-", "/"))
                       for identity in sorted(catalogue.REQUIRED_FACTSHEET_IDS)])


def source_feature(number, object_id):
    return dict(type="Feature", properties=dict(PipelineID=f"EnbridgeLine{number}", OBJECTID=object_id),
                geometry=dict(type="LineString", coordinates=[[-82, 43], [-80, 43.1]]))


class CatalogueValidationTests(unittest.TestCase):
    def setUp(self):
        self.payload = catalogue_fixture()
        self.route_ids = {"enbridge-mainline-lakehead"}

    def errors(self):
        return catalogue.validate_catalogue(self.payload, self.route_ids)

    def test_source_publication_dates_do_not_become_live_capacity(self):
        self.payload["lines"][0]["sources"].append(dict(label="Undated page", url="https://www.enbridge.com/asset"))
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.payload["lines"][0]["capacity_kbbl_d"], 300)

    def test_known_published_lines_cannot_silently_drop_from_coverage(self):
        self.payload["lines"] = [line for line in self.payload["lines"] if line["id"] != "enbridge-line-292"]
        self.assertTrue(any("enbridge-line-292" in error for error in self.errors()))
        self.payload = catalogue_fixture()
        self.payload["lines"][0]["line_number"] = "999"
        self.assertTrue(any("does not match" in error for error in self.errors()))

    def test_additional_reviewed_named_system_does_not_require_fixed_row_count(self):
        self.payload["lines"].append(line_record("enbridge-named-system", None))
        self.payload["lines"].append(line_record("former-enbridge-olympic", None))
        self.assertEqual(self.errors(), [])

    def test_duplicate_id_unsupported_field_and_non_iso_review_are_rejected(self):
        for mutation in (lambda p: p["lines"].append(copy.deepcopy(p["lines"][0])),
                         lambda p: p["lines"][0].update(flow_today=1),
                         lambda p: p["lines"][0].update(reviewed_at="2026-02-30")):
            with self.subTest(mutation=mutation):
                self.payload = catalogue_fixture()
                mutation(self.payload)
                self.assertTrue(self.errors())

    def test_absent_capacity_and_explicit_null_are_distinct_from_zero(self):
        line = self.payload["lines"][0]
        for bad in (0, -1, True, float("nan"), float("inf"), "300"):
            with self.subTest(value=bad):
                line["capacity_kbbl_d"] = bad
                self.assertTrue(self.errors())
        line.update(capacity_kbbl_d=None, capacity_basis="not_published")
        self.assertEqual(self.errors(), [])
        del line["capacity_kbbl_d"]
        self.assertTrue(self.errors())

    def test_section_ratings_require_label_and_cannot_be_summed_to_scalar(self):
        line = self.payload["lines"][0]
        line.update(capacity_kbbl_d=None, capacity_basis="section_dependent")
        self.assertTrue(self.errors())
        line["capacity_label"] = "West section 140; east section 164 kbbl/d"
        self.assertEqual(self.errors(), [])
        line["capacity_kbbl_d"] = 304
        self.assertTrue(self.errors())

    def test_unsafe_source_or_commercial_urls_and_missing_evidence_rejected(self):
        for unsafe in ("javascript:alert(1)", "https://user:password@example.com/", "https://example.com/a\n", "https://example.com:invalid/"):
            with self.subTest(url=unsafe):
                self.payload = catalogue_fixture()
                self.payload["lines"][0]["commercial_links"] = [dict(label="Tariff", url=unsafe)]
                self.assertTrue(self.errors())
        self.payload = catalogue_fixture()
        self.payload["lines"][0]["sources"] = []
        self.assertTrue(self.errors())

    def test_catalogue_cannot_publish_coordinates_or_unmapped_context(self):
        for changes in (dict(geometry={"type": "LineString"}), dict(route_ids=["guessed-route"])):
            self.payload = catalogue_fixture()
            self.payload["lines"][0].update(changes)
            self.assertTrue(self.errors())
        self.payload = catalogue_fixture()
        self.payload["metadata"]["extra"] = {"coordinates": []}
        self.assertTrue(self.errors())

    def test_unknown_products_are_explicit_and_cannot_imply_operating_status(self):
        line = self.payload["lines"][0]
        line.update(products=[])
        self.assertTrue(self.errors())
        line.update(status="unknown", products_note="Product service not independently verified.")
        self.assertEqual(self.errors(), [])

    def test_exact_source_copy_and_publication_drift_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, routes = root / "source.json", root / "public.json", root / "routes.geojson"
            source.write_text(json.dumps(self.payload, indent=2), encoding="utf-8")
            routes.write_text(json.dumps(dict(type="FeatureCollection", features=[dict(properties=dict(feature_kind="pipeline", route_id="enbridge-mainline-lakehead"))])), encoding="utf-8")
            catalogue.publish_catalogue(source, output, routes=routes)
            self.assertEqual(output.read_bytes(), source.read_bytes())
            self.assertEqual(catalogue.published_catalogue_errors(output, source, routes=routes), [])
            changed = copy.deepcopy(self.payload)
            changed["lines"][0]["capacity_kbbl_d"] = 999
            output.write_text(json.dumps(changed), encoding="utf-8")
            self.assertTrue(catalogue.published_catalogue_errors(output, source, routes=routes))

    def test_duplicate_json_keys_and_nonfinite_literals_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for contents in ('{"id":1,"id":2}', '{"capacity":NaN}'):
                path.write_text(contents, encoding="utf-8")
                with self.assertRaises(ValueError):
                    catalogue.read_json(path)


class ExplicitCerSplitTests(unittest.TestCase):
    def setUp(self):
        self.children = [route for route in pipelines.ROUTES if route["route_id"] in {"enbridge-line-7", "enbridge-line-11"}]
        self.facts = {route["route_id"]: dict(origin="Reviewed origin", destination="Reviewed destination", product="Crude oil",
                                             capacity_kbbl_d=180, capacity_basis="annual_average", capacity_note="Published rating",
                                             source_url="https://www.enbridge.com/asset", source_name="Enbridge", verified_at="2026-10-11")
                      for route in self.children}
        self.existing = dict(type="FeatureCollection", metadata=dict(product_networks={"source_feature_count": 329}, warnings=[]), features=[
            dict(type="Feature", properties=dict(feature_kind="pipeline", route_id="enbridge-lines-7-11", default_visible=False),
                 geometry=dict(type="MultiLineString", coordinates=[[[-82, 43], [-80, 43.1]]])),
            dict(type="Feature", properties=dict(feature_kind="pipeline", route_id="enbridge-mainline-lakehead", source_feature_ids=[4, 179]),
                 geometry=dict(type="MultiLineString", coordinates=[[[-110, 54], [-82, 43]]])),
            dict(type="Feature", properties=dict(feature_kind="hub", name="Reference"), geometry=dict(type="Point", coordinates=[-80, 43]))])

    @staticmethod
    def query(url, where):
        if url != pipelines.CER_PIPELINES_URL:
            raise AssertionError("Unexpected network fetch")
        number = "7" if where == "PipelineID = 'EnbridgeLine7'" else "11" if where == "PipelineID = 'EnbridgeLine11'" else None
        if number is None:
            raise AssertionError(f"Unexpected identity predicate: {where}")
        return [source_feature(number, int(number))]

    def test_individual_lines_require_explicit_source_ids_not_grouped_corridor(self):
        original = copy.deepcopy(self.existing)
        with patch.object(pipelines, "query_arcgis_geojson", side_effect=self.query) as query:
            merged = pipelines.merge_verified_enbridge_lines(self.existing, self.facts)
        self.assertEqual(query.call_count, 2)
        self.assertEqual(self.existing, original, "A failed/staged merge cannot mutate the published input")
        self.assertEqual(merged["features"][1:], original["features"][1:] + merged["features"][-2:])
        self.assertEqual(merged["features"][0]["geometry"], original["features"][0]["geometry"])
        self.assertFalse(merged["features"][0]["properties"]["default_visible"])
        self.assertEqual(merged["metadata"]["product_networks"], original["metadata"]["product_networks"])
        for child in merged["features"][-2:]:
            props = child["properties"]
            number = props["route_id"].removeprefix("enbridge-line-")
            self.assertTrue(props["default_visible"])
            self.assertEqual(props["geometry_source_identities"], [dict(source_url=pipelines.CER_PIPELINES_URL,
                identity_fields={"PipelineID": f"EnbridgeLine{number}"}, source_feature_ids=[int(number)])])

    def test_no_publication_after_empty_misidentified_or_duplicate_query(self):
        for result in ([], [source_feature("9", 17)], [source_feature("7", 2), source_feature("7", 2)]):
            with self.subTest(result=result), patch.object(pipelines, "query_arcgis_geojson", return_value=result):
                before = copy.deepcopy(self.existing)
                with self.assertRaises(ValueError):
                    pipelines.merge_verified_enbridge_lines(self.existing, self.facts)
                self.assertEqual(self.existing, before)

    def test_merge_is_idempotent_and_preserves_hidden_combined_reference(self):
        with patch.object(pipelines, "query_arcgis_geojson", side_effect=self.query):
            first = pipelines.merge_verified_enbridge_lines(self.existing, self.facts)
            second = pipelines.merge_verified_enbridge_lines(first, self.facts)
        self.assertEqual(first, second)
        self.assertEqual(len(second["features"]), len(self.existing["features"]) + 2)

    def test_reviewed_product_name_and_section_overrides_do_not_change_source_ids(self):
        feature = dict(type="Feature", properties=dict(FID=1, Opername="ENBRIDGE", Pipename="Southern Lights"),
                       geometry=dict(type="LineString", coordinates=[[-90, 42], [-100, 48]]))
        identity = pipelines.product_network_id("ENBRIDGE", "Southern Lights")
        details = dict(self.facts["enbridge-line-7"], route_name="Enbridge Line 13 / Southern Lights",
                       menu_section="Diluent pipelines", product="Diluent")
        output, metadata = pipelines.build_product_network_features([feature], {}, {identity: details})
        props = output[0]["properties"]
        self.assertEqual(props["route_name"], details["route_name"])
        self.assertEqual(props["menu_section"], "Diluent pipelines")
        self.assertEqual(props["source_feature_ids"], [1])
        self.assertEqual(metadata["source_feature_count"], 1)
        collection = dict(features=output, metadata=dict(product_networks=metadata))
        self.assertEqual(infrastructure.validate_product_networks(collection), [])


if __name__ == "__main__":
    unittest.main()
