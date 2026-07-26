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
import gzip
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
CACHE_TTL_REDFIN = 24 * 3600      # Filtered Redfin market-tracker slices: 24 hours


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
                f"{RENTCAST_FREE_TIER_LIMIT} calls/month. Further live calls may "
                "fail or incur charges; cached responses do not count against the quota."
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
        return json.dumps({
            "error": "CENSUS_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Get a free API key at https://api.census.gov/data/key_signup.html"
        })

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
            "total_population": int(values[0]) if values[0] and values[0] != "-666666666" else None,
            "median_household_income": int(values[1]) if values[1] and values[1] != "-666666666" else None,
            "median_gross_rent": int(values[2]) if values[2] and values[2] != "-666666666" else None,
            "total_housing_units": int(values[3]) if values[3] and values[3] != "-666666666" else None,
            "occupied_units": int(values[4]) if values[4] and values[4] != "-666666666" else None,
            "vacant_units": int(values[5]) if values[5] and values[5] != "-666666666" else None,
            "owner_occupied_units": int(values[6]) if values[6] and values[6] != "-666666666" else None,
            "renter_occupied_units": int(values[7]) if values[7] and values[7] != "-666666666" else None,
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
        JSON string with median home value and housing age distribution,
        including the ACS vintage year used ("acs_vintage").
        Successful responses are cached on disk for 7 days.
    """
    validation_error = _validate_geography(state_fips, county_fips)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("CENSUS_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "CENSUS_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Get a free API key at https://api.census.gov/data/key_signup.html"
        })

    # Define variables to fetch
    variables = [
        "B25077_001E",  # Median home value
        "B25034_001E",  # Total housing units (for year built)
        "B25034_002E",  # Built 2014 or later
        "B25034_003E",  # Built 2010-2013
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

        # Create result dictionary
        result = {
            "acs_vintage": vintage,
            "median_home_value": int(values[0]) if values[0] and values[0] != "-666666666" else None,
            "state_fips": state_fips,
            "county_fips": county_fips if county_fips else None,
            "year_built_distribution": {
                "total_units": int(values[1]) if values[1] and values[1] != "-666666666" else None,
                "2014_or_later": int(values[2]) if values[2] and values[2] != "-666666666" else None,
                "2010_to_2013": int(values[3]) if values[3] and values[3] != "-666666666" else None,
                "2000_to_2009": int(values[4]) if values[4] and values[4] != "-666666666" else None,
                "1990_to_1999": int(values[5]) if values[5] and values[5] != "-666666666" else None,
                "1980_to_1989": int(values[6]) if values[6] and values[6] != "-666666666" else None,
                "1970_to_1979": int(values[7]) if values[7] and values[7] != "-666666666" else None,
                "1960_to_1969": int(values[8]) if values[8] and values[8] != "-666666666" else None,
                "1950_to_1959": int(values[9]) if values[9] and values[9] != "-666666666" else None,
                "1940_to_1949": int(values[10]) if values[10] and values[10] != "-666666666" else None,
                "1939_or_earlier": int(values[11]) if values[11] and values[11] != "-666666666" else None
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

@mcp.tool()
def get_redfin_market_data(region_type: str = "metro") -> str:
    """
    Get information about Redfin market data files and how to access them.
    Note: These are large TSV files (hundreds of MB) - this tool provides URLs and guidance.

    Args:
        region_type: Geographic level of the data file. Must be one of
            "national", "metro", "city", "zip", or "neighborhood".
            Defaults to "metro".

    Returns:
        JSON string with download URLs, column descriptions, and usage guidance
    """
    base_url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/"

    files = {
        "national": "us_national_market_tracker.tsv000.gz",
        "metro": "redfin_metro_market_tracker.tsv000.gz",
        "city": "city_market_tracker.tsv000.gz",
        "zip": "zip_code_market_tracker.tsv000.gz",
        "neighborhood": "neighborhood_market_tracker.tsv000.gz"
    }

    if region_type not in files:
        return json.dumps({
            "error": f"Invalid region_type: '{region_type}'.",
            "valid_region_types": list(files.keys())
        })

    file_url = base_url + files[region_type]

    result = {
        "see_also": ("For a ready-parsed monthly time series for a single region "
                     "(no manual download), call the get_redfin_market_snapshot "
                     "tool instead."),
        "data_source": "Redfin Data Center",
        "region_type": region_type,
        "download_url": file_url,
        "format": "TSV (tab-separated values), gzip compressed",
        "file_size": "Large (typically 100+ MB compressed)",
        "update_frequency": "Monthly",
        "key_columns": {
            "period_begin": "Start date of the time period",
            "period_end": "End date of the time period",
            "region_type": "Geographic level (national, metro, city, zip, neighborhood)",
            "region_name": "Name of the geographic region",
            "median_sale_price": "Median sale price of homes",
            "median_sale_price_mom": "Month-over-month % change in median sale price",
            "median_sale_price_yoy": "Year-over-year % change in median sale price",
            "median_ppsf": "Median price per square foot",
            "homes_sold": "Total number of homes sold",
            "inventory": "Total number of homes for sale",
            "months_of_supply": "Number of months to sell current inventory at current pace",
            "median_dom": "Median days on market",
            "avg_sale_to_list": "Average sale price to list price ratio",
            "sold_above_list": "Percentage of homes that sold above list price",
            "off_market_in_two_weeks": "Percentage of homes that went off market within two weeks"
        },
        "usage_instructions": [
            "1. Download the file using wget, curl, or your preferred tool",
            "2. Decompress the .gz file",
            "3. Parse the TSV file (tab-separated)",
            "4. Filter by region and time period as needed",
            "5. For latest data, sort by period_end descending and take the most recent"
        ],
        "example_curl": f"curl -o redfin_data.tsv.gz {file_url}",
        "available_files": {
            "national": "National-level metrics",
            "metro": "Metro area metrics (400+ metros)",
            "city": "City-level metrics",
            "zip": "ZIP code-level metrics",
            "neighborhood": "Neighborhood-level metrics"
        },
        "note": "Due to file size, this tool provides guidance rather than downloading the data directly. Process locally for best results."
    }

    return json.dumps(result, indent=2)


REDFIN_BASE_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/"

# Files behind get_redfin_market_snapshot. Redfin's data calls cities "place",
# matching the region_type value used inside the files themselves.
REDFIN_SNAPSHOT_FILES = {
    "metro": "redfin_metro_market_tracker.tsv000.gz",
    "county": "county_market_tracker.tsv000.gz",
    "place": "city_market_tracker.tsv000.gz",
    "zip": "zip_code_market_tracker.tsv000.gz",
}

REDFIN_REGION_EXAMPLES = {
    "metro": "Los Angeles, CA metro area",
    "county": "Los Angeles County, CA",
    "place": "Denver, CO",
    "zip": "90210",
}

_REDFIN_METRIC_COLUMNS = ("median_sale_price", "homes_sold", "inventory",
                          "median_dom", "months_of_supply")


def _redfin_num(raw: str):
    """Parse a Redfin TSV numeric field; empty/NA becomes None, whole floats become int."""
    raw = raw.strip().strip('"')
    if not raw or raw.upper() == "NA":
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return int(value) if value.is_integer() else round(value, 2)


def _redfin_region_match(region_lc: str, needle: str, region_type: str) -> bool:
    if region_type == "zip":
        # Rows look like "Zip Code: 90210" - compare digits only.
        return re.sub(r"\D", "", region_lc) == needle
    return needle in region_lc


def _scan_redfin_file(region_type: str, needle: str):
    """Stream one Redfin market-tracker gzip TSV from S3 line by line.

    Never loads the whole file into memory: the HTTP body is decompressed
    incrementally and each line is filtered as it arrives. Keeps only
    "All Residential", non-seasonally-adjusted, monthly rows whose region
    matches needle.

    Returns (matches, samples): matches maps each matching region name to
    {period_begin: row_dict}; samples is a list of example region names seen
    in the file (for helpful no-match error messages).
    """
    url = REDFIN_BASE_URL + REDFIN_SNAPSHOT_FILES[region_type]
    matches = {}
    samples = []
    seen_samples = set()

    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=120) as response:
        gz = gzip.GzipFile(fileobj=response)
        text = io.TextIOWrapper(gz, encoding="utf-8", errors="replace", newline="")

        # Header names are quoted and UPPERCASE in the live files
        # (e.g. "PERIOD_BEGIN"); normalize to bare lowercase.
        header = text.readline().rstrip("\r\n").split("\t")
        col = {name.strip().strip('"').lower(): i for i, name in enumerate(header)}
        required = ["region", "period_begin", "period_end", "property_type"]
        required += list(_REDFIN_METRIC_COLUMNS)
        missing = [c for c in required if c not in col]
        if missing:
            raise ValueError(f"Redfin file is missing expected columns: {missing}")

        region_i = col["region"]
        ptype_i = col["property_type"]
        adj_i = col.get("is_seasonally_adjusted")
        dur_i = col.get("period_duration")
        max_i = max(col[c] for c in required)

        for line in text:
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) <= region_i:
                continue
            region_raw = fields[region_i].strip().strip('"')
            region_lc = region_raw.lower()
            if len(seen_samples) < 15 and region_lc not in seen_samples:
                seen_samples.add(region_lc)
                samples.append(region_raw)
            if not _redfin_region_match(region_lc, needle, region_type):
                continue
            if len(fields) <= max_i:
                continue
            if fields[ptype_i].strip().strip('"') != "All Residential":
                continue
            if adj_i is not None and len(fields) > adj_i and \
                    fields[adj_i].strip().strip('"').lower() in ("t", "true"):
                continue
            if dur_i is not None and len(fields) > dur_i and \
                    fields[dur_i].strip().strip('"') not in ("30", "30.0", ""):
                continue  # keep only monthly periods
            row = {
                "period_begin": fields[col["period_begin"]].strip().strip('"'),
                "period_end": fields[col["period_end"]].strip().strip('"'),
            }
            for metric in _REDFIN_METRIC_COLUMNS:
                row[metric] = _redfin_num(fields[col[metric]])
            matches.setdefault(region_raw, {})[row["period_begin"]] = row

    return matches, samples


def _redfin_snapshot_result(region: str, region_type: str, rows: list,
                            months: int, from_cache: bool) -> dict:
    return {
        "data_source": "Redfin Data Center market tracker (property type: All Residential)",
        "region": region,
        "region_type": region_type,
        "months_returned": min(months, len(rows)),
        "served_from_cache": from_cache,
        "monthly": rows[:months],  # newest first
    }


@mcp.tool()
def get_redfin_market_snapshot(region_name: str, region_type: str = "metro", months: int = 24) -> str:
    """
    Get a monthly housing-market time series for one region from Redfin Data
    Center's free public market-tracker data. No API key required - this is
    the plugin's zero-cost live market data path.

    Returns median sale price, homes sold, inventory, median days on market,
    and months of supply for each of the last `months` months (property type
    "All Residential", newest first).

    Cost note: the first uncached call streams Redfin's gzipped TSV from S3
    and can take minutes on slow connections. Approximate compressed sizes:
    metro ~110 MB, county ~240 MB, place ~1 GB, zip ~1.5 GB - prefer metro or
    county when either granularity works. The file is processed line by line
    (never fully loaded into memory), and the filtered slice is cached for
    24 hours under ~/.cache/real-estate-data/, so repeat calls for the same
    region are instant regardless of the `months` value.

    Args:
        region_name: Region to look up. Format by region_type:
            metro: "Los Angeles, CA metro area" (a case-insensitive substring
                like "los angeles" also works if it matches only one region)
            county: "Los Angeles County, CA"
            place: "Denver, CO" (cities/towns)
            zip: "90210" (5-digit ZIP code, exact match)
        region_type: One of "metro", "county", "place", "zip". Default "metro".
        months: Number of most recent months to return (default 24, max 240).

    Returns:
        JSON string with one entry per month (newest first), or an error that
        lists valid region examples when nothing matches
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

    if region_type == "zip":
        needle = re.sub(r"\D", "", region_name)
        if len(needle) != 5:
            return json.dumps({
                "error": "For region_type 'zip', region_name must be a 5-digit "
                         "ZIP code (e.g., '90210')."
            })
    else:
        needle = region_name.strip().lower()
        if not needle:
            return json.dumps({
                "error": "region_name must not be empty.",
                "region_name_examples": REDFIN_REGION_EXAMPLES
            })

    cache_key = f"{region_type}|{needle}"
    cached = _cache_get("redfin", cache_key, CACHE_TTL_REDFIN)
    if cached is not None:
        return json.dumps(
            _redfin_snapshot_result(cached["region"], region_type,
                                    cached["rows"], months, from_cache=True),
            indent=2)

    try:
        matches, samples = _scan_redfin_file(region_type, needle)
    except urllib.error.HTTPError as e:
        return json.dumps({"error": f"Redfin data download HTTP error: {e.code} - {e.reason}"})
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Redfin data download connection error: {str(e)}"})
    except (OSError, ValueError) as e:
        return json.dumps({"error": f"Redfin data processing error: {str(e)}"})

    if not matches:
        return json.dumps({
            "error": f"No {region_type} rows matched region_name '{region_name}'.",
            "hint": ("Check the spelling and format. Matching is a case-insensitive "
                     "substring for metro/county/place and an exact 5-digit match for zip."),
            "region_name_examples": REDFIN_REGION_EXAMPLES,
            "sample_regions_in_file": samples
        }, indent=2)

    if len(matches) > 1:
        exact = [name for name in matches if name.strip().lower() == needle]
        if len(exact) != 1:
            return json.dumps({
                "error": (f"region_name '{region_name}' matched {len(matches)} regions; "
                          "pass one of the exact names below."),
                "matching_regions": sorted(matches.keys())[:25]
            }, indent=2)
        resolved = exact[0]
    else:
        resolved = next(iter(matches))

    rows = sorted(matches[resolved].values(),
                  key=lambda r: r["period_begin"], reverse=True)
    _cache_put("redfin", cache_key, {"region": resolved, "rows": rows})
    return json.dumps(
        _redfin_snapshot_result(resolved, region_type, rows, months, from_cache=False),
        indent=2)


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
        return json.dumps({
            "error": "FRED_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Get a free API key at https://fred.stlouisfed.org/docs/api/api_key.html"
        })

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
    """
    cached = _cache_get("rentcast", cache_key, CACHE_TTL_MARKET)
    if cached is not None:
        return json.dumps(
            _with_rentcast_quota(cached, _rentcast_usage(), from_cache=True),
            indent=2)

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
    Get rent estimate for a property using Rentcast AVM.

    Responses are cached on disk for 24 hours (cache hits cost no quota).
    Every response includes a "rentcast_quota" note tracking free-tier usage
    ("N/50 free-tier calls used this month") and a warning as the limit nears.

    Args:
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with rent estimate, comparable rentals, and confidence score
    """
    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "RENTCAST_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for a free API key at https://app.rentcast.io/app/api"
        })

    base_url = "https://api.rentcast.io/v1/avm/rent/long-term"
    url = f"{base_url}?{urllib.parse.urlencode({'address': address})}"
    return _rentcast_call(api_key, f"avm-rent|{address.strip().lower()}", url)


@mcp.tool()
def get_rentcast_market_data(zip_code: str) -> str:
    """
    Get rental market statistics for a ZIP code from Rentcast.

    Responses are cached on disk for 24 hours (cache hits cost no quota).
    Every response includes a "rentcast_quota" note tracking free-tier usage
    ("N/50 free-tier calls used this month") and a warning as the limit nears.

    Args:
        zip_code: Five-digit ZIP code (e.g., "90001")

    Returns:
        JSON string with market stats including median rent, rent growth, and vacancy rate
    """
    validation_error = _validate_zip(zip_code)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "RENTCAST_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for a free API key at https://app.rentcast.io/app/api"
        })

    base_url = "https://api.rentcast.io/v1/markets"
    url = f"{base_url}?{urllib.parse.urlencode({'zipCode': zip_code})}"
    return _rentcast_call(api_key, f"markets|{zip_code}", url)


# ============================================================================
# Mashvisor Tools (Paid - requires MASHVISOR_API_KEY)
# ============================================================================

@mcp.tool()
def get_mashvisor_property(address: str, state: str, city: str, zip_code: str) -> str:
    """
    Get property details and rental income estimates from Mashvisor.

    Args:
        address: Street address (e.g., "123 Main St")
        state: Two-letter state code (e.g., "CA")
        city: City name (e.g., "Los Angeles")
        zip_code: Five-digit ZIP code (e.g., "90001")

    Returns:
        JSON string with property details, STR/LTR estimates, and neighborhood score
    """
    validation_error = _validate_zip(zip_code)
    if validation_error:
        return json.dumps({"error": validation_error})

    api_key = os.environ.get("MASHVISOR_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "MASHVISOR_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://www.mashvisor.com/api"
        })

    # Build URL with query parameters
    base_url = "https://api.mashvisor.com/v1.1/client/property"
    params = {
        "address": address,
        "state": state,
        "city": city,
        "zip_code": zip_code
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"Mashvisor API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Mashvisor API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Mashvisor API error: {str(e)}"})


@mcp.tool()
def get_mashvisor_neighborhood(city: str, state: str, zip_code: str = "") -> str:
    """
    Get neighborhood investment analysis from Mashvisor.

    Args:
        city: City name (e.g., "Los Angeles")
        state: Two-letter state code (e.g., "CA")
        zip_code: Five-digit ZIP code (optional, e.g., "90001")

    Returns:
        JSON string with neighborhood analysis including investment score, cash on cash, cap rate
    """
    if zip_code:
        validation_error = _validate_zip(zip_code)
        if validation_error:
            return json.dumps({"error": validation_error})

    api_key = os.environ.get("MASHVISOR_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "MASHVISOR_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://www.mashvisor.com/api"
        })

    # Build URL with query parameters
    base_url = "https://api.mashvisor.com/v1.1/client/neighborhood"
    params = {
        "city": city,
        "state": state
    }
    if zip_code:
        params["zip_code"] = zip_code

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"Mashvisor API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Mashvisor API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Mashvisor API error: {str(e)}"})


# ============================================================================
# AirDNA Tools (Paid - requires AIRDNA_API_KEY)
# ============================================================================

@mcp.tool()
def get_airdna_rentalizer(address: str, bedrooms: int, bathrooms: float) -> str:
    """
    Get short-term rental revenue projections for a property from AirDNA's Rentalizer.

    Args:
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")
        bedrooms: Number of bedrooms (e.g., 3)
        bathrooms: Number of bathrooms (e.g., 2 or 2.5)

    Returns:
        JSON string with STR revenue projection, ADR, occupancy rate, and RevPAR
    """
    api_key = os.environ.get("AIRDNA_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "AIRDNA_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://www.airdna.co/vacation-rental-data"
        })

    # Rentalizer estimates are requested via POST with a JSON body
    url = "https://api.airdna.co/api/enterprise/v2/rentalizer/estimate"
    payload = json.dumps({
        "address": address,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms
    }).encode()

    # Create request with bearer token
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"AirDNA API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"AirDNA API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"AirDNA API error: {str(e)}"})


@mcp.tool()
def get_airdna_market_stats(city: str, state: str) -> str:
    """
    Get market-level short-term rental statistics from AirDNA.

    Args:
        city: City name (e.g., "Los Angeles")
        state: Two-letter state code (e.g., "CA")

    Returns:
        JSON string with market STR metrics including ADR, occupancy, revenue, listings count
    """
    api_key = os.environ.get("AIRDNA_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "AIRDNA_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://www.airdna.co/vacation-rental-data"
        })

    # Build URL with query parameters
    base_url = "https://api.airdna.co/v2/market/statistics"
    params = {
        "city": city,
        "state": state
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with bearer token
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"AirDNA API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"AirDNA API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"AirDNA API error: {str(e)}"})


# ============================================================================
# ATTOM Tools (Paid - requires ATTOM_API_KEY)
# ============================================================================

@mcp.tool()
def get_attom_property(address: str) -> str:
    """
    Get detailed property information from ATTOM Data Solutions.

    Args:
        address: Full property address with a comma between the street and the
            city/state/zip (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with property details, lot size, building size, year built, bed/bath count
    """
    params, address_error = _attom_address_params(address)
    if address_error:
        return json.dumps({"error": address_error})

    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "ATTOM_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://api.developer.attomdata.com/"
        })

    # ATTOM requires the street (address1) and city/state/zip (address2) split
    base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("apikey", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"ATTOM API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"ATTOM API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"ATTOM API error: {str(e)}"})


@mcp.tool()
def get_attom_valuation(address: str) -> str:
    """
    Get automated valuation model (AVM) estimate from ATTOM Data Solutions.

    Args:
        address: Full property address with a comma between the street and the
            city/state/zip (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with AVM estimate, confidence score, and comparable sales
    """
    params, address_error = _attom_address_params(address)
    if address_error:
        return json.dumps({"error": address_error})

    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "ATTOM_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://api.developer.attomdata.com/"
        })

    # ATTOM requires the street (address1) and city/state/zip (address2) split
    base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/valuation/homevaluation"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("apikey", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"ATTOM API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"ATTOM API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"ATTOM API error: {str(e)}"})


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
