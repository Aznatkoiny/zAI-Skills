# Real Estate Data MCP Server

A Python MCP server that provides tools for accessing multiple real estate data APIs.

## Features

This server exposes 13 tools across 7 different real estate data providers:

### Census Bureau (Free - requires API key)
- `get_census_demographics(state_fips, county_fips="", tract="", year=0)` - Population, income, rent, and housing statistics
- `get_census_housing_stats(state_fips, county_fips="", year=0)` - Median home value and housing age distribution

Both tools accept an optional `year` (ACS 5-year vintage, e.g., `2023`). When
omitted, the server uses the latest likely vintage (current year minus 2) and
automatically falls back one more year if that vintage is not yet published.
The vintage actually used is returned as `acs_vintage` in the JSON result.
Inputs are validated: `state_fips` must be 2 digits, `county_fips` 3 digits,
`tract` 6 digits, and `tract` requires `county_fips`.

### Redfin Data Center (Free - no auth)
- `get_redfin_market_snapshot(region_name, region_type="metro", months=24)` - Live
  monthly market time series (median sale price, homes sold, inventory, median DOM,
  months of supply) for one region, streamed line-by-line from Redfin's public
  gzipped TSVs on S3 without loading the whole file. `region_type` is one of
  `metro`, `county`, `place` (cities), or `zip`. The first uncached call streams
  the whole file (metro ~110 MB, county ~240 MB, place ~1 GB, zip ~1.5 GB
  compressed); the filtered slice is then cached for 24 hours, so repeat calls
  are instant. No-match errors list valid region examples and sample region
  names from the file. This is the plugin's zero-key live-data path.
- `get_redfin_market_data(region_type="metro")` - Market data file URLs and usage guidance
  (points to `get_redfin_market_snapshot` for ready-parsed data).
  Valid `region_type` values: `national`, `metro`, `city`, `zip`, `neighborhood`.
  Invalid values return an error listing the accepted options.

### FRED (Free - requires API key)
- `get_fred_series(series_id, observations=24)` - Recent observations for any FRED
  series, newest first. Recommended macro series for underwriting:
  `MORTGAGE30US` (30-year fixed mortgage rate, weekly), `DGS10` (10-year Treasury
  yield, daily), `RRVRUSQ156N` (US rental vacancy rate, quarterly).

### Rentcast (Free tier: 50/month - requires API key)
- `estimate_rent(address)` - Rent estimates with comparable rentals
- `get_rentcast_market_data(zip_code)` - ZIP code market statistics (ZIP must be 5 digits)

Both Rentcast tools cache responses for 24 hours (cache hits cost no quota) and
append a `rentcast_quota` note ("N/50 free-tier calls used this month") backed by
a persistent monthly counter, with a warning once usage reaches 45.

### Mashvisor (Paid - requires API key)
- `get_mashvisor_property(address, state, city, zip_code)` - Property details with STR/LTR estimates
- `get_mashvisor_neighborhood(city, state, zip_code="")` - Neighborhood investment analysis

### AirDNA (Paid - requires API key)
- `get_airdna_rentalizer(address, bedrooms, bathrooms)` - Short-term rental revenue projections.
  Sent as a POST with a JSON body to AirDNA's Rentalizer estimate endpoint;
  `bedrooms` (int) and `bathrooms` (float, e.g., `2.5`) are required.
- `get_airdna_market_stats(city, state)` - Market-level STR statistics

### ATTOM (Paid - requires API key)
- `get_attom_property(address)` - Detailed property information
- `get_attom_valuation(address)` - Automated valuation model (AVM) estimates

ATTOM requires the street and the city/state/zip as separate `address1` /
`address2` query parameters. The server splits the address on the first comma,
so pass a full address like `"123 Main St, Los Angeles, CA 90001"`. Addresses
without a comma return a clear error instead of a failed API call.

## Installation

When installed as part of the `real-estate-investment` plugin, no manual setup
is needed: the plugin launches the server through `run.sh`, which on first run
creates a `.venv` next to `server.py` and installs `requirements.txt` into it
(progress is printed to stderr). Later runs reuse the venv and re-install only
if `requirements.txt` changes.

Set up API keys as environment variables before starting Claude Code:
```bash
export CENSUS_API_KEY="your_key_here"
export FRED_API_KEY="your_key_here"
export RENTCAST_API_KEY="your_key_here"
export MASHVISOR_API_KEY="your_key_here"
export AIRDNA_API_KEY="your_key_here"
export ATTOM_API_KEY="your_key_here"
```

No key is needed for the Redfin tools.

## Running the Server

Via the launcher (recommended - creates/reuses the local venv automatically):
```bash
bash run.sh
```

Or manually with your own environment:
```bash
pip install -r requirements.txt
python server.py
```

Both use the MCP stdio transport, so all diagnostics go to stderr and stdout is
reserved for the protocol.

## Caching and Quota Guarding

Responses from slow or quota-limited sources are cached on disk under
`~/.cache/real-estate-data/` (override with `REAL_ESTATE_DATA_CACHE_DIR`):

- Census ACS responses: 7 days
- Rentcast and FRED responses: 24 hours
- Filtered Redfin market-tracker slices: 24 hours

Caching is best-effort: an unwritable cache directory just disables it and
never breaks a tool call. Rentcast free-tier usage is tracked with a
persistent monthly counter (`rentcast-usage.json` in the cache dir); every
Rentcast response reports usage and warns as the 50-call limit approaches.

## API Key Resources

- **Census Bureau**: Free API key at https://api.census.gov/data/key_signup.html
- **FRED**: Free API key at https://fred.stlouisfed.org/docs/api/api_key.html
- **Rentcast**: Sign up at https://app.rentcast.io/app/api
- **Mashvisor**: Sign up at https://www.mashvisor.com/api
- **AirDNA**: Sign up at https://www.airdna.co/vacation-rental-data
- **ATTOM**: Sign up at https://api.developer.attomdata.com/

## Implementation Notes

- Uses **only Python standard library** for HTTP requests (`urllib.request`)
- Single dependency: `mcp>=1.0.0`
- Graceful error handling for missing API keys and network errors
- Input validation for FIPS codes and ZIP codes with clear error messages
- All tools return JSON-formatted strings
- `get_redfin_market_snapshot` streams gzipped TSVs incrementally (constant memory)
- Best-effort disk caching plus a persistent Rentcast monthly-quota counter
- Offline unit checks in `test_server.py` (stubbed `mcp` and network):
  `python3 -m unittest test_server`

## Example Usage

```python
# Get demographics for Los Angeles County, CA (latest vintage, auto-detected)
get_census_demographics(state_fips="06", county_fips="037")

# Pin a specific ACS vintage
get_census_demographics(state_fips="06", county_fips="037", year=2022)

# Live Redfin monthly market snapshot (no API key needed)
get_redfin_market_snapshot(region_name="Boise", region_type="metro", months=12)
get_redfin_market_snapshot(region_name="90210", region_type="zip")

# Macro context from FRED (30-year mortgage rate, last 24 weekly readings)
get_fred_series(series_id="MORTGAGE30US")

# Estimate rent for a property
estimate_rent(address="123 Main St, Los Angeles, CA 90001")

# Project STR revenue for a 3 bed / 2 bath property
get_airdna_rentalizer(address="123 Main St, Los Angeles, CA 90001", bedrooms=3, bathrooms=2)

# ATTOM property detail (comma between street and city/state/zip is required)
get_attom_property(address="123 Main St, Los Angeles, CA 90001")

# Get neighborhood analysis
get_mashvisor_neighborhood(city="Los Angeles", state="CA", zip_code="90001")
```
