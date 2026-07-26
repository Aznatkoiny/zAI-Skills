#!/usr/bin/env python3
"""
Offline unit checks for the real-estate-data MCP server.

Stubs the `mcp` package (so the real dependency is not required) and all
network calls, then exercises the cache, the Rentcast quota counter, the
Redfin streaming snapshot parser, and the FRED tool.

Run with:  python3 -m unittest test_server -v
"""

import gzip
import io
import json
import os
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

# --- Stub the mcp package so server.py imports without the real dependency ---
if "mcp.server.fastmcp" not in sys.modules:
    fastmcp_mod = types.ModuleType("mcp.server.fastmcp")

    class _FakeFastMCP:
        def __init__(self, name):
            self.name = name

        def tool(self):
            def decorator(fn):
                return fn
            return decorator

        def run(self):
            raise RuntimeError("not runnable in tests")

    fastmcp_mod.FastMCP = _FakeFastMCP
    mcp_mod = types.ModuleType("mcp")
    server_mod = types.ModuleType("mcp.server")
    server_mod.fastmcp = fastmcp_mod
    mcp_mod.server = server_mod
    sys.modules["mcp"] = mcp_mod
    sys.modules["mcp.server"] = server_mod
    sys.modules["mcp.server.fastmcp"] = fastmcp_mod

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server  # noqa: E402


class CacheDirTestCase(unittest.TestCase):
    """Base: every test gets its own throwaway cache dir."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_env = os.environ.get("REAL_ESTATE_DATA_CACHE_DIR")
        os.environ["REAL_ESTATE_DATA_CACHE_DIR"] = self._tmp.name

    def tearDown(self):
        if self._old_env is None:
            os.environ.pop("REAL_ESTATE_DATA_CACHE_DIR", None)
        else:
            os.environ["REAL_ESTATE_DATA_CACHE_DIR"] = self._old_env
        self._tmp.cleanup()


class TestCache(CacheDirTestCase):
    def test_roundtrip(self):
        server._cache_put("t", "key1", {"a": 1})
        self.assertEqual(server._cache_get("t", "key1", 3600), {"a": 1})

    def test_miss(self):
        self.assertIsNone(server._cache_get("t", "nope", 3600))

    def test_ttl_expiry(self):
        server._cache_put("t", "key2", [1, 2])
        path = server._cache_path("t", "key2")
        old = time.time() - 7200
        os.utime(path, (old, old))
        self.assertIsNone(server._cache_get("t", "key2", 3600))
        self.assertEqual(server._cache_get("t", "key2", 8000), [1, 2])

    def test_unwritable_dir_is_tolerated(self):
        # Point the cache dir below a regular file: makedirs must fail.
        blocker = os.path.join(self._tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        os.environ["REAL_ESTATE_DATA_CACHE_DIR"] = os.path.join(blocker, "sub")
        server._cache_put("t", "key3", {"a": 1})  # must not raise
        self.assertIsNone(server._cache_get("t", "key3", 3600))


class TestRentcastQuota(CacheDirTestCase):
    def test_counter_increments_and_persists(self):
        self.assertEqual(server._rentcast_usage(), 0)
        self.assertEqual(server._rentcast_usage(increment=True), 1)
        self.assertEqual(server._rentcast_usage(increment=True), 2)
        self.assertEqual(server._rentcast_usage(), 2)

    def test_month_rollover_resets(self):
        server._rentcast_usage(increment=True)
        with open(server._rentcast_counter_path(), "w") as f:
            json.dump({"month": "1999-01", "count": 42}, f)
        self.assertEqual(server._rentcast_usage(), 0)

    def test_unwritable_dir_returns_minus_one(self):
        blocker = os.path.join(self._tmp.name, "blocker")
        with open(blocker, "w") as f:
            f.write("x")
        os.environ["REAL_ESTATE_DATA_CACHE_DIR"] = os.path.join(blocker, "sub")
        self.assertEqual(server._rentcast_usage(increment=True), -1)

    def test_quota_note_format(self):
        out = server._with_rentcast_quota({"rent": 2000}, 3)
        self.assertEqual(out["rentcast_quota"], "3/50 free-tier calls used this month")
        self.assertNotIn("rentcast_quota_warning", out)

    def test_quota_warning_at_threshold(self):
        out = server._with_rentcast_quota({"rent": 2000}, 45)
        self.assertIn("rentcast_quota_warning", out)

    def test_quota_note_on_untrackable(self):
        out = server._with_rentcast_quota({"rent": 2000}, -1)
        self.assertIn("tracking unavailable", out["rentcast_quota"])

    def test_rentcast_tool_appends_quota_and_caches(self):
        body = json.dumps({"rent": 2450}).encode()
        with mock.patch.dict(os.environ, {"RENTCAST_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen",
                                  return_value=io.BytesIO(body)) as m:
            first = json.loads(server.get_rentcast_market_data("90210"))
            self.assertEqual(first["rent"], 2450)
            self.assertEqual(first["rentcast_quota"],
                             "1/50 free-tier calls used this month")
            self.assertEqual(m.call_count, 1)
            # Second call is served from cache: no network, no quota burn.
            second = json.loads(server.get_rentcast_market_data("90210"))
            self.assertTrue(second["served_from_cache"])
            self.assertEqual(second["rentcast_quota"],
                             "1/50 free-tier calls used this month")
            self.assertEqual(m.call_count, 1)


def _gz(tsv: str) -> io.BytesIO:
    return io.BytesIO(gzip.compress(tsv.encode()))


_REDFIN_HEADER = ("period_begin\tperiod_end\tperiod_duration\tregion_type\t"
                  "region\tis_seasonally_adjusted\tproperty_type\t"
                  "median_sale_price\thomes_sold\tinventory\tmedian_dom\t"
                  "months_of_supply\n")


def _redfin_row(begin, end, region, price, sold="10", inv="20", dom="30",
                supply="2.5", ptype="All Residential", adj="f", dur="30"):
    return (f"{begin}\t{end}\t{dur}\tzip\t{region}\t{adj}\t{ptype}\t"
            f"{price}\t{sold}\t{inv}\t{dom}\t{supply}\n")


class TestRedfinSnapshot(CacheDirTestCase):
    def _fake_file(self):
        tsv = _REDFIN_HEADER
        tsv += _redfin_row("2026-05-01", "2026-05-31", "Zip Code: 90210", "3500000")
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Zip Code: 90210", "3600000.0")
        # Rows that must be filtered out:
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Zip Code: 90210", "9999999",
                           ptype="Condo/Co-op")
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Zip Code: 90210", "8888888",
                           adj="t")
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Zip Code: 10001", "1200000")
        return _gz(tsv)

    def test_filters_and_orders_rows(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()):
            result = json.loads(server.get_redfin_market_snapshot("90210", "zip", 24))
        self.assertEqual(result["region"], "Zip Code: 90210")
        self.assertEqual(result["months_returned"], 2)
        self.assertFalse(result["served_from_cache"])
        newest = result["monthly"][0]
        self.assertEqual(newest["period_begin"], "2026-06-01")
        self.assertEqual(newest["median_sale_price"], 3600000)  # whole float -> int
        self.assertEqual(newest["months_of_supply"], 2.5)
        self.assertEqual(result["monthly"][1]["median_sale_price"], 3500000)

    def test_months_slice_and_cache_hit(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()) as m:
            server.get_redfin_market_snapshot("90210", "zip", 24)
            # Different months value must hit the cached slice, not the network.
            result = json.loads(server.get_redfin_market_snapshot("90210", "zip", 1))
            self.assertEqual(m.call_count, 1)
        self.assertTrue(result["served_from_cache"])
        self.assertEqual(result["months_returned"], 1)
        self.assertEqual(result["monthly"][0]["period_begin"], "2026-06-01")

    def test_no_match_lists_examples(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()):
            result = json.loads(server.get_redfin_market_snapshot("00000", "zip"))
        self.assertIn("error", result)
        self.assertIn("region_name_examples", result)
        self.assertIn("Zip Code: 90210", result["sample_regions_in_file"])

    def test_ambiguous_match_lists_candidates(self):
        tsv = _REDFIN_HEADER
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Springfield, IL", "200000")
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Springfield, MO", "210000")
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_gz(tsv)):
            result = json.loads(
                server.get_redfin_market_snapshot("Springfield", "place"))
        self.assertIn("error", result)
        self.assertEqual(sorted(result["matching_regions"]),
                         ["Springfield, IL", "Springfield, MO"])

    def test_exact_match_wins_over_substring(self):
        tsv = _REDFIN_HEADER
        tsv += _redfin_row("2026-06-01", "2026-06-30", "Los Angeles, CA", "900000")
        tsv += _redfin_row("2026-06-01", "2026-06-30", "East Los Angeles, CA", "600000")
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_gz(tsv)):
            result = json.loads(
                server.get_redfin_market_snapshot("Los Angeles, CA", "place"))
        self.assertEqual(result["region"], "Los Angeles, CA")
        self.assertEqual(result["monthly"][0]["median_sale_price"], 900000)

    def test_invalid_region_type(self):
        result = json.loads(server.get_redfin_market_snapshot("90210", "galaxy"))
        self.assertIn("error", result)
        self.assertEqual(result["valid_region_types"],
                         ["county", "metro", "place", "zip"])

    def test_invalid_zip(self):
        result = json.loads(server.get_redfin_market_snapshot("Beverly Hills", "zip"))
        self.assertIn("5-digit", result["error"])


class TestRedfinRealFileFormat(CacheDirTestCase):
    """The live S3 files use quoted UPPERCASE headers, quoted string values,
    and true/false for IS_SEASONALLY_ADJUSTED."""

    def test_real_style_header_and_values(self):
        header = ('"PERIOD_BEGIN"\t"PERIOD_END"\t"PERIOD_DURATION"\t'
                  '"REGION_TYPE"\t"IS_SEASONALLY_ADJUSTED"\t"REGION"\t'
                  '"PROPERTY_TYPE"\t"MEDIAN_SALE_PRICE"\t"HOMES_SOLD"\t'
                  '"INVENTORY"\t"MEDIAN_DOM"\t"MONTHS_OF_SUPPLY"\n')
        row = ('"2026-05-01"\t"2026-05-31"\t30\t"metro"\tfalse\t'
               '"Boise City, ID metro area"\t"All Residential"\t'
               '512000\t900\t1800\t21\t2\n')
        adj_row = ('"2026-05-01"\t"2026-05-31"\t30\t"metro"\ttrue\t'
                   '"Boise City, ID metro area"\t"All Residential"\t'
                   '999999\t900\t1800\t21\t2\n')
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_gz(header + row + adj_row)):
            result = json.loads(
                server.get_redfin_market_snapshot("Boise", "metro", 12))
        self.assertEqual(result["region"], "Boise City, ID metro area")
        self.assertEqual(result["months_returned"], 1)
        self.assertEqual(result["monthly"][0]["median_sale_price"], 512000)


class TestFred(CacheDirTestCase):
    def test_no_key_error(self):
        env = {k: v for k, v in os.environ.items() if k != "FRED_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = json.loads(server.get_fred_series("MORTGAGE30US"))
        self.assertIn("FRED_API_KEY not configured", result["error"])
        self.assertIn("https://fred.stlouisfed.org/docs/api/api_key.html",
                      result["info"])

    def test_invalid_series_id(self):
        result = json.loads(server.get_fred_series("not a series!"))
        self.assertIn("Invalid series_id", result["error"])

    def test_success_parses_and_caches(self):
        body = json.dumps({"observations": [
            {"date": "2026-07-23", "value": "6.72"},
            {"date": "2026-07-16", "value": "."},
        ]}).encode()
        with mock.patch.dict(os.environ, {"FRED_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen",
                                  return_value=io.BytesIO(body)) as m:
            result = json.loads(server.get_fred_series("MORTGAGE30US", 2))
            self.assertEqual(result["series_id"], "MORTGAGE30US")
            self.assertEqual(result["observations"][0],
                             {"date": "2026-07-23", "value": 6.72})
            self.assertIsNone(result["observations"][1]["value"])
            cached = json.loads(server.get_fred_series("MORTGAGE30US", 2))
            self.assertTrue(cached["served_from_cache"])
            self.assertEqual(m.call_count, 1)


class TestCensusCache(CacheDirTestCase):
    def test_fetch_acs_cached(self):
        body = json.dumps([["B01003_001E"], ["12345"]]).encode()
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=io.BytesIO(body)) as m:
            data, vintage = server._fetch_acs(["B01003_001E"], "for=state:06", "k", 2023)
            self.assertEqual(data[1], ["12345"])
            self.assertEqual(vintage, 2023)
            data2, vintage2 = server._fetch_acs(["B01003_001E"], "for=state:06", "k", 2023)
            self.assertEqual((data2, vintage2), (data, vintage))
            self.assertEqual(m.call_count, 1)


class TestGuidanceToolPointer(unittest.TestCase):
    def test_points_to_snapshot_tool(self):
        result = json.loads(server.get_redfin_market_data("metro"))
        self.assertIn("get_redfin_market_snapshot", result["see_also"])


if __name__ == "__main__":
    unittest.main()
