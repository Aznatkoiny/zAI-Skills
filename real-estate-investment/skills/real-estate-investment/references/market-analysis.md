# Market Analysis & Data Sources

## Table of Contents
1. [Market Scoring Framework](#market-scoring-framework)
2. [Data Tools](#data-tools)
3. [Comparable Analysis](#comparable-analysis)
4. [Submarket Analysis](#submarket-analysis)

---

## Market Scoring Framework

### Economic Indicators

**Job Growth** (BLS)
- Most critical metric for rental demand
- Data: https://www.bls.gov/emp/, https://trerc.tamu.edu/data/employment-bls/

**Population Growth** (Census)
- Census API and ACS at tract/county/metro/state levels

**Median Household Income** (Census ACS)
- Variable: B19013 (Median Household Income)
- Updated annually at all geographic levels

**Rent Growth YoY**
- Sources: Zillow Observed Rent Index (free), Census ACS year over year (free key), Rentcast (50 free calls/month), AirDNA (STR, paid). Redfin has prices, not rents.

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

This is the plugin's one market-scoring rubric. `/compare-markets` and the market-researcher agent both use it, so the same markets get the same scores either way. Score each factor 0-100 from the buckets, multiply by the weight, and sum to a 0-100 total.

| Factor | Weight | 100 | 75 | 50 | 25 | Where to get it |
|---|---|---|---|---|---|---|
| Job growth (YoY) | 20% | >3% | 2-3% | 1-2% | <1% | BLS (WebSearch) |
| Population growth (YoY) | 15% | >2% | 1-2% | 0.5-1% | <0.5% | Census estimates (WebSearch) |
| Rent growth (YoY) | 20% | >5% | 3-5% | 1-3% | <1% | Rentcast, Census ACS year over year, or published rent indexes |
| Rental vacancy | 15% | <5% | 5-7% | 7-10% | >10% | Census ACS (`get_census_demographics`), FRED for the national rate |
| Rent-to-price (monthly rent / price) | 15% | >0.8% | 0.6-0.8% | 0.4-0.6% | <0.4% | Redfin median sale price plus Census or Rentcast rent |
| Supply risk | 15% | Low pipeline | Moderate | High | Oversupply | Redfin months of supply and inventory trend, permits (HUD SOCDS) |

Supply-risk guide: months of supply under 3 with flat or falling inventory is low; 3-5 moderate; 5-7 or inventory rising more than 20% year over year is high; above 7 is oversupply. When a factor has no data, score the others, reweight them to 100%, and say which factor is missing.

The national job outlook for context: BLS projects about +5.9 million jobs (+3.5%) for 2025-2035 [BLS Employment Projections, released 2026-08-27].

---

## Data Tools

The plugin's `real-estate-data` server wraps these providers, so call its tools rather than writing HTTP code. Tool names appear in Claude Code as `mcp__plugin_real-estate-investment_real-estate-data__<tool>`.

| Provider | Tool(s) | Key | Gives |
|---|---|---|---|
| Redfin Data Center | `get_redfin_market_snapshot`, `get_redfin_market_data` | none | Monthly median sale price (and YoY), $/sq ft, homes sold, new listings, inventory, months of supply, days on market, sale-to-list, for national, state, metro, county, city or ZIP. Pass several regions separated by " \| " in one call. No rents. |
| Census ACS | `get_census_demographics`, `get_census_housing_stats` | `CENSUS_API_KEY` (free) | Population, median income, median gross rent, vacancy, tenure, median home value, housing age. Takes FIPS codes; look them up first if needed. |
| FRED | `get_fred_series` | `FRED_API_KEY` (free) | Mortgage rates (`MORTGAGE30US`), Treasury yields (`DGS10`), national rental vacancy (`RRVRUSQ156N`), any other FRED series |
| Rentcast | `estimate_rent`, `get_rentcast_market_data` | `RENTCAST_API_KEY` (50 free calls a month, then billed; the server stops at 50 unless the user opts in) | Property rent estimate with range and comps; ZIP listing statistics |
| ATTOM | `get_attom_property`, `get_attom_valuation` | `ATTOM_API_KEY` (paid) | Property facts; AVM value with range and confidence score |
| Mashvisor | `get_mashvisor_property`, `get_mashvisor_neighborhood` | `MASHVISOR_API_KEY` (paid) | Property record; neighborhood overview by ID |
| AirDNA | `get_airdna_rentalizer`, `get_airdna_market_stats` | `AIRDNA_API_KEY` (paid, via AirDNA sales) | STR revenue estimate; market occupancy, ADR and revenue |

The ATTOM, Mashvisor and AirDNA tools follow the providers' docs but are untested against live keys, so check the raw fields they return. When a tool reports a missing key, fall back to WebSearch for the same figure and cite the page you used.

Other free sources worth a search: Zillow Observed Rent Index (ZORI) for rent growth, HUD SOCDS for building permits, BLS for metro employment.

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

**Scoring Model** (for neighborhoods within one metro; compare whole metros with the rubric in §Weighted Scoring Model):
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
