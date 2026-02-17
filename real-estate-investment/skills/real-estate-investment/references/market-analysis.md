# Market Analysis & Data Sources

## Table of Contents
1. [Market Scoring Framework](#market-scoring-framework)
2. [API Integration](#api-integration)
   - [Mashvisor API](#mashvisor-api)
   - [AirDNA API](#airdna-api)
   - [ATTOM Data API](#attom-data-api)
   - [Rentcast API](#rentcast-api)
   - [Census Bureau API](#census-bureau-api)
   - [Redfin Data Center](#redfin-data-center)
3. [Comparable Analysis](#comparable-analysis)
4. [Submarket Analysis](#submarket-analysis)

---

## Market Scoring Framework

### Economic Indicators

**Job Growth** (BLS)
- Most critical metric for rental demand
- Data: https://www.bls.gov/emp/, https://trerc.tamu.edu/data/employment-bls/
- National projection: 5.2M jobs 2024-2034 (3.1% growth)

**Population Growth** (Census)
- Census API and ACS at tract/county/metro/state levels

**Median Household Income** (Census ACS)
- Variable: B19013 (Median Household Income)
- Updated annually at all geographic levels

**Rent Growth YoY**
- Sources: Zillow Rent Index (free), Redfin CSV (free), AirDNA (STR, paid), Rentcast API (50 free/month)

### Supply Metrics

**Building Permits**
- HUD SOCDS: https://socds.huduser.gov/permits/ (1980-present, county-level)
- HUD GIS: https://hudgis-hud.opendata.arcgis.com/datasets/HUD::residential-construction-permits-by-county/about
- Census: https://www.census.gov/construction/nrc/

**Construction Pipeline**
- HUD Survey of Construction (SOC)
- HUD Survey of Market Absorption (SOMA)
- HUD USHMC Database (annual/quarterly/monthly)

**Months of Inventory**
- Formula: (Total Active Listings) / (Monthly Sales Volume)
- Sources: MLS, Redfin

### Demand Metrics

**Vacancy Rates**
- Formula: (vacant days / available days) × 100
- Healthy range: 5-10%
- FRED: https://fred.stlouisfed.org/series/RRVRUSQ156N (Q1 1956-present)
- Census Bureau (multiple geographic levels)

**Absorption Rates**
- Formula: (Total SF Leased/Sold) / (Total Time Period)
- Sources: CoStar, local MLS, real estate associations

**Days on Market**
- Sources: MLS, Zillow, Redfin, Realtor.com

### Affordability Metrics

**Rent-to-Income Ratio**
- Formula: (Monthly Rent) / (Gross Monthly Income)
- Standard: ≤30% (typical landlord requirement)

**Price-to-Rent Ratio**
- Formula: (Home Price) / (Annual Gross Rent)
- <15: Buying favored | 15-21: Balanced | >21: Renting favored
- Related: 7% rule (annual rent ≈ 7% of purchase price)

**Home Price-to-Income Ratio**
- Formula: (Median Home Price) / (Median Household Income)
- Combine Census income + Zillow/Redfin price data

### Weighted Scoring Model

Example structure:
```
Job Growth: 20%
Rent Growth YoY: 20%
Population Growth: 15%
Vacancy Rate: 15%
Median Income Growth: 10%
Price-to-Rent Ratio: 10%
Building Permits: 5%
Days on Market: 5%
```

Calculate distance between comparatives and target; weight by Gross Asset Value (GAV) for portfolios.

---

## API Integration

### Mashvisor API

**Auth**: Token via `x-api-key` HTTP header (JWT over HTTPS)
**Base**: `https://api.mashvisor.com/v1.1/client/`
**Docs**: https://www.mashvisor.com/api-doc/, https://github.com/mashvisor/mashvisor-api-docs

**Endpoints**:
```
GET /airbnb-property/market-summary
    Params: state, city
GET /trends/neighborhoods
GET /city/properties/{state}/{city}
```

**Python**:
```python
import requests

headers = {'x-api-key': 'YOUR_API_KEY'}
url = 'https://api.mashvisor.com/v1.1/client/airbnb-property/market-summary'
params = {'state': 'FL', 'city': 'Miami'}
response = requests.get(url, headers=headers, params=params)
data = response.json()
```

**Pricing**: Contact sales (available via RapidAPI)

---

### AirDNA API

**Auth**: Bearer Token in `Authorization` header
**Base**: `https://api.airdna.co`
**Docs**: https://apidocs.airdna.co/, https://airdna.redoc.ly/, https://enterprise-help.airdna.co/en/articles/8185669

**Packages**: Market Data, Property Valuations & Comps, Rentalizer Lead Gen, Smart Rates Data

**Endpoints**:
```
POST /rentalizer/estimate
    Returns: Revenue projections, occupancy, recommended rates
GET /market/search
    Returns: Market availability, classification
GET /property/availability
    Returns: Availability calendar (up to 12 months)
```

**Python**:
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_TOKEN',
    'Accept': 'application/json'
}

url = 'https://api.airdna.co/rentalizer/estimate'
payload = {
    'address': '123 Main St, Miami, FL 33101',
    'bedrooms': 2,
    'bathrooms': 2
}
response = requests.post(url, headers=headers, json=payload)
estimate = response.json()
```

**Pricing**: Contact sales; enterprise discounts for >5,000 calls/month

---

### ATTOM Data API

**Coverage**: 155M+ U.S. residential/commercial properties, 70B rows, 9,000 attributes/property
**Docs**: https://apitracker.io/a/attomdata, https://www.postman.com/api-evangelist/attom/documentation/4puqnzg, https://docs.deweydata.io/docs/attom

**Data**: Property details, tax assessments, sales history, ownership, AVMs, automated rent values, mortgage info, zoning, land use, development applications, historical imagery

**Endpoints**: Property Details, Property Valuation (AVM), Sales History, Tax Assessment, Mortgage/Foreclosure, Neighborhood Data

**Python**:
```python
import requests

headers = {
    'apikey': 'YOUR_API_KEY',
    'Accept': 'application/json'
}

url = 'https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail'
params = {
    'address1': '123 Main St',
    'address2': 'Miami, FL 33101'
}
response = requests.get(url, headers=headers, params=params)
property_data = response.json()
```

**Pricing**: ~$500/month basic (few thousand calls); scales for bulk downloads; enterprise via consultation

---

### Rentcast API

**Auth**: API Key via `X-Api-Key` header
**Base**: `https://api.rentcast.io/v1/`
**Docs**: https://developers.rentcast.io/, https://www.postman.com/rentcast/rentcast-api/documentation/ca4yudw

**Endpoints**:
```
GET /properties
    Params: city, state, limit
GET /avm/value
    Returns: Property valuation estimate
GET /avm/rent
    Returns: Rental estimate
GET /markets
    Returns: Market trends, statistics
```

**Python**:
```python
import requests

headers = {
    'Accept': 'application/json',
    'X-Api-Key': 'YOUR_API_KEY'
}

# Search properties
url = 'https://api.rentcast.io/v1/properties'
params = {'city': 'Austin', 'state': 'TX', 'limit': 20}
response = requests.get(url, headers=headers, params=params)
properties = response.json()

# Rental estimate
url = 'https://api.rentcast.io/v1/avm/rent'
params = {
    'address': '123 Main St',
    'city': 'Austin',
    'state': 'TX',
    'zipCode': '78701',
    'bedrooms': 2,
    'bathrooms': 2,
    'squareFootage': 1200
}
response = requests.get(url, headers=headers, params=params)
rent_estimate = response.json()
```

**Pricing**: Free (50 requests/month), paid tiers with higher limits, live support 7 days/week

---

### Census Bureau API

**Auth**: Free API key via query param `?key=YOUR_API_KEY`
**Request key**: https://api.census.gov/data/key_signup.html
**Base URLs**:
- ACS 5-Year: `https://api.census.gov/data/{year}/acs/acs5`
- ACS 1-Year: `https://api.census.gov/data/{year}/acs/acs1`
- Decennial: `https://api.census.gov/data/{year}/dec/sf1`

**Docs**: https://www.census.gov/data/developers/data-sets.html, https://www.census.gov/programs-surveys/acs/data/data-via-api.html

**Key Housing Variables**:
```
B25001: Total Housing Units
B25002: Occupancy Status
B25003: Tenure (Owner/Renter)
B25004: Vacancy Status (For Rent, For Sale, etc.)
B25034: Year Structure Built
B25064: Median Gross Rent
B25077: Median Home Value
B19013: Median Household Income
B01003: Total Population
```

**Variable Finder**: https://api.census.gov/data/2021/acs/acs5/variables.html

**Python (census library)**:
```python
from census import Census
from us import states

c = Census("YOUR_API_KEY")

# Median household income by state
data = c.acs5.get(
    ('NAME', 'B19013_001E'),
    {'for': 'state:*'},
    year=2021
)

# Vacancy status by tract (Miami-Dade County, FL)
data = c.acs5.get(
    ('NAME', 'B25004_001E', 'B25004_002E', 'B25004_003E'),
    {'for': 'tract:*', 'in': 'state:12 county:086'},
    year=2021
)

# Multiple housing variables for city
variables = ['NAME', 'B25001_001E', 'B25002_002E', 'B25002_003E',
             'B25064_001E', 'B19013_001E']
data = c.acs5.get(
    tuple(variables),
    {'for': 'place:45000', 'in': 'state:12'},  # Miami, FL
    year=2021
)
```

**Python (requests)**:
```python
import requests
import pandas as pd

base_url = 'https://api.census.gov/data/2021/acs/acs5'
params = {
    'get': 'NAME,B25001_001E,B25064_001E,B19013_001E',
    'for': 'county:*',
    'in': 'state:12',  # Florida
    'key': 'YOUR_API_KEY'
}
response = requests.get(base_url, params=params)
data = response.json()
df = pd.DataFrame(data[1:], columns=data[0])
```

**Geographic Levels**: Nation, State, County, Census Tract, Block Group, Place (cities), MSA, ZCTA

**Libraries**: census (https://pypi.org/project/census/), pytidycensus, censusdata

**Pricing**: FREE

---

### Redfin Data Center

**Access**: Manual CSV download (no API)
**URL**: https://www.redfin.com/news/data-center/, https://www.redfin.com/news/data-center/printable-market-data/

**Geographic Levels**: National, Metro, State, County, City, ZIP, Neighborhood

**Metrics**: Median sale price, homes sold, new listings, days on market, price drops, inventory, sale-to-list ratio, pending sales, off-market sales

**Updates**: Weekly (Wednesdays), Monthly (3rd Friday)

**Download Methods**:
1. Via visualization: Select region/metro/timeframe/metric → click chart → download button
2. Via Download tab: Select region type → download complete dataset

**Python (conceptual)**:
```python
import requests
import pandas as pd
from io import StringIO

# UNVERIFIED - may require interactive download
url = 'https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz'
response = requests.get(url)
df = pd.read_csv(StringIO(response.text), sep='\t', compression='gzip')
miami_data = df[df['city'] == 'Miami']
```

**Pricing**: FREE

---

## Comparable Analysis

### Selection Criteria

**1. Proximity**
- Same neighborhood preferred
- Set radius/"circle" around subject
- Location differences = value differences

**2. Recency**
- Last 3-6 months standard
- Older sales require market conditions adjustments

**3. Similarity**
- Size (SF), age, style, condition, site characteristics, room count, finished area
- More alike = fewer adjustments needed

**Minimum**: 3 recently sold similar properties

**Sources**: MLS, public records, Zillow/Redfin/Realtor.com, PropStream, CoreLogic, Black Knight, ATTOM/Rentcast APIs

### Adjustment Methodology

**1. Transactional Adjustments**
- Financing terms (seller financing, below-market rates)
- Conditions of sale (distressed, foreclosure, short sale, REO)
- Motivations (rushed sale, family transfer, estate)

**2. Market Conditions**
- Appreciation/depreciation between comp sale date and appraisal date
- Calculated as % change per month/quarter

**3. Physical Characteristics**
- Location, size/SF, lot size, age, condition, amenities, bedrooms/bathrooms, views

**Adjustment Direction**:
- Comp INFERIOR to subject → ADD to comp price
- Comp SUPERIOR to subject → SUBTRACT from comp price

**Goal**: Adjust comps to approximate value if identical to subject

### Quantitative Methods

**1. Paired Sales Analysis**
- Find 2 similar properties differing in ONE characteristic
- Formula: (Price Difference) / (Feature Difference)
- Example: Home A (2,000 SF, $400k) vs. Home B (2,500 SF, $450k) → $50k / 500 SF = $100/SF

**2. Market-Based Adjustments**
- Statistical regression from local sales data
- Reflects actual market reaction

**3. Cost-Based Adjustments**
- Cost to create minus depreciation
- Less reliable for buyer value

### Per-Square-Foot Adjustments

**Calculation**: (Sale Price) / (Square Footage)

**Diminishing Returns**:
- First 1,000 SF worth more/SF than beyond 3,000 SF
- Adjust at lower rate for additional SF

**Example**:
```
Comp: 2,000 SF, $400k → $200/SF
Subject: 2,500 SF

Option 1 (Full Rate): 2,500 × $200 = $500k
Option 2 (Marginal Rate): $400k + (500 SF × $150) = $475k
```

### Multifamily Per-Unit Adjustments

**Unit Types**: Studio, 1BR/1BA, 2BR/1BA, 2BR/2BA, 3BR/2BA

**Process**:
1. Identify unit mix for subject and comps
2. Calculate per-unit value from comp sales
3. Adjust for unit mix differences
4. Consider income potential, market rent, unit size

**Example**:
```
Comp: 10 units (5×1BR, 5×2BR), $1.5M
Subject: 10 units (3×1BR, 7×2BR)

Assume 1BR=$120k, 2BR=$180k (from paired sales)
Comp: (5×$120k) + (5×$180k) = $1.5M ✓
Subject: (3×$120k) + (7×$180k) = $1.62M
```

### Automated Valuation Models (AVMs)

**Types**:
1. **Comparables-Based**: Mimics appraiser's sales comparison approach
2. **Hedonic Models**: Statistical regression (e.g., Zillow Zestimate, Redfin Estimate, ATTOM AVM)

**Advantages**: Speed, consistency, cost-effective, scalability, objectivity

**Limitations**: Data-dependent, no physical inspection, assumes average condition, market lag, less accurate for unique properties

**Accuracy**: Median error 5-10% in data-rich markets; higher in rural/unique/volatile markets

**Providers**: Zillow, Redfin, ATTOM, CoreLogic, Black Knight, Collateral Analytics, HouseCanary, ClearCapital

**Best Practices**:
- Use as starting point
- Compare multiple AVM sources
- Verify with recent comps
- Physical inspection for high-stakes decisions
- Adjust for known condition issues

---

## Submarket Analysis

### Neighborhood Signals

**School Ratings**
- Data: **GreatSchools API** (https://www.greatschools.org/api)
- Coverage: 200,000+ K-12 public/private/charter schools
- NearbySchools API for location-based search
- Scale: 1-10 (10=highest)

**Crime Statistics**
- **NeighborhoodScout**: https://www.neighborhoodscout.com/, API: https://api.locationinc.com/about-the-data (≥$5k/year)
- **SpotCrime**: https://spotcrime.com/ (free, Google Maps plots)
- **CrimeGrade**: https://crimegrade.org/ (neighborhood-level grades)
- **LexisNexis Community Crime Map**: https://communitycrimemap.com/
- Local police department portals

**Walkability**
- **Walk Score API**: https://www.walkscore.com/professional/api.php
- Base: `https://api.walkscore.com`
- Metrics: Walk Score, Transit Score, Bike Score
- Default quota: 5,000 calls/day
- Docs: https://walkscore-api.readthedocs.io/, PyPI: https://pypi.org/project/walkscore-api/

**Python (Walk Score)**:
```python
import requests

api_key = 'YOUR_WALKSCORE_API_KEY'
url = 'https://api.walkscore.com/score'
params = {
    'format': 'json',
    'address': '123 Main St Miami FL 33101',
    'lat': 25.7617,
    'lon': -80.1918,
    'transit': 1,
    'bike': 1,
    'wsapikey': api_key
}
response = requests.get(url, params=params)
scores = response.json()
print(f"Walk: {scores.get('walkscore')}, Transit: {scores.get('transit', {}).get('score')}, Bike: {scores.get('bike', {}).get('score')}")
```

**Transit Access**
- Walk Score Transit API, local transit authority APIs, Google Maps Distance Matrix API

### Integrated Platforms

- **NeighborhoodScout**: All-in-one (crime, demographics, housing, schools, trends), API ≥$5k/year
- **Realtor.com**: GreatSchools + walkability + crime + demographics
- **Zillow**: GreatSchools + Walk/Transit/Bike + demographics + crime (API discontinued for new users)
- **Redfin**: GreatSchools + demographics + crime + walkability (CSV downloads, not neighborhood APIs)

### Submarket Definition

**What**: Geographic area (neighborhood, zip, census tracts) with distinct characteristics (school district, zoning, demographics, housing type/age, income, walkability/transit)

**Evaluation Framework**:

**1. Demand**
- Days on market (lower=stronger), absorption rate (higher=stronger), rent/price growth YoY, vacancy rate (lower=tighter), population growth

**2. Supply**
- Building permits, new construction starts, inventory levels (months), conversion projects

**3. Demographics**
- Median income, age distribution, renter vs. owner rate, education, employment sectors

**4. Amenity Access**
- School ratings, Walk/Transit/Bike Score, crime rate, parks/recreation

**5. Physical**
- Housing stock age, property types, lot sizes, architectural styles, condition/renovation trends

**6. Investment**
- Price-to-rent ratio, cap rates, cash-on-cash return, rent growth, appreciation history

**Scoring Model**:
```python
import pandas as pd

def score_submarket(submarket_data):
    weights = {
        'job_growth': 0.15,
        'population_growth': 0.10,
        'rent_growth_yoy': 0.15,
        'median_income': 0.10,
        'school_rating': 0.10,
        'walk_score': 0.05,
        'crime_grade': 0.10,
        'vacancy_rate': 0.10,  # Inverse
        'days_on_market': 0.05,  # Inverse
        'price_to_rent': 0.10
    }
    normalized = normalize_metrics(submarket_data)  # 0-100 scale
    score = sum(normalized[k] * weights[k] for k in weights)
    return score

submarkets_df['score'] = submarkets_df.apply(score_submarket, axis=1)
top_submarkets = submarkets_df.nlargest(10, 'score')
```

**Identification Techniques**:
1. **Geographic**: Zip codes, census tracts, neighborhoods, school districts, MLS areas
2. **Statistical**: K-means clustering on property/demographic characteristics
3. **Local Knowledge**: Realtor insights, historical delineations, cultural enclaves

**Use Cases**: Target acquisition zones, pricing strategy, risk assessment, marketing messaging, development site selection
