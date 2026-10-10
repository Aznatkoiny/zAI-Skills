#!/usr/bin/env python3
"""
Offline unit checks for the real-estate-data MCP server.

Stubs the `mcp` package (so the real dependency is not required) and all
network calls, then exercises the cache, the Rentcast quota counter, the
Redfin streaming snapshot parser, and the FRED tool.

Run with:  python3 -m unittest test_server -v
"""

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


class TestRentcastOverageGate(CacheDirTestCase):
    def _fill_quota(self):
        for _ in range(server.RENTCAST_FREE_TIER_LIMIT):
            server._rentcast_usage(increment=True)

    def test_blocks_at_limit(self):
        self._fill_quota()
        env = {k: v for k, v in os.environ.items() if k != "RENTCAST_ALLOW_OVERAGE"}
        env["RENTCAST_API_KEY"] = "k"
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(server.urllib.request, "urlopen") as m:
            result = json.loads(server.get_rentcast_market_data("90210"))
            self.assertEqual(m.call_count, 0)
        self.assertIn("free-tier limit reached", result["error"])

    def test_overage_opt_in(self):
        self._fill_quota()
        body = json.dumps({"rent": 2450}).encode()
        with mock.patch.dict(os.environ, {"RENTCAST_API_KEY": "k",
                                          "RENTCAST_ALLOW_OVERAGE": "1"}), \
                mock.patch.object(server.urllib.request, "urlopen",
                                  return_value=io.BytesIO(body)) as m:
            result = json.loads(server.get_rentcast_market_data("90210"))
            self.assertEqual(m.call_count, 1)
        self.assertEqual(result["rent"], 2450)


class _Resp(io.BytesIO):
    pass


def _json_resp(obj):
    return _Resp(json.dumps(obj).encode())


class TestPaidProviders(unittest.TestCase):
    def test_airdna_two_step(self):
        responses = [_json_resp({"payload": {"results": [{"id": "airdna-163", "name": "Austin"},
                                                         {"id": "airdna-9", "name": "Austin West"}]}})]
        responses += [_json_resp({"metric": m}) for m in server.AIRDNA_MARKET_METRICS]
        with mock.patch.dict(os.environ, {"AIRDNA_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen", side_effect=responses) as m:
            result = json.loads(server.get_airdna_market_stats("Austin", "tx"))
        first = m.call_args_list[0].args[0]
        self.assertTrue(first.full_url.endswith("/api/enterprise/v2/market/search"))
        self.assertEqual(json.loads(first.data), {"search_term": "Austin, TX"})
        self.assertIn("/market/airdna-163/metrics/occupancy", m.call_args_list[1].args[0].full_url)
        self.assertEqual(result["market"]["id"], "airdna-163")
        self.assertEqual(result["metrics"]["adr"], {"metric": "adr"})

    def test_mashvisor_lookup_then_overview(self):
        responses = [_json_resp({"content": {"results": [{"id": 101, "name": "Silver Lake"},
                                                         {"id": 102, "name": "Echo Park"}]}}),
                     _json_resp({"content": {"occupancy": 0.6}})]
        with mock.patch.dict(os.environ, {"MASHVISOR_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen", side_effect=responses) as m:
            result = json.loads(server.get_mashvisor_neighborhood("Los Angeles", "ca", "silver lake"))
        self.assertIn("/city/neighborhoods/CA/Los%20Angeles", m.call_args_list[0].args[0].full_url)
        self.assertIn("/neighborhood/101/bar?state=CA", m.call_args_list[1].args[0].full_url)
        self.assertEqual(result["neighborhood_id"], "101")

    def test_mashvisor_lists_when_ambiguous(self):
        responses = [_json_resp({"content": [{"id": 1, "name": "Downtown"}, {"id": 2, "name": "Midtown"}]})]
        with mock.patch.dict(os.environ, {"MASHVISOR_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen", side_effect=responses):
            result = json.loads(server.get_mashvisor_neighborhood("Austin", "TX"))
        self.assertEqual([h["id"] for h in result["neighborhoods"]], [1, 2])

    def test_attom_avm_endpoint(self):
        with mock.patch.dict(os.environ, {"ATTOM_API_KEY": "k"}), \
                mock.patch.object(server.urllib.request, "urlopen",
                                  return_value=_json_resp({"property": []})) as m:
            server.get_attom_valuation("123 Main St, Austin, TX 78704")
        req = m.call_args.args[0]
        self.assertIn("/propertyapi/v1.0.0/attomavm/detail?address1=123+Main+St", req.full_url)
        self.assertEqual(req.get_header("Apikey"), "k")

    def test_missing_key_message(self):
        env = {k: v for k, v in os.environ.items() if k != "ATTOM_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = json.loads(server.get_attom_property("1 A St, B, TX 78704"))
        self.assertIn("ATTOM_API_KEY not configured", result["error"])
        self.assertIn("settings.json", result["info"])


class TestCensusParsing(unittest.TestCase):
    def test_sentinels_become_none(self):
        self.assertIsNone(server._acs_int("-666666666"))
        self.assertIsNone(server._acs_int("-999999999"))
        self.assertIsNone(server._acs_int(None))
        self.assertEqual(server._acs_int("1234"), 1234)
        self.assertEqual(server._acs_int("-5"), -5)

    def test_year_built_labels_follow_vintage(self):
        row = ["500000"] + ["10"] * 11 + ["06"]
        with mock.patch.dict(os.environ, {"CENSUS_API_KEY": "k"}), \
                mock.patch.object(server, "_fetch_acs", return_value=([["h"], row], 2024)):
            new = json.loads(server.get_census_housing_stats("06"))
        self.assertIn("2020_or_later", new["year_built_distribution"])
        with mock.patch.dict(os.environ, {"CENSUS_API_KEY": "k"}), \
                mock.patch.object(server, "_fetch_acs", return_value=([["h"], row], 2019)):
            old = json.loads(server.get_census_housing_stats("06", year=2019))
        self.assertIn("2014_or_later", old["year_built_distribution"])


_REDFIN_HEADER = ('"LAST UPDATED","FREQUENCY","PERIOD BEGIN","PERIOD END","REGION ID",'
                  '"REGION TYPE","REGION NAME","HOMES SOLD","MEDIAN SALE PRICE NSA ($)",'
                  '"MEDIAN SALE PRICE NSA YOY (%)","MEDIAN DAYS ON MARKET (DAYS)",'
                  '"AVERAGE SALE TO LIST RATIO (%)","NEW LISTINGS","INVENTORY",'
                  '"MEDIAN SALE PRICE PER SQ.FT. ($)","MONTHS OF SUPPLY"\n')


def _redfin_row(begin, end, region, price, freq="Monthly", sold="10", inv="20",
                dom="30", supply="2.5", rtype="Zip Code"):
    return (f'"2026-08-15","{freq}","{begin}","{end}","1","{rtype}","{region}",'
            f'{sold},{price},4.1,{dom},99.2,12,{inv},410,{supply}\n')


def _csv(text: str) -> io.BytesIO:
    return io.BytesIO(text.encode())


class TestRedfinSnapshot(CacheDirTestCase):
    def _fake_file(self):
        csv_text = _REDFIN_HEADER
        csv_text += _redfin_row("2026-05-01", "2026-05-31", "90210", "3500000")
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "90210", "3600000.0")
        # Rolling 3-month rows are ignored when monthly rows exist.
        csv_text += _redfin_row("2026-04-01", "2026-06-30", "90210", "9999999",
                                freq="Rolling 3 Months")
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "10001", "1200000")
        return _csv(csv_text)

    def test_filters_and_orders_rows(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()):
            result = json.loads(server.get_redfin_market_snapshot("90210", "zip", 24))
        self.assertEqual(result["region"], "90210")
        self.assertEqual(result["period_type"], "Monthly")
        self.assertEqual(result["periods_returned"], 2)
        self.assertEqual(result["latest_period_end"], "2026-06-30")
        self.assertFalse(result["served_from_cache"])
        newest = result["periods"][0]
        self.assertEqual(newest["period_begin"], "2026-06-01")
        self.assertEqual(newest["median_sale_price"], 3600000)  # whole float -> int
        self.assertEqual(newest["months_of_supply"], 2.5)
        self.assertEqual(newest["median_sale_price_per_sqft"], 410)
        self.assertEqual(result["periods"][1]["median_sale_price"], 3500000)

    def test_rolling_fallback_and_na(self):
        csv_text = _REDFIN_HEADER
        csv_text += _redfin_row("2026-04-01", "2026-06-30", "78704", "NA",
                                freq="Rolling 3 Months")
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_csv(csv_text)):
            result = json.loads(server.get_redfin_market_snapshot("78704", "zip"))
        self.assertEqual(result["period_type"], "Rolling 3 Months")
        self.assertIsNone(result["periods"][0]["median_sale_price"])

    def test_months_slice_and_cache_hit(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()) as m:
            server.get_redfin_market_snapshot("90210", "zip", 24)
            # Different months value must hit the cached series, not the network.
            result = json.loads(server.get_redfin_market_snapshot("90210", "zip", 1))
            self.assertEqual(m.call_count, 1)
        self.assertTrue(result["served_from_cache"])
        self.assertEqual(result["periods_returned"], 1)
        self.assertEqual(result["periods"][0]["period_begin"], "2026-06-01")

    def test_multiple_regions_one_download(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()) as m:
            result = json.loads(server.get_redfin_market_snapshot("90210 | 10001", "zip"))
            self.assertEqual(m.call_count, 1)
        regions = [r["region"] for r in result["results"]]
        self.assertEqual(regions, ["90210", "10001"])

    def test_no_match_lists_examples(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=self._fake_file()):
            result = json.loads(server.get_redfin_market_snapshot("00000", "zip"))
        self.assertIn("error", result)
        self.assertIn("region_name_examples", result)
        self.assertIn("90210", result["sample_regions_in_file"])

    def test_ambiguous_match_lists_candidates(self):
        csv_text = _REDFIN_HEADER
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "Springfield, IL", "200000", rtype="City")
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "Springfield, MO", "210000", rtype="City")
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_csv(csv_text)):
            result = json.loads(
                server.get_redfin_market_snapshot("Springfield", "place"))
        self.assertIn("error", result)
        self.assertEqual(sorted(result["matching_regions"]),
                         ["Springfield, IL", "Springfield, MO"])

    def test_exact_match_wins_over_substring(self):
        csv_text = _REDFIN_HEADER
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "Los Angeles, CA", "900000", rtype="City")
        csv_text += _redfin_row("2026-06-01", "2026-06-30", "East Los Angeles, CA", "600000", rtype="City")
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_csv(csv_text)):
            result = json.loads(
                server.get_redfin_market_snapshot("Los Angeles, CA", "place"))
        self.assertEqual(result["region"], "Los Angeles, CA")
        self.assertEqual(result["periods"][0]["median_sale_price"], 900000)

    def test_missing_column_is_reported(self):
        with mock.patch.object(server.urllib.request, "urlopen",
                               return_value=_csv('"REGION NAME","FREQUENCY"\n"x","Monthly"\n')):
            result = json.loads(server.get_redfin_market_snapshot("x", "metro"))
        self.assertIn("missing expected columns", result["error"])

    def test_invalid_region_type(self):
        result = json.loads(server.get_redfin_market_snapshot("90210", "galaxy"))
        self.assertIn("error", result)
        self.assertEqual(result["valid_region_types"],
                         ["county", "metro", "national", "place", "state", "zip"])

    def test_invalid_zip(self):
        result = json.loads(server.get_redfin_market_snapshot("Beverly Hills", "zip"))
        self.assertIn("5-digit", result["error"])


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
