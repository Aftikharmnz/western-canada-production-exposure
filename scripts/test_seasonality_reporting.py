"""Synthetic fixtures for actual values and source/stream reporting metadata."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_seasonality_index as seasonality
import run_etl as etl


def asset(aid, **kwargs):
    return dict(asset_id=aid, latitude=51.0, longitude=-113.0, asset_kind="well", is_rollup=False, **kwargs)


def record(aid, month, value, source="source", stream="Oil", scenario="actual"):
    return dict(asset_id=aid, date=f"{month}-01", volume_kbbl_d=value,
                source_id=source, stream=stream, scenario=scenario)


def group(month, rows, source="source", stream="Oil", scenario="actual"):
    return dict(date=f"{month}-01", rows=rows, source_id=source, stream=stream,
                scenario=scenario, asset_ref="assets.rows")


class SeasonalityReportingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=etl.ROOT)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "monthly").mkdir()

    def write_dataset(self, assets, records=None, months=None, compact_assets=True):
        if compact_assets:
            fields = ["asset_id", "latitude", "longitude", "asset_kind", "is_rollup"]
            assets = dict(fields=fields, rows=[[row.get(field) for field in fields] for row in assets])
        (self.root / "assets.json").write_text(json.dumps(assets), encoding="utf-8")
        (self.root / "monthly_production.json").write_text(json.dumps(records or []), encoding="utf-8")
        for filename, payload in (months or {}).items():
            (self.root / "monthly" / filename).write_text(json.dumps(payload), encoding="utf-8")

    def build(self):
        with redirect_stdout(io.StringIO()):
            return seasonality.build_index(self.root)

    def test_metadata_groups_and_months_are_deterministic(self):
        rows = [record("one", "2026-03", 3, "zeta", "Oil"),
                record("one", "2026-01", 1, "alpha", "Gas"),
                record("one", "2026-02", 2, "alpha", "Gas")]
        self.write_dataset([asset("one")], rows)
        first = self.build()
        self.write_dataset([asset("one")], list(reversed(rows)))
        second = self.build()

        self.assertEqual(first, second)
        self.assertEqual(first["__reporting"]["schema_version"], 1)
        self.assertEqual(first["__reporting"]["groups"], [
            dict(source_id="alpha", stream="Gas", months=["2026-01", "2026-02"]),
            dict(source_id="zeta", stream="Oil", months=["2026-03"]),
        ])
        self.assertEqual(first["one"]["__groups"], [0, 1])

    def test_unmapped_and_excluded_observations_still_establish_group_availability(self):
        rows = [asset("mapped"), asset("unmapped"), asset("rollup"), asset("province")]
        rows[1]["latitude"] = None
        rows[2]["is_rollup"] = True
        rows[3]["asset_kind"] = "province"
        self.write_dataset(rows, [record("mapped", "2026-01", 1)], {
            "observations.json": [group("2026-02", [[1, 2]]),
                                  group("2026-03", [[2, 3]]),
                                  group("2026-04", [[3, 0]], "other", "Oil")],
        })
        result = self.build()

        self.assertEqual(set(result), {"mapped", "__reporting"})
        self.assertEqual(result["__reporting"]["groups"], [
            dict(source_id="other", stream="Oil", months=["2026-04"]),
            dict(source_id="source", stream="Oil", months=["2026-01", "2026-02", "2026-03"]),
        ])
        self.assertEqual(result["mapped"]["__groups"], [1])
        self.assertNotIn("__month_groups", result["mapped"])

    def test_zero_is_observed_while_missing_invalid_and_forecast_values_are_excluded(self):
        base = [record("one", "2026-01", 0), record("one", "2026-02", 100, scenario="forecast"),
                record("one", "2026-03", None), record("one", "2026-04", -1),
                record("one", "2026-05", float("nan")), record("one", "2026-06", float("inf")),
                record("one", "2026-07", True)]
        self.write_dataset([asset("one")], base, {
            "compact.json": [group("2026-09", [[0, 0]]), group("2026-10", [[0, 200]], scenario="forecast"),
                             group("2026-11", [[0, None], [0, -10], [0, float("nan")]])],
        })
        result = self.build()

        self.assertEqual(result["one"], {"2026-01": 0, "2026-09": 0, "__groups": [0]})
        self.assertEqual(result["__reporting"]["groups"][0]["months"], ["2026-01", "2026-09"])
        self.assertNotIn("2026-08", result["one"])

    def test_multi_stream_month_membership_preserves_a_missing_component(self):
        self.write_dataset([asset("multi"), asset("other")], [record("multi", "2026-01", 2, stream="Propane")], {
            "february.json": [group("2026-02", [[0, 3]], stream="Propane"),
                              group("2026-02", [[0, 5]], stream="Butane")],
            "march.json": [group("2026-03", [[0, 4]], stream="Propane"),
                           group("2026-03", [[1, 8]], stream="Butane")],
            "april.json": [group("2026-04", [[0, 0]], stream="Butane"),
                           group("2026-04", [[0, 0]], stream="Propane")],
        })
        result = self.build()

        self.assertEqual(result["multi"]["2026-02"], 8)
        self.assertEqual(result["multi"]["2026-03"], 4)
        self.assertEqual(result["multi"]["2026-04"], 0)
        self.assertEqual(result["multi"]["__groups"], [0, 1])
        self.assertEqual(result["multi"]["__month_groups"], {
            "2026-01": [1], "2026-02": [0, 1], "2026-03": [1], "2026-04": [0, 1],
        })
        self.assertEqual(result["__reporting"]["groups"][0]["months"], ["2026-02", "2026-03", "2026-04"])
        self.assertNotIn("__month_groups", result["other"])

    def test_plain_assets_and_legacy_monthly_records_remain_supported(self):
        self.write_dataset([asset("one")], [record("one", "2026-01", 2)], {
            "legacy.json": [record("one", "2026-01", 3), record("one", "2026-02", 0)],
        }, compact_assets=False)
        result = self.build()
        self.assertEqual(result["one"], {"2026-01": 5, "2026-02": 0, "__groups": [0]})

    def test_compact_export_keeps_explicit_zero_and_filters_null_negative_and_unknown_assets(self):
        rows = [record("one", "2026-01", value) for value in (0, None, -1, 2.5)]
        rows.append(record("unknown", "2026-01", 0))
        payload = etl.compact_on_demand_payload(rows, {"one": 0})
        self.assertEqual(payload["rows"], [[0, 0.0], [0, 2.5]])
        self.write_dataset([asset("one")], months={"exported.json": payload})
        self.assertEqual(self.build()["one"]["2026-01"], 2.5)

    def test_failed_atomic_replacement_preserves_previous_index(self):
        output = self.root / "asset_seasonality.json"
        output.write_text('{"previous":{}}', encoding="utf-8")
        with patch.object(Path, "replace", side_effect=OSError("replacement failed")):
            with self.assertRaisesRegex(OSError, "replacement failed"):
                seasonality.write_index({"new": {"2026-01": 0}}, output)
        self.assertEqual(output.read_text(encoding="utf-8"), '{"previous":{}}')

    def test_main_writes_the_requested_dataset_without_leaving_temporary_file(self):
        self.write_dataset([asset("one")], [record("one", "2026-01", 0)])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(seasonality.main(["--data-dir", str(self.root)]), 0)
        output = self.root / "asset_seasonality.json"
        result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["one"]["2026-01"], 0)
        self.assertFalse(output.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
