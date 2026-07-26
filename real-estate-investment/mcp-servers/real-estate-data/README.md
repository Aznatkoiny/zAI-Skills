# Real Estate Data MCP Server

A Python MCP server that provides tools for accessing multiple real estate data APIs.

## Features

This server exposes 11 tools across 6 different real estate data providers:

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
- `get_redfin_market_data(region_type="metro")` - Market data file URLs and usage guidance.
  Valid `region_type` values: `national`, `metro`, `city`, `zip`, `neighborhood`.
  Invalid values return an error listing the accepted options.

### Rentcast (Free tier: 50/month - requires API key)
- `estimate_rent(address)` - Rent estimates with comparable rentals
- `get_rentcast_market_data(zip_code)` - ZIP code market statistics (ZIP must be 5 digits)

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
export RENTCAST_API_KEY="your_key_here"
export MASHVISOR_API_KEY="your_key_here"
export AIRDNA_API_KEY="your_key_here"
export ATTOM_API_KEY="your_key_here"
```

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

## API Key Resources

- **Census Bureau**: Free API key at https://api.census.gov/data/key_signup.html
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
- Redfin tool provides guidance rather than downloading large files

## Example Usage

```python
# Get demographics for Los Angeles County, CA (latest vintage, auto-detected)
get_census_demographics(state_fips="06", county_fips="037")

# Pin a specific ACS vintage
get_census_demographics(state_fips="06", county_fips="037", year=2022)

# Estimate rent for a property
estimate_rent(address="123 Main St, Los Angeles, CA 90001")

# Project STR revenue for a 3 bed / 2 bath property
get_airdna_rentalizer(address="123 Main St, Los Angeles, CA 90001", bedrooms=3, bathrooms=2)

# ATTOM property detail (comma between street and city/state/zip is required)
get_attom_property(address="123 Main St, Los Angeles, CA 90001")

# Get neighborhood analysis
get_mashvisor_neighborhood(city="Los Angeles", state="CA", zip_code="90001")
```
