#!/usr/bin/env python3
"""
Real Estate Data MCP Server
Provides tools for accessing multiple real estate data APIs including Census Bureau,
Redfin Data Center, Rentcast, Mashvisor, AirDNA, and ATTOM.
"""

from mcp.server.fastmcp import FastMCP
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import gzip
from io import BytesIO

mcp = FastMCP("real-estate-data")


# ============================================================================
# Census Bureau Tools (Free - requires CENSUS_API_KEY)
# ============================================================================

@mcp.tool()
def get_census_demographics(state_fips: str, county_fips: str = "", tract: str = "") -> str:
    """
    Get demographic data from Census Bureau's ACS 5-year survey.

    Args:
        state_fips: Two-digit state FIPS code (e.g., "06" for California)
        county_fips: Three-digit county FIPS code (optional, e.g., "037" for Los Angeles)
        tract: Six-digit census tract code (optional)

    Returns:
        JSON string with population, income, rent, and housing statistics
    """
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

    # Build URL
    base_url = "https://api.census.gov/data/2022/acs/acs5"
    params = {
        "get": ",".join(variables),
        "key": api_key
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}&{geography}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        if len(data) < 2:
            return json.dumps({"error": "No data returned from Census API"})

        # Parse response (first row is headers, second row is data)
        headers = data[0]
        values = data[1]

        # Create result dictionary
        result = {
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
def get_census_housing_stats(state_fips: str, county_fips: str = "") -> str:
    """
    Get housing statistics from Census Bureau including median home value and year built data.

    Args:
        state_fips: Two-digit state FIPS code (e.g., "06" for California)
        county_fips: Three-digit county FIPS code (optional, e.g., "037" for Los Angeles)

    Returns:
        JSON string with median home value and housing age distribution
    """
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

    # Build URL
    base_url = "https://api.census.gov/data/2022/acs/acs5"
    params = {
        "get": ",".join(variables),
        "key": api_key
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}&{geography}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        if len(data) < 2:
            return json.dumps({"error": "No data returned from Census API"})

        # Parse response
        values = data[1]

        # Create result dictionary
        result = {
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
def get_redfin_market_data(region_type: str = "metro", time_period: str = "monthly") -> str:
    """
    Get information about Redfin market data files and how to access them.
    Note: These are large TSV files (hundreds of MB) - this tool provides URLs and guidance.

    Args:
        region_type: Type of region data ("national" or "metro")
        time_period: Time period for data ("monthly" is the primary option)

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
        region_type = "metro"

    file_url = base_url + files[region_type]

    result = {
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


# ============================================================================
# Rentcast Tools (Free tier: 50 requests/month - requires RENTCAST_API_KEY)
# ============================================================================

@mcp.tool()
def estimate_rent(address: str) -> str:
    """
    Get rent estimate for a property using Rentcast AVM.

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

    # Build URL with query parameters
    base_url = "https://api.rentcast.io/v1/avm/rent/long-term"
    params = {"address": address}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("X-Api-Key", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"Rentcast API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Rentcast API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Rentcast API error: {str(e)}"})


@mcp.tool()
def get_rentcast_market_data(zip_code: str) -> str:
    """
    Get rental market statistics for a ZIP code from Rentcast.

    Args:
        zip_code: Five-digit ZIP code (e.g., "90001")

    Returns:
        JSON string with market stats including median rent, rent growth, and vacancy rate
    """
    api_key = os.environ.get("RENTCAST_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "RENTCAST_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for a free API key at https://app.rentcast.io/app/api"
        })

    # Build URL with query parameters
    base_url = "https://api.rentcast.io/v1/markets"
    params = {"zipCode": zip_code}
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Create request with API key header
    req = urllib.request.Request(url)
    req.add_header("X-Api-Key", api_key)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

        return json.dumps(data, indent=2)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return json.dumps({
            "error": f"Rentcast API HTTP error: {e.code} - {e.reason}",
            "details": error_body
        })
    except urllib.error.URLError as e:
        return json.dumps({"error": f"Rentcast API connection error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Rentcast API error: {str(e)}"})


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
def get_airdna_rentalizer(address: str) -> str:
    """
    Get short-term rental revenue projections for a property from AirDNA.

    Args:
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with STR revenue projection, ADR, occupancy rate, and RevPAR
    """
    api_key = os.environ.get("AIRDNA_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "AIRDNA_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://www.airdna.co/vacation-rental-data"
        })

    # Build URL with query parameters
    base_url = "https://api.airdna.co/v2/rentalizer"
    params = {"address": address}
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
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with property details, lot size, building size, year built, bed/bath count
    """
    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "ATTOM_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://api.developer.attomdata.com/"
        })

    # Build URL with query parameters
    base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
    params = {"address": address}
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
        address: Full property address (e.g., "123 Main St, Los Angeles, CA 90001")

    Returns:
        JSON string with AVM estimate, confidence score, and comparable sales
    """
    api_key = os.environ.get("ATTOM_API_KEY", "")
    if not api_key:
        return json.dumps({
            "error": "ATTOM_API_KEY not configured. Set it in your plugin's environment variables.",
            "info": "Sign up for an API key at https://api.developer.attomdata.com/"
        })

    # Build URL with query parameters
    base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/valuation/homevaluation"
    params = {"address": address}
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
