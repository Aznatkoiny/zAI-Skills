#!/usr/bin/env python3
"""
Real Estate Data MCP Server
Provides tools for accessing multiple real estate data APIs including Census Bureau,
Redfin Data Center, FRED, Rentcast, Mashvisor, AirDNA, and ATTOM.

Responses from slow or quota-limited sources are cached on disk under
~/.cache/real-estate-data/ (best-effort: an unwritable cache dir just disables
caching). Rentcast free-tier usage is tracked with a persistent monthly counter
in the same directory.
"""

from mcp.server.fastmcp import FastMCP
import datetime
import hashlib
import io
import os
import json
import re
import tempfile
import time
import urllib.request
import urllib.parse
import urllib.error

mcp = FastMCP("real-estate-data")


# ============================================================================
# Shared Helpers
# ============================================================================

def _validate_geography(state_fips: str, county_fips: str = "", tract: str = "") -> str:
    """Validate Census FIPS geography inputs. Returns an error message, or "" if valid."""
    if not re.fullmatch(r"\d{2}", state_fips):
        return "Invalid state_fips: must be exactly 2 digits (e.g., '06' for California)."
    if county_fips and not re.fullmatch(r"\d{3}", county_fips):
        return "Invalid county_fips: must be exactly 3 digits (e.g., '037' for Los Angeles County)."
    if tract and not re.fullmatch(r"\d{6}", tract):
        return "Invalid tract: must be exactly 6 digits (e.g., '101110')."
    if tract and not county_fips:
        return ("tract requires county_fips: census tracts are only unique within a county, "
                "so provide the 3-digit county_fips along with the tract.")
    return ""


def _validate_zip(zip_code: str) -> str:
    """Validate a 5-digit ZIP code. Returns an error message, or "" if valid."""
    if not re.fullmatch(r"\d{5}", zip_code):
        return "Invalid zip_code: must be exactly 5 digits (e.g., '90001')."
    return ""


def _missing_key(var: str, signup: str) -> str:
    return json.dumps({
        "error": f"{var} not configured.",
        "info": (f"{signup} Set {var} in your shell profile (export {var}=...) or under \"env\" "
                 "in ~/.claude/settings.json, then restart Claude Code."),
    })


def _acs_int(raw):
    """Parse an ACS estimate. Census encodes "no estimate" as large negative
    sentinels (-666666666, -999999999, -888888888, ...), which become None."""
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= -100000000:
        return None
    return int(value)


def _fetch_acs(variables: list, geography: str, api_key: str, year: int):
    """Fetch ACS 5-year data from the Census API.

    If year is 0 (not specified), tries the latest likely vintage
    (current year minus 2) and falls back one more year if that vintage
    is not yet published (HTTP 404).

    Returns (data, vintage_year). Raises urllib.error.HTTPError/URLError
    on unrecoverable errors. Successful responses are cached on disk for
    7 days (keyed by variables, geography, and requested year).
    """
    cache_key = f"{geography}|{','.join(variables)}|{year}"
    cached = _cache_get("census", cache_key, CACHE_TTL_CENSUS)
    if cached is not None:
        return cached["data"], cached["vintage"]

    if year:
        candidates = [year]
    else:
        latest = datetime.date.today().year - 2
        candidates = [latest, latest - 1]

    params = {"get": ",".join(variables), "key": api_key}
    query = urllib.parse.urlencode(params)

    for i, vintage in enumerate(candidates):
        url = f"https://api.census.gov/data/{vintage}/acs/acs5?{query}&{geography}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode())
            _cache_put("census", cache_key, {"data": data, "vintage": vintage})
            return data, vintage
        except urllib.error.HTTPError as e:
            if e.code == 404 and i < len(candidates) - 1:
                continue
            raise


# ============================================================================
# File Cache (best-effort, under ~/.cache/real-estate-data/)
# ============================================================================

CACHE_TTL_MARKET = 24 * 3600      # API market data (Rentcast, FRED): 24 hours
CACHE_TTL_CENSUS = 7 * 24 * 3600  # Census ACS data: 7 days
CACHE_TTL_REDFIN = 24 * 3600      # Filtered Redfin region series: 24 hours


def _cache_dir() -> str:
    """Cache directory (override with REAL_ESTATE_DATA_CACHE_DIR, e.g., in tests)."""
    override = os.environ.get("REAL_ESTATE_DATA_CACHE_DIR", "")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), ".cache", "real-estate-data")


def _cache_path(namespace: str, key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return os.path.join(_cache_dir(), f"{namespace}-{digest}.json")


def _cache_get(namespace: str, key: str, ttl_seconds: int):
    """Return the cached JSON value for key, or None if absent/stale/unreadable."""
    path = _cache_path(namespace, key)
    try:
        if time.time() - os.path.getmtime(path) > ttl_seconds:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _cache_put(namespace: str, key: str, value) -> None:
    """Best-effort cache write (atomic via temp file + rename).

    An unwritable cache dir just disables caching; it never breaks a tool call.
    """
    tmp_path = None
    try:
        cache_dir = _cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=cache_dir, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f)
        os.replace(tmp_path, _cache_path(namespace, key))
    except (OSError, TypeError, ValueError):
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ============================================================================
# Rentcast Free-Tier Quota Guard (persistent monthly counter)
# ============================================================================

RENTCAST_FREE_TIER_LIMIT = 50
RENTCAST_WARN_THRESHOLD = 45


def _rentcast_counter_path() -> str:
    return os.path.join(_cache_dir(), "rentcast-usage.json")


def _rentcast_usage(increment: bool = False) -> int:
    """Read (and optionally increment) the persistent monthly Rentcast counter.

    Returns the number of calls recorded for the current month. Returns -1 if
    increment was requested but the counter file could not be persisted (e.g.,
    unwritable cache dir), signaling that usage tracking is unavailable.
    """
    month = datetime.date.today().strftime("%Y-%m")
    path = _rentcast_counter_path()
    count = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        if state.get("month") == month:
            count = int(state.get("count", 0))
    except (OSError, ValueError, TypeError):
        pass  # missing/corrupt counter file: start from 0 for this month

    if increment:
        count += 1
        tmp_path = None
        try:
            cache_dir = _cache_dir()
            os.makedirs(cache_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=cache_dir, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"month": month, "count": count}, f)
            os.replace(tmp_path, path)
        except (OSError, TypeError, ValueError):
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return -1
    return count


def _with_rentcast_quota(data, count: int, from_cache: bool = False) -> dict:
    """Attach the monthly free-tier usage note (and warning) to a Rentcast response."""
    out = dict(data) if isinstance(data, dict) else {"data": data}
    if count < 0:
        out["rentcast_quota"] = (
            "Rentcast free-tier usage tracking unavailable "
            "(cache directory is not writable)."
        )
    else:
        out["rentcast_quota"] = (
            f"{count}/{RENTCAST_FREE_TIER_LIMIT} free-tier calls used this month"
        )
        if count >= RENTCAST_WARN_THRESHOLD:
            out["rentcast_quota_warning"] = (
                f"Approaching the Rentcast free-tier limit of "
                f"{RENTCAST_FREE_TIER_LIMIT} calls/month. At the limit, live calls stop "
                "unless RENTCAST_ALLOW_OVERAGE=1 is set; cached responses don't count."
            )
    if from_cache:
        out["served_from_cache"] = True
    return out


def _attom_address_params(address: str):
    """Split a one-line address into ATTOM's address1/address2 query parameters.

    ATTOM's propertyapi requires the street portion (address1) and the
    city/state/zip portion (address2) as separate parameters rather than a
    single address string.

    Returns (params, error): params is a dict and error is "" on success;
    params is None and error is a message on failure.
    """
    address1, _, address2 = address.partition(",")
    address1 = address1.strip()
    address2 = address2.strip()
    if not address1 or not address2:
        return None, ("Address must include a comma separating the street from the "
                      "city/state/zip (e.g., '123 Main St, Los Angeles, CA 90001').")
    return {"address1": address1, "address2": address2}, ""


# ============================================================================
# Census Bureau Tools (Free - requires CENSUS_API_KEY)
# ============================================================================

@mcp.tool()
def get_census_demographics(state_fips: str, county_fips: str = "", tract: str = "", year: int = 0) -> str:
    """
    Get demographic data from Census Bureau's ACS 5-year survey.

    Args:
        state_fips: Two-digit state FIPS code (e.g., "06" for California)
        county_fips: Three-digit county FIPS code (optional, e.g., "037" for Los Angeles)
        tract: Six-digit census tract code (optional; requires county_fips)
        year: ACS vintage year (optional, e.g., 2023). Defaults to the latest
            likely vintage (current year minus 2), falling back one more year
            if that vintage is not yet published.

    Returns:
        JSON string with population, income, rent, and housing statistics,
        including the ACS vintage year used ("acs_vintage").
        Successful responses are cached on disk for 7 days.
    """
    validation_error = _validate_geography(state_fips, county_fips, tract)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("CENSUS_API_KEY", "")
    if not api_key:
        return _missing_key("CENSUS_API_KEY", "Get a free API key at https://api.census.gov/data/key_signup.html.")

    # Define variables to fetch
    variables = [
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25064_001E",  # Median gross rent
        "B25001_001E",  # Total housing units
        "B25002_002E",  # Occupied housing units
        "B25002_003E",  # Vacant housing units
        "B25003_002E",  # Owner-occupied units
        "B25003_003E"   # Renter-occupied units
    ]

    # Build geography parameter
    if tract:
        geography = f"for=tract:{tract}&in=state:{state_fips}+county:{county_fips}"
    elif county_fips:
        geography = f"for=county:{county_fips}&in=state:{state_fips}"
    else:
        geography = f"for=state:{state_fips}"

    try:
        data, vintage = _fetch_acs(variables, geography, api_key, year)

        if len(data) < 2:
            return json.dumps({"error": "No data returned from Census API"})

        # Parse response (first row is headers, second row is data)
        values = data[1]

        # Create result dictionary
        result = {
            "acs_vintage": vintage,
            "total_population": _acs_int(values[0]),
            "median_household_income": _acs_int(values[1]),
            "median_gross_rent": _acs_int(values[2]),
            "total_housing_units": _acs_int(values[3]),
            "occupied_units": _acs_int(values[4]),
            "vacant_units": _acs_int(values[5]),
            "owner_occupied_units": _acs_int(values[6]),
            "renter_occupied_units": _acs_int(values[7]),
            "state_fips": state_fips,
            "county_fips": county_fips if county_fips else None,
            "tract": tract if tract else None
        }

        # Calculate additional metrics
        if result["occupied_units"] and result["occupied_units"] > 0:
            if result["owner_occupied_units"]:
                result["owner_occupied_pct"] = round(result["owner_occupied_units"] / result["occupied_units"] * 100, 2)
            if result["renter_occupied_units"]:
                result["renter_occupied_pct"] = round(result["renter_occupied_units"] / result["occupied_units"] * 100, 2)

        if result["total_housing_units"] and result["total_housing_units"] > 0 and result["vacant_units"]:
            result["vacancy_rate"] = round(result["vacant_units"] / result["total_housing_units"] * 100, 2)

        return json.dumps(result, indent=2)

    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"Census API HTTP error: {e.code} - {e.reason}"})
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Census API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Census API error: {str(e)}"})


@mcp.tool()
def get_census_housing_stats(state_fips: str, county_fips: str = "", year: int = 0) -> str:
    """
    Get housing statistics from Census Bureau including median home value and year built data.

    Args:
        state_fips: Two-digit state FIPS code (e.g., "06" for California)
        county_fips: Three-digit county FIPS code (optional, e.g., "037" for Los Angeles)
        year: ACS vintage year (optional, e.g., 2023). Defaults to the latest
            likely vintage (current year minus 2), falling back one more year
            if that vintage is not yet published.

    Returns:
        JSON string with median home value and the count of housing units by
        year built, including the ACS vintage year used ("acs_vintage"). From
        the 2021 vintage on, the newest bins are "2020_or_later" and
        "2010_to_2019"; earlier vintages use "2014_or_later" and "2010_to_2013".
        Successful responses are cached on disk for 7 days.
    """
    validation_error = _validate_geography(state_fips, county_fips)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("CENSUS_API_KEY", "")
    if not api_key:
        return _missing_key("CENSUS_API_KEY", "Get a free API key at https://api.census.gov/data/key_signup.html.")

    # Define variables to fetch
    variables = [
        "B25077_001E",  # Median home value
        "B25034_001E",  # Total housing units (for year built)
        "B25034_002E",  # Built 2020 or later (2014 or later before the 2021 vintage)
        "B25034_003E",  # Built 2010-2019 (2010-2013 before the 2021 vintage)
        "B25034_004E",  # Built 2000-2009
        "B25034_005E",  # Built 1990-1999
        "B25034_006E",  # Built 1980-1989
        "B25034_007E",  # Built 1970-1979
        "B25034_008E",  # Built 1960-1969
        "B25034_009E",  # Built 1950-1959
        "B25034_010E",  # Built 1940-1949
        "B25034_011E"   # Built 1939 or earlier
    ]

    # Build geography parameter
    if county_fips:
        geography = f"for=county:{county_fips}&in=state:{state_fips}"
    else:
        geography = f"for=state:{state_fips}"

    try:
        data, vintage = _fetch_acs(variables, geography, api_key, year)

        if len(data) < 2:
            return json.dumps({"error": "No data returned from Census API"})

        # Parse response
        values = data[1]

        # The ACS changed the two newest year-built bins with the 2021 vintage.
        newest, recent = (("2020_or_later", "2010_to_2019") if vintage >= 2021
                          else ("2014_or_later", "2010_to_2013"))

        # Create result dictionary
        result = {
            "acs_vintage": vintage,
            "median_home_value": _acs_int(values[0]),
            "state_fips": state_fips,
            "county_fips": county_fips if county_fips else None,
            "year_built_distribution": {
                "total_units": _acs_int(values[1]),
                newest: _acs_int(values[2]),
                recent: _acs_int(values[3]),
                "2000_to_2009": _acs_int(values[4]),
                "1990_to_1999": _acs_int(values[5]),
                "1980_to_1989": _acs_int(values[6]),
                "1970_to_1979": _acs_int(values[7]),
                "1960_to_1969": _acs_int(values[8]),
                "1950_to_1959": _acs_int(values[9]),
                "1940_to_1949": _acs_int(values[10]),
                "1939_or_earlier": _acs_int(values[11])
            }
        }

        return json.dumps(result, indent=2)

    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"Census API HTTP error: {e.code} - {e.reason}"})
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Census API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Census API error: {str(e)}"})


# ============================================================================
# Redfin Data Center Tools (Free - no auth required)
# ============================================================================

REDFIN_BASE_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_data_center/housing_market/monthly/"

# Redfin Data Center "Housing Market Data" downloads (plain CSV, refreshed
# monthly). These replaced the old redfin_market_tracker/*.tsv000.gz files,
# which stopped updating in June 2026. Redfin calls cities "City" in the data;
# the tool keeps the region_type name "place" for backward compatibility.
REDFIN_SNAPSHOT_FILES = {
    "national": "country.csv",       # ~55 KB
    "state": "all_states.csv",       # ~3 MB
    "metro": "all_metros.csv",       # ~46 MB
    "county": "all_counties.csv",    # ~150 MB
    "place": "all_cities.csv",       # ~1.1 GB
    "zip": "all_zips.csv",           # ~1.3 GB
}

REDFIN_REGION_EXAMPLES = {
    "national": "National",
    "state": "Texas",
    "metro": "Austin, TX metro area",
    "county": "Travis County, TX",
    "place": "Denver, CO",
    "zip": "78704",
}

# Output field -> CSV column header (headers are matched case-insensitively).
_REDFIN_COLUMNS = {
    "median_sale_price": "MEDIAN SALE PRICE NSA ($)",
    "median_sale_price_yoy_pct": "MEDIAN SALE PRICE NSA YOY (%)",
    "median_sale_price_per_sqft": "MEDIAN SALE PRICE PER SQ.FT. ($)",
    "homes_sold": "HOMES SOLD",
    "new_listings": "NEW LISTINGS",
    "inventory": "INVENTORY",
    "months_of_supply": "MONTHS OF SUPPLY",
    "median_days_on_market": "MEDIAN DAYS ON MARKET (DAYS)",
    "avg_sale_to_list_pct": "AVERAGE SALE TO LIST RATIO (%)",
}


def _redfin_num(raw: str):
    """Parse a Redfin numeric field; empty/NA becomes None, whole floats become int."""
    raw = (raw or "").strip().strip('"')
    if not raw or raw.upper() == "NA":
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return int(value) if value.is_integer() else round(value, 2)


def _redfin_region_match(region_lc: str, needle: str, region_type: str) -> bool:
    if region_type == "national":
        return True  # the country file has a single region, "National"
    if region_type == "zip":
        return re.sub(r"\D", "", region_lc) == needle
    return needle in region_lc


def _scan_redfin_file(region_type: str, needles: list):
    """Stream one Redfin housing-market CSV from S3 and keep rows for the needles.

    The file is read row by row (never loaded whole). Returns (matches, samples):
    matches maps needle -> {region_name -> {frequency -> {period_begin: row}}};
    samples is a list of example region names seen in the file, for
    helpful no-match errors.
    """
    import csv
    url = REDFIN_BASE_URL + REDFIN_SNAPSHOT_FILES[region_type]
    matches = {n: {} for n in needles}
    samples, seen_samples = [], set()

    req = urllib.request.Request(url, headers={"User-Agent": "real-estate-data-mcp (zAI-Skills plugin)"})
    with urllib.request.urlopen(req, timeout=180) as response:
        text = io.TextIOWrapper(response, encoding="utf-8", errors="replace", newline="")
        reader = csv.reader(text)
        header = next(reader)
        col = {name.strip().upper(): i for i, name in enumerate(header)}
        required = ["FREQUENCY", "PERIOD BEGIN", "PERIOD END", "REGION NAME"] + list(_REDFIN_COLUMNS.values())
        missing = [c for c in required if c not in col]
        if missing:
            raise ValueError(f"Redfin file is missing expected columns: {missing}")
        region_i, freq_i = col["REGION NAME"], col["FREQUENCY"]
        max_i = max(col[c] for c in required)

        for fields in reader:
            if len(fields) <= max_i:
                continue
            region_raw = fields[region_i].strip()
            region_lc = region_raw.lower()
            if len(seen_samples) < 15 and region_lc not in seen_samples:
                seen_samples.add(region_lc)
                samples.append(region_raw)
            for needle in needles:
                if not _redfin_region_match(region_lc, needle, region_type):
                    continue
                row = {
                    "period_begin": fields[col["PERIOD BEGIN"]].strip(),
                    "period_end": fields[col["PERIOD END"]].strip(),
                }
                for out_name, header_name in _REDFIN_COLUMNS.items():
                    row[out_name] = _redfin_num(fields[col[header_name]])
                freq = fields[freq_i].strip()
                matches[needle].setdefault(region_raw, {}).setdefault(freq, {})[row["period_begin"]] = row
    return matches, samples


def _redfin_series(by_freq: dict):
    """Prefer monthly rows; fall back to rolling 3-month rows (city and ZIP files)."""
    for freq in ("Monthly", "Rolling 3 Months"):
        if by_freq.get(freq):
            rows = sorted(by_freq[freq].values(), key=lambda r: r["period_begin"], reverse=True)
            return freq, rows
    freq, rows_by_begin = next(iter(by_freq.items()))
    return freq, sorted(rows_by_begin.values(), key=lambda r: r["period_begin"], reverse=True)


def _redfin_snapshot_result(region: str, region_type: str, frequency: str, rows: list,
                            months: int, from_cache: bool) -> dict:
    return {
        "data_source": "Redfin Data Center housing market data (all residential, not seasonally adjusted)",
        "region": region,
        "region_type": region_type,
        "period_type": frequency,
        "latest_period_end": rows[0]["period_end"] if rows else None,
        "periods_returned": min(months, len(rows)),
        "served_from_cache": from_cache,
        "periods": rows[:months],  # newest first
    }


def _redfin_resolve(needle: str, region_name: str, region_type: str, found: dict, samples: list):
    """Pick one region for a needle, or explain why not."""
    if not found:
        return None, {
            "region_name": region_name,
            "error": f"No {region_type} rows matched '{region_name}'.",
            "hint": ("Matching is a case-insensitive substring for named regions and an exact "
                     "5-digit match for ZIPs; metros use Redfin's names like 'Austin, TX metro area'."),
            "region_name_examples": REDFIN_REGION_EXAMPLES,
            "sample_regions_in_file": samples,
        }
    if len(found) > 1:
        exact = [name for name in found if name.strip().lower() == needle]
        if len(exact) != 1:
            return None, {
                "region_name": region_name,
                "error": f"'{region_name}' matched {len(found)} regions; pass one of the exact names below.",
                "matching_regions": sorted(found.keys())[:25],
            }
        return exact[0], None
    return next(iter(found)), None


@mcp.tool()
def get_redfin_market_snapshot(region_name: str, region_type: str = "metro", months: int = 24) -> str:
    """
    Housing-market time series for one or more regions from Redfin Data
    Center's free public data. No API key required.

    Each period has: median sale price (and its year-over-year %), median sale
    price per sq ft, homes sold, new listings, inventory, months of supply,
    median days on market, and average sale-to-list ratio, all residential
    property types combined, not seasonally adjusted, newest first. Metro,
    county, state and national data are monthly; city ("place") and ZIP data
    are mostly rolling 3-month periods (the response says which). Redfin
    publishes about six weeks after month end. No rent data: use the Rentcast
    tools or Census for rents.

    To compare markets, pass several regions separated by " | " in one call
    (e.g. "Austin, TX metro area | Nashville, TN metro area"): the file is read
    once for all of them. The first uncached call downloads the file for that
    level (metro ~46 MB, county ~150 MB, place ~1.1 GB, zip ~1.3 GB), which can
    take minutes for place and zip; results are cached for 24 hours.

    Args:
        region_name: Region(s) to look up, separated by " | ". Formats:
            metro: "Austin, TX metro area" (a substring like "austin, tx" works if unique)
            county: "Travis County, TX"
            place: "Denver, CO"
            zip: "78704"
            state: "Texas"
            national: any name (the file has one region, "National")
        region_type: "metro" (default), "county", "place", "zip", "state", or "national".
        months: Number of most recent periods per region (default 24, max 240).

    Returns:
        JSON with one result per region (or a single result object when one
        region was asked for), each listing periods newest first, or an error
        with valid examples when a region doesn't match
    """
    region_type = region_type.strip().lower()
    if region_type not in REDFIN_SNAPSHOT_FILES:
        return json.dumps({
            "error": f"Invalid region_type: '{region_type}'.",
            "valid_region_types": sorted(REDFIN_SNAPSHOT_FILES.keys()),
            "region_name_examples": REDFIN_REGION_EXAMPLES
        })
    if months < 1:
        return json.dumps({"error": "months must be a positive integer."})
    months = min(months, 240)

    requested = [r.strip() for r in region_name.split("|") if r.strip()]
    if not requested:
        return json.dumps({"error": "region_name must not be empty.", "region_name_examples": REDFIN_REGION_EXAMPLES})
    needles = {}
    for name in requested:
        if region_type == "zip":
            digits = re.sub(r"\D", "", name)
            if len(digits) != 5:
                return json.dumps({"error": f"For region_type 'zip', each region must be a 5-digit ZIP code (got '{name}')."})
            needles[name] = digits
        else:
            needles[name] = name.lower()

    results, to_scan = {}, []
    for name, needle in needles.items():
        cached = _cache_get("redfin-v2", f"{region_type}|{needle}", CACHE_TTL_REDFIN)
        if cached is not None:
            results[name] = _redfin_snapshot_result(cached["region"], region_type, cached["frequency"],
                                                    cached["rows"], months, from_cache=True)
        else:
            to_scan.append(name)

    if to_scan:
        try:
            matches, samples = _scan_redfin_file(region_type, sorted({needles[n] for n in to_scan}))
        except urllib.error.HTTPError as e:
            return json.dumps({"error": f"Redfin data download HTTP error: {e.code} - {e.reason}"})
        except urllib.error.URLError as e:
            return json.dumps({"error": f"Redfin data download connection error: {str(e)}"})
        except (OSError, ValueError) as e:
            return json.dumps({"error": f"Redfin data processing error: {str(e)}"})
        for name in to_scan:
            needle = needles[name]
            resolved, err = _redfin_resolve(needle, name, region_type, matches.get(needle, {}), samples)
            if err:
                results[name] = err
                continue
            frequency, rows = _redfin_series(matches[needle][resolved])
            _cache_put("redfin-v2", f"{region_type}|{needle}", {"region": resolved, "frequency": frequency, "rows": rows})
            results[name] = _redfin_snapshot_result(resolved, region_type, frequency, rows, months, from_cache=False)

    if len(requested) == 1:
        return json.dumps(results[requested[0]], indent=2)
    return json.dumps({"results": [results[n] for n in requested]}, indent=2)


@mcp.tool()
def get_redfin_market_data(region_type: str = "metro") -> str:
    """
    Download link and column guide for a whole Redfin Data Center housing-market
    file, for analysis across many regions at once (e.g. ranking all metros).
    For one or a few regions, use get_redfin_market_snapshot instead: it
    downloads, filters and parses the file for you.

    Args:
        region_type: "national", "state", "metro" (default), "county", "place", or "zip".

    Returns:
        JSON with the download URL, approximate size, format notes and the
        column names as they appear in the file
    """
    region_type = region_type.strip().lower()
    if region_type == "city":
        region_type = "place"
    if region_type not in REDFIN_SNAPSHOT_FILES:
        return json.dumps({"error": f"Invalid region_type: '{region_type}'.",
                           "valid_region_types": sorted(REDFIN_SNAPSHOT_FILES.keys())})
    sizes = {"national": "~55 KB", "state": "~3 MB", "metro": "~46 MB", "county": "~150 MB",
             "place": "~1.1 GB", "zip": "~1.3 GB"}
    url = REDFIN_BASE_URL + REDFIN_SNAPSHOT_FILES[region_type]
    return json.dumps({
        "data_source": "Redfin Data Center housing market data",
        "region_type": region_type,
        "download_url": url,
        "format": "CSV with a header row; text fields quoted; missing values are NA",
        "approximate_size": sizes[region_type],
        "update_frequency": "Monthly (about six weeks after month end)",
        "rows": ("One row per region per period. FREQUENCY is 'Monthly' or 'Rolling 3 Months' "
                 "(city and ZIP files are mostly rolling 3-month). All residential property "
                 "types combined, not seasonally adjusted."),
        "key_columns": {
            "REGION NAME": "Region, e.g. 'Austin, TX metro area', 'Travis County, TX', '78704'",
            "FREQUENCY": "Monthly or Rolling 3 Months",
            "PERIOD BEGIN / PERIOD END": "Period dates (YYYY-MM-DD)",
            "MEDIAN SALE PRICE NSA ($)": "Median sale price",
            "MEDIAN SALE PRICE NSA YOY (%)": "Year-over-year change in median sale price",
            "MEDIAN SALE PRICE PER SQ.FT. ($)": "Median sale price per square foot",
            "HOMES SOLD": "Homes sold in the period",
            "NEW LISTINGS / ACTIVE LISTINGS / INVENTORY": "Supply measures",
            "MONTHS OF SUPPLY": "Months to sell current inventory at the current pace",
            "MEDIAN DAYS ON MARKET (DAYS)": "Median days on market",
            "AVERAGE SALE TO LIST RATIO (%)": "Average sale price as % of list price",
        },
        "see_also": "get_redfin_market_snapshot (one or a few regions, parsed for you)",
        "tip": ("Filter by REGION NAME and FREQUENCY, sort by PERIOD END descending. With pandas: "
                "pd.read_csv(url, na_values='NA')."),
    }, indent=2)


# ============================================================================
# FRED Tools (Free - requires FRED_API_KEY)
# ============================================================================

@mcp.tool()
def get_fred_series(series_id: str, observations: int = 24) -> str:
    """
    Get recent observations for a FRED (Federal Reserve Economic Data) series -
    macro context for real estate underwriting.

    Most useful series for real estate analysis:
        MORTGAGE30US - 30-year fixed-rate mortgage average, % (weekly)
        DGS10        - 10-year Treasury constant-maturity yield, % (daily)
        RRVRUSQ156N  - US rental vacancy rate, % (quarterly)

    Requires FRED_API_KEY (free). Responses are cached on disk for 24 hours.

    Args:
        series_id: FRED series ID (e.g., "MORTGAGE30US")
        observations: Number of most recent observations to return (default 24)

    Returns:
        JSON string with the observations, newest first (missing values are null)
    """
    series_id = series_id.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_.\-]{1,64}", series_id):
        return json.dumps({
            "error": ("Invalid series_id: use a FRED series ID such as "
                      "'MORTGAGE30US', 'DGS10', or 'RRVRUSQ156N'.")
        })
    if observations < 1:
        return json.dumps({"error": "observations must be a positive integer."})
    observations = min(observations, 1000)

    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        return _missing_key("FRED_API_KEY", "Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html.")

    cache_key = f"{series_id}|{observations}"
    cached = _cache_get("fred", cache_key, CACHE_TTL_MARKET)
    if cached is not None:
        cached_out = dict(cached)
        cached_out["served_from_cache"] = True
        return json.dumps(cached_out, indent=2)

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": observations
    }
    url = f"https://api.stlouisfed.org/fred/series/observations?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        obs = []
        for o in data.get("observations", []):
            raw = o.get("value", ".")
            try:
                value = float(raw)
            except (TypeError, ValueError):
                value = None  # FRED encodes missing values as "."
            obs.append({"date": o.get("date"), "value": value})

        result = {
            "data_source": "FRED (Federal Reserve Bank of St. Louis)",
            "series_id": series_id,
            "observations_returned": len(obs),
            "observations": obs  # newest first
        }
        _cache_put("fred", cache_key, result)
        return json.dumps(result, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"FRED API HTTP error: {e.code} - {e.reason}",
            "details": error_body,
            "hint": "HTTP 400 usually means an unknown series_id or an invalid FRED_API_KEY."
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"FRED API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"FRED API error: {str(e)}"})


# ============================================================================
# Rentcast Tools (Free tier: 50 requests/month - requires RENTCAST_API_KEY)
# ============================================================================

def _rentcast_call(api_key: str, cache_key: str, url: str) -> str:
    """Shared Rentcast fetch: 24h disk cache plus the monthly quota counter.

    Cache hits do not increment the counter (they cost no quota). Live calls
    increment it before the request is issued, so failed requests - which may
    still count against Rentcast's free tier - are tracked conservatively.
    Once the month's free calls are used, live calls stop unless the user set
    RENTCAST_ALLOW_OVERAGE=1, because Rentcast bills each request beyond the
    free allowance.
    """
    cached = _cache_get("rentcast", cache_key, CACHE_TTL_MARKET)
    if cached is not None:
        return json.dumps(
            _with_rentcast_quota(cached, _rentcast_usage(), from_cache=True),
            indent=2)

    used = _rentcast_usage()
    if used >= RENTCAST_FREE_TIER_LIMIT and os.environ.get("RENTCAST_ALLOW_OVERAGE", "") != "1":
        return json.dumps({
            "error": (f"Rentcast free-tier limit reached ({used}/{RENTCAST_FREE_TIER_LIMIT} "
                      "calls this month by this plugin's count). No request was sent, "
                      "because further calls may be billed."),
            "info": ("Use Census median gross rent or comparable listings instead, or, if the "
                     "user accepts Rentcast's per-request charges, they can set "
                     "RENTCAST_ALLOW_OVERAGE=1 and restart Claude Code."),
        }, indent=2)

    req = urllib.request.Request(url)
    req.add_header("X-Api-Key", api_key)
    req.add_header("Accept", "application/json")

    count = _rentcast_usage(increment=True)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        _cache_put("rentcast", cache_key, data)
        return json.dumps(_with_rentcast_quota(data, count), indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps(_with_rentcast_quota({
            "error": f"Rentcast API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        }, count), indent=2)
    except urllib.error.URLError as e:
        return json.dumps(_with_rentcast_quota(
            {"error": f"Rentcast API connection error: {str(e)}"}, count), indent=2)
    except Exception as e:
        return json.dumps(_with_rentcast_quota(
            {"error": f"Rentcast API error: {str(e)}"}, count), indent=2)


@mcp.tool()
def estimate_rent(address: str) -> str:
    """
    Long-term rent estimate for one property from Rentcast's rent AVM.

    Responses are cached on disk for 24 hours (cache hits cost no quota).
    Every response includes a "rentcast_quota" note tracking free-tier usage
    ("N/50 free-tier calls used this month"), a warning as the limit nears,
    and a refusal at the limit unless RENTCAST_ALLOW_OVERAGE=1.

    Args:
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON with the estimated monthly rent, a low-high range
        (rentRangeLow/rentRangeHigh), and the comparable rental listings used
        (address, rent, distance, correlation). Rentcast gives no separate
        confidence score; a wide range means a less certain estimate.
    """
    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        return _missing_key("RENTCAST_API_KEY", "Sign up for a free API key at https://app.rentcast.io/app/api.")

    base_url = "https://api.rentcast.io/v1/avm/rent/long-term"
    url = f"{base_url}?{urllib.parse.urlencode({'address': address})}"
    return _rentcast_call(api_key, f"avm-rent|{address.strip().lower()}", url)


@mcp.tool()
def get_rentcast_market_data(zip_code: str) -> str:
    """
    Get rental market statistics for a ZIP code from Rentcast.

    Responses are cached on disk for 24 hours (cache hits cost no quota).
    Every response includes a "rentcast_quota" note tracking free-tier usage
    ("N/50 free-tier calls used this month"), a warning as the limit nears,
    and a refusal at the limit unless RENTCAST_ALLOW_OVERAGE=1.

    Args:
        zip_code: Five-digit ZIP code (e.g., "90001")

    Returns:
        JSON with Rentcast's listing statistics for the ZIP: saleData and
        rentalData, each with averages, medians, ranges, per-sq-ft figures,
        days on market and listing counts, broken down by property type and
        bedrooms, plus monthly history. These come from listings, so there is
        no vacancy rate (use Census for vacancy).
    """
    validation_error = _validate_zip(zip_code)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        return _missing_key("RENTCAST_API_KEY", "Sign up for a free API key at https://app.rentcast.io/app/api.")

    base_url = "https://api.rentcast.io/v1/markets"
    url = f"{base_url}?{urllib.parse.urlencode({'zipCode': zip_code})}"
    return _rentcast_call(api_key, f"markets|{zip_code}", url)


# ============================================================================
# Paid providers: Mashvisor, AirDNA, ATTOM
#
# These calls follow each provider's published API docs but have not been run
# against a live key by this plugin's maintainers, so each response carries an
# "unverified_integration" note. If a call fails, the HTTP error body is
# returned as-is so the cause is visible.
# ============================================================================

_UNVERIFIED_NOTE = ("This integration follows the provider's published docs but hasn't been tested "
                    "with a live key; check field names in the raw response before relying on them.")


def _paid_request(provider: str, url: str, headers: dict, payload=None):
    """Send one JSON request. Returns (data, None) or (None, error_dict)."""
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for name, value in headers.items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode()), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace") if e.fp else ""
        return None, {"error": f"{provider} API HTTP error: {e.code} - {e.reason}",
                      "details": error_body[:2000]}
    except urllib.error.URLError as e:
        return None, {"error": f"{provider} API connection error: {str(e)}"}
    except ValueError as e:
        return None, {"error": f"{provider} API returned non-JSON content: {str(e)}"}


def _find_records(data, keys=("id",)):
    """Return the first list of dicts (searching nested dicts) whose items have all keys."""
    if isinstance(data, list):
        if data and all(isinstance(x, dict) and all(k in x for k in keys) for x in data):
            return data
        for item in data:
            found = _find_records(item, keys)
            if found:
                return found
    elif isinstance(data, dict):
        for value in data.values():
            found = _find_records(value, keys)
            if found:
                return found
    return []


@mcp.tool()
def get_mashvisor_property(address: str, state: str, city: str, zip_code: str) -> str:
    """
    Property record from Mashvisor (paid; needs MASHVISOR_API_KEY).

    Returns Mashvisor's property details as the API sends them (listing and
    building facts). Mashvisor serves rental income estimates from a separate
    endpoint this tool doesn't call, so don't expect STR/LTR estimates here.

    Args:
        address: Street address (e.g., "123 Main St")
        state: Two-letter state code (e.g., "CA")
        city: City name (e.g., "Los Angeles")
        zip_code: Five-digit ZIP code (e.g., "90001")

    Returns:
        JSON with Mashvisor's raw property response, or an error
    """
    validation_error = _validate_zip(zip_code)
    if validation_error:
        return json.dumps({"error": validation_error})
    api_key = os.environ.get("MASHVISOR_API_KEY", "")
    if not api_key:
        return _missing_key("MASHVISOR_API_KEY", "Mashvisor API access: https://www.mashvisor.com/data-api.")

    params = {"address": address, "state": state, "city": city, "zip_code": zip_code}
    url = f"https://api.mashvisor.com/v1.1/client/property?{urllib.parse.urlencode(params)}"
    data, err = _paid_request("Mashvisor", url, {"x-api-key": api_key})
    if err:
        return json.dumps(err, indent=2)
    return json.dumps({"unverified_integration": _UNVERIFIED_NOTE, "data": data}, indent=2)


@mcp.tool()
def get_mashvisor_neighborhood(city: str, state: str, neighborhood: str = "", neighborhood_id: str = "") -> str:
    """
    Neighborhood investment overview from Mashvisor (paid; needs MASHVISOR_API_KEY).

    Mashvisor keys neighborhood data by ID. With neighborhood_id, this returns
    that neighborhood's overview. Otherwise it lists the city's neighborhoods
    (with IDs); if `neighborhood` names exactly one of them, it fetches that
    overview too. The overview's fields (rental yields, occupancy, prices) are
    passed through as Mashvisor returns them.

    Args:
        city: City name (e.g., "Los Angeles")
        state: Two-letter state code (e.g., "CA")
        neighborhood: Neighborhood name to look up (optional, e.g., "Silver Lake")
        neighborhood_id: Mashvisor neighborhood ID, if already known (optional)

    Returns:
        JSON with the overview, or the list of neighborhoods to choose from
    """
    api_key = os.environ.get("MASHVISOR_API_KEY", "")
    if not api_key:
        return _missing_key("MASHVISOR_API_KEY", "Mashvisor API access: https://www.mashvisor.com/data-api.")
    headers = {"x-api-key": api_key}
    state = state.strip().upper()

    if not neighborhood_id:
        list_url = ("https://api.mashvisor.com/v1.1/client/city/neighborhoods/"
                    f"{urllib.parse.quote(state)}/{urllib.parse.quote(city.strip())}")
        data, err = _paid_request("Mashvisor", list_url, headers)
        if err:
            return json.dumps(err, indent=2)
        hoods = _find_records(data, ("id", "name"))
        if neighborhood:
            wanted = neighborhood.strip().lower()
            hits = [h for h in hoods if wanted in str(h.get("name", "")).lower()]
            exact = [h for h in hits if str(h.get("name", "")).lower() == wanted]
            hits = exact or hits
            if len(hits) == 1:
                neighborhood_id = str(hits[0]["id"])
        if not neighborhood_id:
            return json.dumps({
                "unverified_integration": _UNVERIFIED_NOTE,
                "note": ("Pass one of these IDs as neighborhood_id (or a unique name as neighborhood) "
                         "to get its overview."),
                "neighborhoods": [{"id": h.get("id"), "name": h.get("name")} for h in hoods][:200],
                "raw": data if not hoods else None,
            }, indent=2)

    bar_url = (f"https://api.mashvisor.com/v1.1/client/neighborhood/{urllib.parse.quote(str(neighborhood_id))}"
               f"/bar?{urllib.parse.urlencode({'state': state})}")
    data, err = _paid_request("Mashvisor", bar_url, headers)
    if err:
        return json.dumps(err, indent=2)
    return json.dumps({"unverified_integration": _UNVERIFIED_NOTE,
                       "neighborhood_id": neighborhood_id, "data": data}, indent=2)


AIRDNA_BASE_URL = "https://api.airdna.co/api/enterprise/v2"
AIRDNA_SIGNUP = "AirDNA Enterprise API tokens are issued by AirDNA's sales team (airdna.co), not self-serve."


@mcp.tool()
def get_airdna_rentalizer(address: str, bedrooms: int, bathrooms: float) -> str:
    """
    Short-term rental revenue estimate for one property from AirDNA's
    Rentalizer (paid Enterprise API; needs AIRDNA_API_KEY).

    The request path and body follow AirDNA's Enterprise v2 docs as far as
    they could be read; it's unverified. The response is passed through as
    AirDNA returns it (typically projected revenue, ADR and occupancy).

    Args:
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")
        bedrooms: Number of bedrooms (e.g., 3)
        bathrooms: Number of bathrooms (e.g., 2 or 2.5)

    Returns:
        JSON with AirDNA's raw estimate response, or an error
    """
    api_key = os.environ.get("AIRDNA_API_KEY", "")
    if not api_key:
        return _missing_key("AIRDNA_API_KEY", AIRDNA_SIGNUP)
    data, err = _paid_request(
        "AirDNA", f"{AIRDNA_BASE_URL}/rentalizer/estimate", {"Authorization": f"Bearer {api_key}"},
        {"address": address, "bedrooms": bedrooms, "bathrooms": bathrooms})
    if err:
        return json.dumps(err, indent=2)
    return json.dumps({"unverified_integration": _UNVERIFIED_NOTE, "data": data}, indent=2)


AIRDNA_MARKET_METRICS = ("occupancy", "adr", "avg_revenue")


@mcp.tool()
def get_airdna_market_stats(city: str, state: str) -> str:
    """
    Market-level short-term rental metrics from AirDNA (paid Enterprise API;
    needs AIRDNA_API_KEY).

    Two steps: searches AirDNA markets for "<city>, <state>", then requests
    occupancy, average daily rate (ADR) and average revenue for the best
    match. Metric responses are passed through as AirDNA returns them.

    Args:
        city: City name (e.g., "Austin")
        state: Two-letter state code (e.g., "TX")

    Returns:
        JSON with the matched market, the other candidates, and each metric's
        raw response (or that metric's error)
    """
    api_key = os.environ.get("AIRDNA_API_KEY", "")
    if not api_key:
        return _missing_key("AIRDNA_API_KEY", AIRDNA_SIGNUP)
    headers = {"Authorization": f"Bearer {api_key}"}

    search_term = f"{city.strip()}, {state.strip().upper()}"
    found, err = _paid_request("AirDNA", f"{AIRDNA_BASE_URL}/market/search", headers,
                               {"search_term": search_term})
    if err:
        return json.dumps(err, indent=2)
    markets = _find_records(found, ("id",))
    if not markets:
        return json.dumps({"error": f"AirDNA returned no market for '{search_term}'.",
                           "unverified_integration": _UNVERIFIED_NOTE, "raw": found}, indent=2)

    market = markets[0]
    market_id = urllib.parse.quote(str(market["id"]))
    metrics = {}
    for metric in AIRDNA_MARKET_METRICS:
        data, err = _paid_request("AirDNA", f"{AIRDNA_BASE_URL}/market/{market_id}/metrics/{metric}",
                                  headers, {})
        metrics[metric] = err or data
    return json.dumps({
        "unverified_integration": _UNVERIFIED_NOTE,
        "market": market,
        "other_candidates": [{"id": m.get("id"), "name": m.get("name")} for m in markets[1:6]],
        "metrics": metrics,
    }, indent=2)


ATTOM_BASE_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
ATTOM_SIGNUP = "ATTOM API keys: https://api.developer.attomdata.com/."


@mcp.tool()
def get_attom_property(address: str) -> str:
    """
    Property record from ATTOM (paid; needs ATTOM_API_KEY): lot and building
    size, year built, bedrooms and bathrooms, property type, and similar
    facts, passed through as ATTOM returns them.

    Args:
        address: Full property address with a comma between the street and the
            city/state/zip (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON with ATTOM's raw property detail response, or an error
    """
    params, address_error = _attom_address_params(address)
    if address_error:
        return json.dumps({"error": address_error})
    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return _missing_key("ATTOM_API_KEY", ATTOM_SIGNUP)
    data, err = _paid_request("ATTOM", f"{ATTOM_BASE_URL}/property/detail?{urllib.parse.urlencode(params)}",
                              {"apikey": api_key})
    if err:
        return json.dumps(err, indent=2)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_attom_valuation(address: str) -> str:
    """
    Automated valuation (AVM) from ATTOM (paid; needs ATTOM_API_KEY): the
    estimated value with a high-low range and ATTOM's confidence score
    ("scr"). It doesn't include comparable sales.

    Args:
        address: Full property address with a comma between the street and the
            city/state/zip (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON with ATTOM's raw AVM response, or an error
    """
    params, address_error = _attom_address_params(address)
    if address_error:
        return json.dumps({"error": address_error})
    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return _missing_key("ATTOM_API_KEY", ATTOM_SIGNUP)
    data, err = _paid_request("ATTOM", f"{ATTOM_BASE_URL}/attomavm/detail?{urllib.parse.urlencode(params)}",
                              {"apikey": api_key})
    if err:
        return json.dumps(err, indent=2)
    return json.dumps({"unverified_integration": _UNVERIFIED_NOTE, "data": data}, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
