# Real Estate Data MCP Server

A Python MCP server that provides tools for accessing multiple real estate data APIs.

## Features

This server exposes 11 tools across 6 different real estate data providers:

### Census Bureau (Free - requires API key)
- `get_census_demographics` - Population, income, rent, and housing statistics
- `get_census_housing_stats` - Median home value and housing age distribution

### Redfin Data Center (Free - no auth)
- `get_redfin_market_data` - Market data file URLs and usage guidance

### Rentcast (Free tier: 50/month - requires API key)
- `estimate_rent` - Rent estimates with comparable rentals
- `get_rentcast_market_data` - ZIP code market statistics

### Mashvisor (Paid - requires API key)
- `get_mashvisor_property` - Property details with STR/LTR estimates
- `get_mashvisor_neighborhood` - Neighborhood investment analysis

### AirDNA (Paid - requires API key)
- `get_airdna_rentalizer` - Short-term rental revenue projections
- `get_airdna_market_stats` - Market-level STR statistics

### ATTOM (Paid - requires API key)
- `get_attom_property` - Detailed property information
- `get_attom_valuation` - Automated valuation model (AVM) estimates

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API keys as environment variables:
```bash
export CENSUS_API_KEY="your_key_here"
export RENTCAST_API_KEY="your_key_here"
export MASHVISOR_API_KEY="your_key_here"
export AIRDNA_API_KEY="your_key_here"
export ATTOM_API_KEY="your_key_here"
```

## Running the Server

```bash
python server.py
```

Or use with MCP client integration via stdio transport.

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
- All tools return JSON-formatted strings
- Redfin tool provides guidance rather than downloading large files

## Example Usage

```python
# Get demographics for Los Angeles County, CA
get_census_demographics(state_fips="06", county_fips="037")

# Estimate rent for a property
estimate_rent(address="123 Main St, Los Angeles, CA 90001")

# Get neighborhood analysis
get_mashvisor_neighborhood(city="Los Angeles", state="CA", zip_code="90001")
```
