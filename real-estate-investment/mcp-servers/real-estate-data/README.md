# Real Estate Data MCP Server

A Python MCP server with 13 tools across 7 real estate data providers. The
`real-estate-investment` plugin starts it automatically; this file is for
anyone working on the server itself.

## Tools

### Redfin Data Center (free, no key)
- `get_redfin_market_snapshot(region_name, region_type="metro", months=24)`: market
  time series (median sale price and its year-over-year change, price per sq ft,
  homes sold, new listings, inventory, months of supply, median days on market,
  sale-to-list ratio) for one or more regions, newest first. Pass several regions
  separated by `" | "` to read the file once for all of them. `region_type` is
  `metro`, `county`, `place` (cities), `zip`, `state`, or `national`. Metro,
  county, state and national data are monthly; city and ZIP data are mostly
  rolling 3-month periods, and the response's `period_type` says which.
  The server streams Redfin's public CSV for that level row by row (metro ~46 MB,
  county ~150 MB, place ~1.1 GB, zip ~1.3 GB), keeps only the matching rows, and
  caches them for 24 hours. No-match errors list example region names.
- `get_redfin_market_data(region_type="metro")`: the download URL and column guide
  for a whole Redfin file, for analysis across many regions at once.

### Census Bureau ACS (free key)
- `get_census_demographics(state_fips, county_fips="", tract="", year=0)`: population,
  median household income, median gross rent, housing units, occupancy and tenure.
- `get_census_housing_stats(state_fips, county_fips="", year=0)`: median home value
  and housing units by year built. From the 2021 vintage the newest bins are
  `2020_or_later` and `2010_to_2019`; earlier vintages use `2014_or_later` and
  `2010_to_2013`.

`year` picks the ACS 5-year vintage; by default the server tries the current year
minus 2 and falls back a year if that isn't published. The vintage used is
returned as `acs_vintage`. Census "no estimate" codes (-666666666 and similar)
come back as `null`.

### FRED (free key)
- `get_fred_series(series_id, observations=24)`: recent observations, newest first.
  Useful series: `MORTGAGE30US` (30-year mortgage rate, weekly), `DGS10` (10-year
  Treasury, daily), `RRVRUSQ156N` (US rental vacancy rate, quarterly).

### Rentcast (50 free calls a month, then billed per call)
- `estimate_rent(address)`: long-term rent estimate with a low-high range and the
  comparable listings used. No separate confidence score.
- `get_rentcast_market_data(zip_code)`: sale and rental listing statistics for a ZIP
  (averages, medians, days on market, listing counts, by property type and
  bedrooms, with monthly history). No vacancy rate.

Responses are cached for 24 hours (cache hits cost nothing) and carry a
`rentcast_quota` note from a monthly counter. At 50 calls the server stops making
live calls unless `RENTCAST_ALLOW_OVERAGE=1` is set, because Rentcast bills each
extra request.

### Paid providers (unverified)
These follow each provider's published docs but haven't been run against a live
key, so their responses carry an `unverified_integration` note and pass the
provider's JSON through unchanged.

- Mashvisor (`MASHVISOR_API_KEY`):
  - `get_mashvisor_property(address, state, city, zip_code)`: the property record
    (rental estimates live on another Mashvisor endpoint this tool doesn't call).
  - `get_mashvisor_neighborhood(city, state, neighborhood="", neighborhood_id="")`:
    lists a city's neighborhoods with IDs, then fetches the overview for one.
- AirDNA Enterprise API (`AIRDNA_API_KEY`, issued by AirDNA's sales team):
  - `get_airdna_rentalizer(address, bedrooms, bathrooms)`: one property's STR
    revenue estimate.
  - `get_airdna_market_stats(city, state)`: finds the market, then fetches its
    occupancy, ADR and average revenue.
- ATTOM (`ATTOM_API_KEY`):
  - `get_attom_property(address)`: property facts.
  - `get_attom_valuation(address)`: AVM value, high-low range and confidence
    score (`scr`); no comparable sales.

  ATTOM wants the street and the city/state/zip separately, so pass an address
  with a comma between them: `"123 Main St, Los Angeles, CA 90001"`.

## Setup

The plugin launches the server through `run.sh`, which finds Python 3.10 or newer,
creates a `.venv` next to `server.py` on first run, and installs
`requirements.txt` into it (re-installing only when that file changes). Setup
messages go to stderr because stdout carries the MCP protocol. The same venv has
numpy and numpy-financial for the plugin's calculation scripts.

API keys are read from the environment. Set the ones you have in your shell
profile or under `env` in `~/.claude/settings.json`, then restart Claude Code:

```bash
export CENSUS_API_KEY="..."     # https://api.census.gov/data/key_signup.html
export FRED_API_KEY="..."       # https://fred.stlouisfed.org/docs/api/api_key.html
export RENTCAST_API_KEY="..."   # https://app.rentcast.io/app/api
export MASHVISOR_API_KEY="..."  # https://www.mashvisor.com/data-api
export AIRDNA_API_KEY="..."     # from AirDNA sales
export ATTOM_API_KEY="..."      # https://api.developer.attomdata.com/
```

Redfin needs no key.

## Caching

Responses are cached under `~/.cache/real-estate-data/` (override with
`REAL_ESTATE_DATA_CACHE_DIR`): Census for 7 days; Rentcast, FRED and Redfin
region series for 24 hours. An unwritable cache directory just turns caching
off. The Rentcast counter lives in the same directory (`rentcast-usage.json`).

## Development

- HTTP uses only the standard library (`urllib`); the one server dependency is `mcp`.
- Offline tests, with `mcp` and the network stubbed:
  `.venv/bin/python -m unittest test_server` (or `bash scripts/smoke_servers.sh`
  from the repo root).

```python
get_redfin_market_snapshot("Austin, TX metro area | Nashville, TN metro area", "metro", 12)
get_redfin_market_snapshot("78704", "zip")
get_census_demographics(state_fips="48", county_fips="453")
get_fred_series("MORTGAGE30US")
estimate_rent("123 Main St, Austin, TX 78704")
```
