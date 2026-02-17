# Advanced Analysis — Sensitivity, Monte Carlo & Waterfalls

**Table of Contents**
- [1. Sensitivity Analysis](#1-sensitivity-analysis)
- [2. Monte Carlo Simulation](#2-monte-carlo-simulation)
- [3. Waterfall Distribution Modeling](#3-waterfall-distribution-modeling)
- [4. Syndication Return Calculations](#4-syndication-return-calculations)

---

## 1. Sensitivity Analysis

### Key Variables to Stress Test

**Interest Rates & Financing:**
- Rate fluctuations affect financing costs and valuations
- Test different debt/equity combinations

**Rental Income & Occupancy:**
- Vacancy rates and occupancy thresholds
- Rent growth rates and lease rollover timing

**Property Values & Market Conditions:**
- Exit cap rate (typically most impactful variable)
- Market value fluctuations and economic cycles

**Operating Expenses:**
- Management fees, utilities, maintenance
- Insurance and property taxes

**Capital Expenditures:**
- Renovation costs, major systems replacement
- Tenant improvement allowances

### Three-Scenario Framework

| Variable | Bear Case | Base Case | Bull Case |
|----------|-----------|-----------|-----------|
| Rent Growth | 1-2% | 3% | 4-5% |
| Vacancy | 15-20% | 8-10% | 5% |
| Exit Cap Rate | +50-100 bps | Market | -50 bps |
| Interest Rate | +100 bps | Current | -50 bps |
| OpEx Growth | 4-5% | 3% | 2% |

### Tornado Diagram Methodology

1. Identify 6-10 key input variables
2. Determine low, base, and high values for each
3. Run model varying one variable at a time (hold others constant)
4. Calculate range of output values (IRR or NPV)
5. Sort by total range (high - low) in descending order
6. Plot as horizontal bars showing swing from low to high

**Interpretation:**
- Longer bar = higher sensitivity
- Top variables require most careful validation
- Prioritize due diligence on high-impact assumptions

### Break-Even Calculations

**Break-Even Occupancy:**
```
Break-Even Occupancy = (Operating Expenses + Debt Service) / Potential Gross Income
```

**Example:**
```
Operating Expenses: $800,000
Annual Debt Service: $1,000,000
Potential Gross Income: $2,500,000

Break-Even = ($800,000 + $1,000,000) / $2,500,000 = 72%
```

**Industry Standards:**
- Most commercial properties: 60-80%
- Lender requirement: ≤85%
- Lower break-even = larger financial cushion

### Python: Basic Sensitivity Analysis

```python
import pandas as pd
import numpy as np

def calculate_irr(rent_growth, vacancy_rate, exit_cap):
    """Simplified IRR calculation (replace with full DCF)"""
    base_irr = 0.12
    irr = base_irr + (rent_growth - 0.03) * 0.5 + (0.10 - vacancy_rate) * 0.3 - (exit_cap - 0.05) * 2
    return irr

# Define variable ranges
variables = {
    'rent_growth': np.arange(0.01, 0.06, 0.01),
    'vacancy_rate': np.arange(0.05, 0.21, 0.03),
    'exit_cap': np.arange(0.04, 0.08, 0.01)
}

# Base case values
base_case = {
    'rent_growth': 0.03,
    'vacancy_rate': 0.10,
    'exit_cap': 0.05
}

# One-way sensitivity analysis
results = []
for var_name, var_range in variables.items():
    for value in var_range:
        params = base_case.copy()
        params[var_name] = value
        irr = calculate_irr(**params)
        results.append({
            'variable': var_name,
            'value': value,
            'irr': irr
        })

df_sensitivity = pd.DataFrame(results)

# Calculate ranges for tornado diagram
tornado_data = df_sensitivity.groupby('variable')['irr'].agg(['min', 'max'])
tornado_data['range'] = tornado_data['max'] - tornado_data['min']
tornado_data = tornado_data.sort_values('range', ascending=False)
print(tornado_data)
```

### Python: Two-Way Sensitivity Table

```python
import pandas as pd
import numpy as np

def calculate_npv(exit_cap, rent_growth):
    base_npv = 5000000
    npv = base_npv - (exit_cap - 0.05) * 10000000 + (rent_growth - 0.03) * 8000000
    return npv

# Create two-way table
exit_caps = np.arange(0.04, 0.08, 0.005)
rent_growths = np.arange(0.01, 0.06, 0.005)

sensitivity_table = pd.DataFrame(
    [[calculate_npv(cap, growth) for growth in rent_growths] for cap in exit_caps],
    index=exit_caps,
    columns=rent_growths
)

# Format as millions
print("NPV Sensitivity Table ($ Millions)")
print((sensitivity_table / 1000000).round(2))
```

### Python: Scenario Analysis

```python
import pandas as pd
import numpy as np

def dcf_model(purchase_price, noi_year1, rent_growth, exit_cap, hold_period=5):
    cash_flows = [-purchase_price]

    # Project NOI
    for year in range(1, hold_period + 1):
        noi = noi_year1 * ((1 + rent_growth) ** year)
        cash_flows.append(noi)

    # Add terminal value
    terminal_noi = cash_flows[-1] * (1 + rent_growth)
    terminal_value = terminal_noi / exit_cap
    cash_flows[-1] += terminal_value

    # Calculate metrics
    irr = np.irr(cash_flows)
    npv = sum([cf / ((1 + 0.10) ** i) for i, cf in enumerate(cash_flows)])

    return {'IRR': irr, 'NPV': npv, 'Terminal Value': terminal_value}

# Define scenarios
scenarios = {
    'Bear Case': {'purchase_price': 50000000, 'noi_year1': 3000000, 'rent_growth': 0.02, 'exit_cap': 0.065},
    'Base Case': {'purchase_price': 50000000, 'noi_year1': 3500000, 'rent_growth': 0.03, 'exit_cap': 0.055},
    'Bull Case': {'purchase_price': 50000000, 'noi_year1': 4000000, 'rent_growth': 0.045, 'exit_cap': 0.048}
}

# Run scenarios
results = {name: dcf_model(**params) for name, params in scenarios.items()}
df_scenarios = pd.DataFrame(results).T
print(df_scenarios)
```

### Python: Break-Even Analysis

```python
def calculate_breakeven_occupancy(operating_expenses, debt_service, potential_gross_income):
    return (operating_expenses + debt_service) / potential_gross_income

# Example
op_ex = 800000
debt_service = 1000000
pgi = 2500000

beo = calculate_breakeven_occupancy(op_ex, debt_service, pgi)
print(f"Break-Even Occupancy: {beo:.1%}")

# Sensitivity on break-even
debt_scenarios = np.arange(800000, 1300000, 100000)
for ds in debt_scenarios:
    beo = calculate_breakeven_occupancy(op_ex, ds, pgi)
    print(f"Debt Service ${ds:,.0f}: Break-Even = {beo:.1%}")
```

---

## 2. Monte Carlo Simulation

### Why Monte Carlo for Real Estate

**Advantages:**
- Incorporates uncertainty through probability distributions
- Calculates likelihood of meeting return thresholds
- Quantifies downside risk (VaR, percentiles)
- Research shows NPV estimates can differ $500K+ from static models

**Limitations:**
- Requires sophisticated modeling skills
- Needs quality historical data for distributions
- "Garbage in, garbage out"

### Variables to Randomize

Based on Cornell research, model these eight variables stochastically:

1. Rent growth rate (most critical)
2. Other income growth rate
3. Operating expense growth rate
4. Capital expenditures growth rate
5. Releasing costs growth rate
6. Terminal cap rate (highest impact on IRR)
7. Days vacant between leases
8. Renewal probability

### Distribution Selection Guide

**Normal Distribution:**
- **Use for:** Variables with symmetric uncertainty
- **Parameters:** Mean (μ), standard deviation (σ)
- **Applications:** Rent growth (μ=3%, σ=2%), property appreciation, OpEx growth
- **Caution:** Can generate impossible values (e.g., negative rents)

**Triangular Distribution:**
- **Use for:** Limited data but expert judgment available
- **Parameters:** Minimum, most likely (mode), maximum
- **Applications:** Cap rates (min=4%, mode=5.5%, max=7%), construction costs, lease-up periods
- **Benefits:** Intuitive, prevents extreme outliers, easy to explain

**Log-Normal Distribution:**
- **Use for:** Variables that cannot be negative with right-skewed distributions
- **Parameters:** Mean and std dev of natural log
- **Applications:** Property values, extreme market movements
- **Benefits:** Realistic for financial variables, prevents negative values

**Uniform Distribution:**
- **Use for:** True randomness within a range
- **Applications:** Rarely used in real estate; perhaps timing variables

### Determining Distribution Parameters

```python
import numpy as np

# Historical rent growth data
historical_rent_growth = np.array([0.025, 0.032, 0.028, 0.041, 0.019,
                                   0.035, 0.027, 0.038, 0.022, 0.031])

# Normal distribution parameters
mean_growth = np.mean(historical_rent_growth)
std_growth = np.std(historical_rent_growth, ddof=1)  # Sample std dev

print(f"Normal: Mean={mean_growth:.2%}, Std={std_growth:.2%}")

# Triangular distribution parameters
min_growth = np.min(historical_rent_growth)
max_growth = np.max(historical_rent_growth)
mode_growth = historical_rent_growth[np.argmax(np.histogram(historical_rent_growth, bins=5)[0])]

print(f"Triangular: Min={min_growth:.2%}, Mode={mode_growth:.2%}, Max={max_growth:.2%}")
```

**Common Benchmarks:**
- Rent Growth: Mean=3%, Std=2%
- Property Appreciation: Mean=3%, varies by market
- Vacancy Rates: Property-specific, 5-15% range
- Cap Rates: Vary by type; multifamily typically 4-7%

### Python: Monte Carlo Framework

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)
n_simulations = 10000

# Model parameters
purchase_price = 50000000
hold_period = 5

# Distribution parameters
rent_growth_mean = 0.03
rent_growth_std = 0.02
exit_cap_min = 0.045
exit_cap_mode = 0.055
exit_cap_max = 0.070
vacancy_mean = 0.08
vacancy_std = 0.03

irr_results = []
npv_results = []

for i in range(n_simulations):
    # Sample variables
    rent_growth = np.random.normal(rent_growth_mean, rent_growth_std)
    exit_cap = np.random.triangular(exit_cap_min, exit_cap_mode, exit_cap_max)
    vacancy = np.random.normal(vacancy_mean, vacancy_std)

    # Constrain to realistic bounds
    rent_growth = np.clip(rent_growth, -0.05, 0.15)
    vacancy = np.clip(vacancy, 0.02, 0.30)

    # Cash flow projection
    year_1_noi = 3500000 * (1 - vacancy)
    cash_flows = [-purchase_price]

    for year in range(1, hold_period + 1):
        noi = year_1_noi * ((1 + rent_growth) ** year)
        cash_flows.append(noi)

    # Terminal value
    terminal_noi = cash_flows[-1] * (1 + rent_growth)
    terminal_value = terminal_noi / exit_cap
    cash_flows[-1] += terminal_value

    # Calculate metrics
    irr = np.irr(cash_flows)
    npv = np.npv(0.10, cash_flows)

    irr_results.append(irr)
    npv_results.append(npv)

irr_results = np.array(irr_results)
npv_results = np.array(npv_results)

# Summary statistics
print("=== MONTE CARLO SIMULATION RESULTS ===")
print(f"Simulations: {n_simulations:,}")
print(f"\nIRR Statistics:")
print(f"  Mean: {np.mean(irr_results):.2%}")
print(f"  Median: {np.median(irr_results):.2%}")
print(f"  Std Dev: {np.std(irr_results):.2%}")
print(f"  5th Percentile: {np.percentile(irr_results, 5):.2%}")
print(f"  95th Percentile: {np.percentile(irr_results, 95):.2%}")

print(f"\nNPV Statistics:")
print(f"  Mean: ${np.mean(npv_results):,.0f}")
print(f"  5th Percentile: ${np.percentile(npv_results, 5):,.0f}")
print(f"  95th Percentile: ${np.percentile(npv_results, 95):,.0f}")

# Probability of meeting targets
target_irr = 0.12
prob_exceed = np.sum(irr_results >= target_irr) / n_simulations
print(f"\nP(IRR >= {target_irr:.0%}): {prob_exceed:.1%}")

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(irr_results, bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(np.mean(irr_results), color='red', linestyle='--', label=f'Mean: {np.mean(irr_results):.2%}')
axes[0].axvline(target_irr, color='green', linestyle='--', label=f'Target: {target_irr:.0%}')
axes[0].set_xlabel('IRR')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Distribution of IRR Outcomes')
axes[0].legend()

axes[1].hist(npv_results / 1000000, bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(np.mean(npv_results) / 1000000, color='red', linestyle='--')
axes[1].set_xlabel('NPV ($ Millions)')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Distribution of NPV Outcomes')

plt.tight_layout()
plt.savefig('monte_carlo_results.png', dpi=300)
```

### Python: Correlated Variables

```python
import numpy as np

# Define correlation matrix (e.g., rent growth vs exit cap)
correlation_matrix = np.array([
    [1.00, -0.50],  # Negative correlation
    [-0.50, 1.00]
])

# Generate correlated samples
n_sims = 10000
mean = [0, 0]
samples = np.random.multivariate_normal(mean, correlation_matrix, n_sims)

# Transform to desired distributions
rent_growth = 0.03 + samples[:, 0] * 0.02  # Mean 3%, std 2%
exit_cap = 0.055 + samples[:, 1] * 0.01     # Mean 5.5%, std 1%

print(f"Correlation: {np.corrcoef(rent_growth, exit_cap)[0, 1]:.2f}")
```

### Output Interpretation

**Key Metrics:**
- **Expected Value (Mean):** Average outcome across simulations
- **Median:** 50th percentile
- **Standard Deviation:** Volatility/risk measure
- **5th Percentile:** 5% chance of worse outcome (downside risk)
- **95th Percentile:** Upside potential

**Value at Risk (VaR):**

```python
# 5% VaR
var_5 = np.percentile(npv_results, 5)
print(f"5% VaR: ${var_5:,.0f}")
print(f"Interpretation: 5% chance NPV ≤ ${var_5:,.0f}")

# Probability of loss
prob_loss = np.sum(npv_results < 0) / len(npv_results)
print(f"P(NPV < 0): {prob_loss:.1%}")
```

**IRR Target Probabilities:**

```python
targets = [0.08, 0.10, 0.12, 0.15, 0.18]

print("IRR Target Probabilities:")
for target in targets:
    prob = np.sum(irr_results >= target) / len(irr_results)
    print(f"  P(IRR >= {target:.0%}): {prob:.1%}")
```

### Iteration Count Guidelines

- **Minimum:** 1,000 iterations for basic analysis
- **Recommended:** 5,000-10,000 iterations for robust results
- **Complex Models:** 10,000+ when modeling many variables

**Test for Convergence:**
```python
# Run multiple iteration counts and check stability
iteration_counts = [100, 500, 1000, 5000, 10000]
means = []

for n in iteration_counts:
    temp_results = [run_simulation() for _ in range(n)]
    means.append(np.mean(temp_results))

print("Mean IRR by Iteration Count:")
for n, m in zip(iteration_counts, means):
    print(f"{n:>6,} iterations: {m:.4%}")
```

Results converge when increasing iterations no longer changes mean/distribution.

---

## 3. Waterfall Distribution Modeling

### Overview

Waterfall distribution structures determine how profits split between GPs (sponsors) and LPs (investors) through sequential tiers. Cash "cascades" through tiers—each must be filled before flowing to the next.

**Purpose:**
- Align GP and LP interests
- Incentivize sponsor performance through "promote"
- Provide downside protection via preferred returns
- Create clear distribution priorities

### Typical 4-Tier Structure

**Tier 1: Return of Capital + Preferred Return**
- 100% to LPs
- First: Return original investment
- Then: Preferred return (typically 7-10%, most commonly 8%)
- No GP distributions until satisfied

**Tier 2: GP Catch-Up**
- Often 100% to GP
- Continues until GP receives proportional share of cumulative profits
- "Catches up" GP to agreed promote percentage

**Tier 3: First Promote Split (8-12% IRR Hurdle)**
- Example: 70% LP, 30% GP
- Applies after 8% IRR achieved
- Continues until next hurdle (e.g., 12% IRR)

**Tier 4: Second Promote Split (12-18% IRR Hurdle)**
- Example: 60% LP, 40% GP
- May have additional tiers at 15%, 18%+ IRR

**Common Hurdle Structures:**

| IRR Range | LP Split | GP Split | Description |
|-----------|----------|----------|-------------|
| < 8% | 100% | 0% | Return of capital + pref |
| 8-12% | 80% | 20% | First promote tier |
| 12-15% | 70% | 30% | Second promote tier |
| 15-18% | 65% | 35% | Third promote tier |
| 18%+ | 60% | 40% | Final promote tier |

### American vs European Waterfalls

**American Waterfall (Deal-by-Deal):**
- GP receives carried interest **before** LPs have full capital return
- Calculated at **individual deal/property level**
- More GP-favorable; provides earlier promote access
- Most prevalent in United States

**How it Works:**
1. Property A sells at profit → GP receives promote immediately
2. Property B may still be held or at loss
3. GP receives promote deal-by-deal

**Advantages:** GP receives compensation sooner, enables longer hold periods
**Disadvantages:** LPs may not receive full capital if later deals underperform

**European Waterfall (Whole-Fund):**
- GP receives **no** carried interest until **all** LPs have capital back + pref return
- Calculated at **fund level**, not deal-by-deal
- More LP-favorable; provides downside protection
- Common in European markets

**How it Works:**
1. No promote until entire fund returns all LP capital
2. Only after 100% capital + pref does GP participate in profits
3. Promotes based on aggregate fund performance

**Advantages:** Better LP protection
**Disadvantages:** GP may wait years for promote, incentive to exit early

**Comparison:**

| Feature | American | European |
|---------|----------|----------|
| Promote Timing | Deal-by-deal | After full fund return |
| GP Compensation | Earlier | Later |
| LP Protection | Lower | Higher |
| GP Incentive | Longer holds | Shorter holds |
| Risk to GP | Lower | Higher |

### Catch-Up Provision

**Purpose:** Allow GP to receive 100% of distributions after pref return until GP reaches target promote percentage on cumulative basis.

**Formula:**
```
GP Catch-Up Amount = (Preferred Return × GP Target %) / (1 - GP Target %)
```

**Example:**
For $2M pref return and 20% target promote:
```
Catch-Up = $2,000,000 × 0.20 / (1 - 0.20) = $500,000
```

**Cash Flow Distribution Example:**
- Total: $10,000,000
- Tier 1 (Pref): $2,000,000 to LPs (100%)
- Tier 2 (Catch-Up): $500,000 to GP (100%)
- Tier 3: $7,500,000 split 80/20
- **Final GP:** $500K + $1,500K = $2,000K = **20%** of total

### Clawback and Lookback Provisions

**Clawback:**
Protection allowing LPs to recoup excess promote if fund fails to meet return thresholds at liquidation.

**How it Works:**
1. Year 3: Property sells at 15% IRR, GP receives 30% promote
2. Year 5: Fund liquidates at 10% overall IRR
3. At 10% IRR, GP only entitled to 20% promote
4. GP must return excess promote to LPs

**Lookback:**
Re-evaluates GP compensation at end of investment period to ensure it matches actual achieved returns.

**Example:**
- Projected IRR at sale: 15% → GP receives 30%
- Actual fund IRR at liquidation: 11% → GP entitled to 20%
- Lookback requires GP to return 10% difference

### Preferred Return: Cumulative vs Non-Cumulative

**Cumulative (Most Common):**
- Unpaid pref from prior periods **accrues** and carries forward
- Must be paid in future periods before other distributions

**Example:**
- 8% annual pref on $10M = $800K/year
- Year 1: Only $400K distributed
- Year 2: Must distribute $1,200K ($800K Year 2 + $400K shortfall)

**Non-Cumulative (Rare):**
- Pref "resets" each period
- Unpaid amounts do not carry forward
- Much less favorable to LPs

### Simple vs Compound Interest

**Simple Interest (Most Common):**
- Unpaid pref accrues but does **not compound**
- Calculated on original capital only

**Example:**
- $10M, 8% simple pref
- Year 1: $0 distributed (owe $800K)
- Year 2: $0 distributed (owe $1,600K total)
- Unpaid pref does not earn additional pref

**Compound Interest:**
- Unpaid pref added to capital balance
- Future pref calculated on capital + unpaid pref

**Example:**
- $10M, 8% compound pref
- Year 1: $0 distributed (owe $800K)
- Year 2 balance: $10.8M
- Year 2 pref: $10.8M × 8% = $864K
- Total owed: $1,664K

**Impact Comparison (5 years, no distributions):**

| Structure | Year 5 Total Owed |
|-----------|-------------------|
| Non-Cumulative | $800,000 |
| Cumulative, Simple | $4,000,000 |
| Cumulative, Compound | $4,693,000 |

### Python: Waterfall Calculator with IRR Hurdles

```python
import numpy as np
import numpy_financial as npf

def calculate_waterfall_irr(
    lp_capital,
    gp_capital,
    cash_flows,
    pref_rate=0.08,
    hurdles=[0.08, 0.12, 0.18],
    lp_splits=[0.80, 0.70, 0.60],
    use_catchup=True
):
    """
    Calculate waterfall distributions with IRR hurdles.

    Returns: dict with distribution amounts for LP and GP
    """
    total_capital = lp_capital + gp_capital
    total_distributions = sum(cash_flows)

    # Calculate project IRR
    investment_cf = [-total_capital] + cash_flows
    project_irr = npf.irr(investment_cf)

    lp_distributions = 0
    gp_distributions = 0
    remaining_cash = total_distributions

    # Tier 1: Return of Capital
    if remaining_cash >= total_capital:
        lp_distributions += lp_capital
        gp_distributions += gp_capital
        remaining_cash -= total_capital
        print(f"Tier 1 - Return of Capital:")
        print(f"  LP: ${lp_capital:,.0f}, GP: ${gp_capital:,.0f}")
        print(f"  Remaining: ${remaining_cash:,.0f}\n")
    else:
        # Pro-rata return
        lp_distributions = remaining_cash * (lp_capital / total_capital)
        gp_distributions = remaining_cash * (gp_capital / total_capital)
        remaining_cash = 0
        return {'lp_total': lp_distributions, 'gp_total': gp_distributions, 'project_irr': -1}

    # Tier 2: Preferred Return
    pref_amount = lp_capital * pref_rate * len(cash_flows)  # Simplified cumulative
    if remaining_cash >= pref_amount:
        lp_distributions += pref_amount
        remaining_cash -= pref_amount
        print(f"Tier 2 - Preferred Return ({pref_rate:.0%}):")
        print(f"  LP: ${pref_amount:,.0f}")
        print(f"  Remaining: ${remaining_cash:,.0f}\n")
    else:
        lp_distributions += remaining_cash
        remaining_cash = 0
        return {'lp_total': lp_distributions, 'gp_total': gp_distributions, 'project_irr': project_irr}

    # Tier 3: GP Catch-Up
    if use_catchup and remaining_cash > 0:
        first_promote = 1 - lp_splits[0]
        total_tier_1_2 = total_capital + pref_amount
        catchup_target = total_tier_1_2 * first_promote / (1 - first_promote)
        catchup_amount = min(catchup_target, remaining_cash)

        gp_distributions += catchup_amount
        remaining_cash -= catchup_amount
        print(f"Tier 3 - GP Catch-Up:")
        print(f"  GP: ${catchup_amount:,.0f}")
        print(f"  Remaining: ${remaining_cash:,.0f}\n")

    # Tier 4+: Promote Tiers
    tier_num = 4
    for i, hurdle in enumerate(hurdles):
        if project_irr >= hurdle and remaining_cash > 0:
            lp_split = lp_splits[i]
            gp_split = 1 - lp_split

            tier_lp = remaining_cash * lp_split
            tier_gp = remaining_cash * gp_split

            lp_distributions += tier_lp
            gp_distributions += tier_gp
            remaining_cash -= (tier_lp + tier_gp)

            print(f"Tier {tier_num} - {hurdle:.0%} IRR Hurdle (LP:{lp_split:.0%}, GP:{gp_split:.0%}):")
            print(f"  LP: ${tier_lp:,.0f}, GP: ${tier_gp:,.0f}\n")
            tier_num += 1
            break

    # Calculate IRRs
    lp_irr = npf.irr([-lp_capital, lp_distributions])
    gp_irr = npf.irr([-gp_capital, gp_distributions]) if gp_capital > 0 else 0

    return {
        'project_irr': project_irr,
        'lp_total': lp_distributions,
        'gp_total': gp_distributions,
        'lp_irr': lp_irr,
        'gp_irr': gp_irr,
        'lp_percent': lp_distributions / total_distributions,
        'gp_percent': gp_distributions / total_distributions
    }

# Example usage
results = calculate_waterfall_irr(
    lp_capital=10000000,
    gp_capital=0,
    cash_flows=[0, 0, 0, 0, 15000000],
    pref_rate=0.08,
    hurdles=[0.08, 0.12, 0.18],
    lp_splits=[0.80, 0.70, 0.60],
    use_catchup=True
)

print("=" * 50)
print("WATERFALL SUMMARY")
print("=" * 50)
print(f"Project IRR: {results['project_irr']:.2%}")
print(f"LP: ${results['lp_total']:,.0f} ({results['lp_percent']:.1%}), IRR: {results['lp_irr']:.2%}")
print(f"GP: ${results['gp_total']:,.0f} ({results['gp_percent']:.1%}), IRR: {results['gp_irr']:.2%}")
```

### Python: Simplified Waterfall

```python
def simple_waterfall(total_proceeds, lp_capital, pref_rate=0.08, promote=0.20):
    """Simplified waterfall with pref return and single promote tier."""
    distributions = {
        'lp': {'return_of_capital': 0, 'pref_return': 0, 'profit_split': 0, 'total': 0},
        'gp': {'catchup': 0, 'profit_split': 0, 'total': 0}
    }

    remaining = total_proceeds

    # Tier 1: Return of capital
    distributions['lp']['return_of_capital'] = min(lp_capital, remaining)
    remaining -= distributions['lp']['return_of_capital']

    if remaining <= 0:
        distributions['lp']['total'] = distributions['lp']['return_of_capital']
        return distributions

    # Tier 2: Preferred return
    pref_amount = lp_capital * pref_rate
    distributions['lp']['pref_return'] = min(pref_amount, remaining)
    remaining -= distributions['lp']['pref_return']

    if remaining <= 0:
        distributions['lp']['total'] = sum(distributions['lp'].values())
        return distributions

    # Tier 3: GP catch-up
    total_tier_1_2 = distributions['lp']['return_of_capital'] + distributions['lp']['pref_return']
    catchup_amount = total_tier_1_2 * promote / (1 - promote)
    distributions['gp']['catchup'] = min(catchup_amount, remaining)
    remaining -= distributions['gp']['catchup']

    # Tier 4: Remaining split
    distributions['lp']['profit_split'] = remaining * (1 - promote)
    distributions['gp']['profit_split'] = remaining * promote

    # Totals
    distributions['lp']['total'] = sum(distributions['lp'].values())
    distributions['gp']['total'] = sum(distributions['gp'].values())

    return distributions

# Example
result = simple_waterfall(total_proceeds=15000000, lp_capital=10000000, pref_rate=0.08, promote=0.20)

print("LP Distributions:")
for key, value in result['lp'].items():
    print(f"  {key}: ${value:,.0f}")

print("\nGP Distributions:")
for key, value in result['gp'].items():
    print(f"  {key}: ${value:,.0f}")

print(f"\nGP Promote: {result['gp']['total'] / (result['lp']['total'] + result['gp']['total']):.1%}")
```

---

## 4. Syndication Return Calculations

### LP vs GP Splits

**Typical Ownership:**
- **LPs:** Provide 90-95% of equity
- **GPs:** Provide 5-10% of equity (sometimes 0%)

**Distribution Priorities:**

| Tier | Description | LP Split | GP Split |
|------|-------------|----------|----------|
| 1 | Return of Capital | Pro-rata | Pro-rata |
| 2 | Preferred Return | 100% | 0% |
| 3 | GP Catch-Up | 0% | 100% |
| 4 | 8-12% IRR | 80% | 20% |
| 5 | 12%+ IRR | 70% | 30% |

**Example ($15M total distribution):**

| Tier | Amount | LP | GP |
|------|--------|----|----|
| Return of Capital | $10M | $10M | $0 |
| Pref Return 8% | $800K | $800K | $0 |
| GP Catch-Up | $200K | $0 | $200K |
| 8-12% IRR | $2M | $1.6M | $400K |
| 12%+ IRR | $2M | $1.4M | $600K |
| **Total** | **$15M** | **$13.8M (92%)** | **$1.2M (8%)** |

### Promote/Carried Interest

**What is a Promote?**
Performance-based compensation earned by GP beyond pro-rata ownership share.

**Common Structures:**

1. **Straight Promote:** All cash flow split per percentages (e.g., 70/30)
2. **Single Hurdle:** 100% to LPs until 8% pref, then 80/20
3. **Multi-Tier IRR Hurdles:**
   - 8% IRR: 80/20
   - 12% IRR: 70/30
   - 15% IRR: 65/35
   - 18% IRR: 60/40

**Total GP Compensation:**
```
Total GP Return = (GP Capital / Total Capital) × Distributions + Promote
```

**Example:**
- Sale Proceeds: $15M
- LP Capital: $9.5M (95%), GP Capital: $500K (5%)
- Pref Return: 8% ($760K to LPs)
- Promote: 20% after pref

**Calculation:**
1. Return of Capital: LP $9.5M, GP $500K
2. Pref to LPs: $760K
3. Remaining: $15M - $10M - $760K = $4,240K
4. Split 80/20: LP $3,392K, GP $848K
5. **Total GP:** $500K + $848K = $1,348K (9% of total)
6. **Promote premium:** 9% - 5% = 4%

**Promote Ranges:**
- **Standard deals:** 20%
- **Value-add/opportunistic:** 25-30%
- **Development/high-risk:** 30-40%

### Capital Account Tracking

**Formula:**
```
Ending Capital Account = Beginning Balance
                        + Capital Contributions
                        + Allocated Income
                        - Allocated Losses
                        - Distributions
```

**Example Tracking:**

| Period | Contributions | Allocated Income | Distributions | Ending Balance |
|--------|--------------|-----------------|--------------|----------------|
| Year 0 | $1,000,000 | $0 | $0 | $1,000,000 |
| Year 1 | $0 | $50,000 | -$30,000 | $1,020,000 |
| Year 2 | $0 | $75,000 | -$40,000 | $1,055,000 |
| Year 3 | $0 | $100,000 | -$50,000 | $1,105,000 |
| Year 4 | $0 | -$20,000 | -$40,000 | $1,045,000 |
| Year 5 | $0 | $500,000 | -$1,545,000 | $0 |

**Python Implementation:**

```python
import pandas as pd

class CapitalAccount:
    def __init__(self, partner_name, initial_contribution):
        self.partner_name = partner_name
        self.balance = initial_contribution
        self.transactions = [{
            'year': 0,
            'type': 'contribution',
            'amount': initial_contribution,
            'balance': initial_contribution
        }]

    def add_contribution(self, year, amount):
        self.balance += amount
        self.transactions.append({'year': year, 'type': 'contribution', 'amount': amount, 'balance': self.balance})

    def allocate_income(self, year, amount):
        self.balance += amount
        self.transactions.append({'year': year, 'type': 'income', 'amount': amount, 'balance': self.balance})

    def record_distribution(self, year, amount):
        self.balance -= amount
        self.transactions.append({'year': year, 'type': 'distribution', 'amount': amount, 'balance': self.balance})

    def get_balance(self):
        return self.balance

    def get_statement(self):
        return pd.DataFrame(self.transactions)

# Example
lp_account = CapitalAccount('LP-001', 1000000)
lp_account.allocate_income(1, 50000)
lp_account.record_distribution(1, 30000)
lp_account.allocate_income(2, 75000)
lp_account.record_distribution(2, 40000)

print(lp_account.get_statement())
print(f"\nBalance: ${lp_account.get_balance():,.0f}")
```

**Why Capital Accounts Matter:**
1. Tax reporting (K-1 allocations)
2. Distribution rights in liquidation
3. Regulatory compliance (IRS Form 1065)
4. Investor transparency
5. Prevent negative balances (clawback risk)

### Distribution Timing

**Frequency:**

- **Monthly:** Stabilized assets (multifamily, retail), requires consistent NOI
- **Quarterly:** Most common for syndications, balances cash flow and admin burden
- **Annual:** Development/heavy value-add, lower early cash flow
- **Event-Driven:** Upon refinance/sale, common for opportunistic deals

**Timing Considerations:**

1. **Operating Cash Flow:** Must have excess after debt service and reserves
2. **Capital Events:** Refi/sale proceeds distributed 30-90 days after closing
3. **Tax Implications:** K-1 allocations may differ from cash (phantom income risk)
4. **Pref Accrual:** Quarterly distributions → pref accrues quarterly

**Python: Distribution Schedule**

```python
import pandas as pd

class DistributionSchedule:
    def __init__(self, noi_schedule, debt_service, reserve_rate=0.10):
        self.noi_schedule = noi_schedule
        self.debt_service = debt_service
        self.reserve_rate = reserve_rate
        self.distributions = []

    def calculate_distributable_cash(self, period_noi):
        cash_after_debt = period_noi - self.debt_service
        reserves = period_noi * self.reserve_rate
        distributable = cash_after_debt - reserves
        return max(distributable, 0)

    def generate_quarterly_distributions(self, years=5):
        quarters = years * 4

        for q in range(quarters):
            year = q // 4 + 1
            quarter = q % 4 + 1

            annual_noi = self.noi_schedule.get(year, 0)
            quarterly_noi = annual_noi / 4

            dist_cash = self.calculate_distributable_cash(quarterly_noi)

            self.distributions.append({
                'year': year,
                'quarter': quarter,
                'noi': quarterly_noi,
                'debt_service': self.debt_service / 4,
                'reserves': quarterly_noi * self.reserve_rate,
                'distributable_cash': dist_cash
            })

        return pd.DataFrame(self.distributions)

# Example
noi_schedule = {1: 1000000, 2: 1050000, 3: 1100000, 4: 1150000, 5: 1200000}
dist_model = DistributionSchedule(noi_schedule, debt_service=600000, reserve_rate=0.10)
schedule = dist_model.generate_quarterly_distributions(years=5)

print("Quarterly Distribution Schedule:")
print(schedule.head(10))
print(f"\nTotal Distributable (5 years): ${schedule['distributable_cash'].sum():,.0f}")
```

**Best Practices:**
1. Set clear expectations in operating agreement
2. Maintain reserves (never distribute below minimums)
3. Establish consistent timing (e.g., 15th of month after quarter-end)
4. Provide distribution notices with explanations
5. Coordinate year-end distributions with K-1 allocations
