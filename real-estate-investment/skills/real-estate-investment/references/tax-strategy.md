# Tax Strategy & Deal Structuring

**DISCLAIMER**: Educational reference only — not legal or tax advice. Consult qualified professionals before making investment or tax planning decisions.

**Currency**: Checked against IRS guidance in October 2026 (OBBBA as implemented by Notice 2026-11, Notice 2026-16, Notice 2026-40, Rev. Proc. 2025-32 and the 2025 editions of Pubs 925, 544 and 946). Dollar thresholds are indexed every year and rules change, so verify any figure that drives a decision with a current search and state the tax year you used.

## Key Figures (verify for the current tax year)

| Item | 2025 | 2026 | Notes |
|---|---|---|---|
| Bonus depreciation | 100% if acquired after Jan 19, 2025 | 100% | Permanent under OBBBA; keyed to the acquisition (binding written contract) date. Property under contract before Jan 20, 2025 keeps the old phase-down (40% if placed in service in 2025, 20% in 2026). |
| §179 limit / phase-out start | $2.5M / $4M | $2.56M / $4.09M | Limited to active trade-or-business income; generally unavailable for residential rental buildings (lodging exclusion) |
| Excess business loss (§461(l)) | $313K single / $626K joint | $256K / $512K | The 2026 threshold dropped, so large bonus or cost-seg losses hit it sooner |
| Long-term capital gains | 0% / 15% / 20% | 0% up to $49,450 single / $98,900 joint; 20% above $545,500 / $613,700 | Plus 3.8% NIIT above MAGI $200K single / $250K joint (not indexed) |
| Unrecaptured §1250 gain | up to 25% | up to 25% | Straight-line depreciation on buildings only |
| §1245 recapture (cost-seg 5/7/15-year components) | ordinary rates | ordinary rates | Up to 37% |
| QBI (§199A) | 20% | 20%, now permanent; thresholds $201,750 / $403,500 | $400 minimum deduction from 2026 for $1,000+ of QBI with material participation. Rentals qualify only as a trade or business (or under the Rev. Proc. 2019-38 safe harbor). |
| Passive loss allowance | $25K, phased out at MAGI $100K-$150K | same | Not indexed |
| SALT deduction cap | $40,000 | $40,400 | Phases down above $505K MAGI (2026); scheduled to revert to $10K in 2030 |
| Estate and gift exemption | $13.99M | $15M | Indexed from 2027; annual gift exclusion $19,000 (2026) |

---

## Table of Contents

1. [Depreciation Schedules](#depreciation-schedules)
2. [Cost Segregation](#cost-segregation)
3. [1031 Exchange](#1031-exchange)
4. [Bonus Depreciation](#bonus-depreciation)
5. [Opportunity Zones](#opportunity-zones)
6. [Entity Structure](#entity-structure)

---

## Depreciation Schedules

### MACRS Recovery Periods

| Property Type | Recovery Period | Method | Convention |
|--------------|----------------|--------|------------|
| Residential Rental (IRC §168(c)) | 27.5 years | Straight-line | Mid-month |
| Commercial/Nonresidential | 39 years | Straight-line | Mid-month |
| Land | NOT depreciable | N/A | N/A |

**Qualifying Residential**: 80%+ gross rental income from dwelling units (apartments, SFR, duplexes).

### Component Depreciation Classes

| Class | Recovery Period | Depreciation Method | Common Property Types |
|-------|----------------|---------------------|----------------------|
| 5-Year | 5 years | 200% DB | Appliances, carpeting, furniture, computers |
| 7-Year | 7 years | 200% DB | Office furniture/fixtures, machinery/equipment |
| 15-Year | 15 years | 150% DB, half-year | Land improvements (parking, sidewalks, fencing, landscaping) |
| QIP | 15 years | Straight-line, half-year | Qualified improvement property (below) |

**Qualified Improvement Property (QIP)**:
- Interior improvements to nonresidential buildings (excludes structural enlargements, elevators, internal framework). Residential rental buildings don't qualify.
- Must be made by the taxpayer after the building was first placed in service, so it does not come with a purchase: interior improvements a seller made stay part of the 39-year building for the buyer.
- 15-year recovery, straight-line (not 150% DB)
- **Acquired after January 19, 2025**: 100% bonus depreciation eligible; **January 1-19, 2025**: 40%
- An electing real property trade or business under §163(j) must use ADS, which makes QIP ineligible for bonus
- **Section 179** can also apply to QIP (limits in Key Figures above)

### Land vs. Building Allocation

**IRS Standard (Treasury Reg §1.167(a)-5)**: Allocate by fair market value.

**Allocation Methods (IRS preference order):**
1. Professional appraisal (most defensible)
2. County tax assessor allocation (commonly used, not always accurate)
3. Independent FMV analysis (comparables, insurance values, cost approach)

**IRS Scrutiny**: Land <10-15% of total value may trigger audit in urban areas.

### Calculation Examples

**Example 1: Residential Rental**
- Purchase: $550,000 | Land: $100,000 | Building: $450,000
- Annual depreciation: $450,000 ÷ 27.5 = **$16,364/year**
- Year 1 (purchased July): $16,364 × 5.5/12 = **$7,500**

**Example 2: Commercial Property**
- Purchase: $2,000,000 | Land: $300,000 | Building: $1,700,000
- Annual depreciation: $1,700,000 ÷ 39 = **$43,590/year**
- Year 1 (placed in service March): $1,700,000 ÷ 39 × 9.5/12 = **$34,509**

**Example 3: Component Depreciation Impact** (placed in service January)
- Purchase: $1,000,000 residential | Land: $150,000
- With segregation: Building $700,000 (27.5yr), Personal property $100,000 (5yr), Land improvements $50,000 (15yr)

Year 1 depreciation if the owner elects out of bonus:
- Building: $700,000 ÷ 27.5 × 11.5/12 = $24,394
- Personal property: $100,000 × 20% = $20,000 (the MACRS table rate already includes the half-year convention)
- Land improvements: $50,000 × 5% = $2,500
- **Total: $46,894**

Without segregation: $850,000 ÷ 27.5 × 11.5/12 = **$29,621**
**Additional deduction: $17,273**

With 100% bonus (acquired after Jan 19, 2025, the default under current law): $24,394 + $150,000 = **$174,394** in year 1.

---

## Cost Segregation

### Methodology

Engineering-based study reclassifies building components from 27.5/39-year to 5/7/15-year classes.

**Process**:
1. Property analysis (site visit or virtual inspection, review construction documents)
2. Component classification (personal property, land improvements, building structure)
3. IRS-compliant documentation and audit support

### 100% Bonus Depreciation (OBBBA)

**One Big Beautiful Bill Act** (PL 119-21, signed July 4, 2025; Notice 2026-11):
- **100% bonus depreciation is permanent** for qualified property **acquired after January 19, 2025**. The acquisition date (the date of a binding written contract) controls, not the placed-in-service date. There is no 2030 end date.
- Applies to 5/7/15-year property (NOT 27.5/39-year building structure)
- No retroactive relief for 2023-2024 purchases

**Property acquired before January 20, 2025** keeps the prior phase-down: 80% (placed in service 2023), 60% (2024), 40% (2025), 20% (2026), 0% after. A taxpayer can elect 40% instead of 100% for the first tax year ending after January 19, 2025.

### Typical Savings by Property Value

| Property Value | Typical Cost Seg % | Accelerated Depreciation | Tax Savings (37% rate) | Study Cost | ROI |
|----------------|-------------------|-------------------------|----------------------|-----------|-----|
| $1M Commercial | 20-30% | $200K-$300K | $74K-$111K | $8K-$12K | 6x-14x |
| $3M Multifamily | 20-25% | $600K-$750K | $222K-$278K | $20K-$25K | 9x-14x |
| $10M Hotel/Specialty | 30-40% | $3M-$4M | $1.11M-$1.48M | $50K-$75K | 15x-30x |

**Study Cost Ranges**:
- Streamlined: $1,200-$5,000
- Detailed: $5,000-$25,000
- Large/complex: $25,000-$75,000+

**Minimum Thresholds**:
- $250K+: Worthwhile for high-income investors (especially STRs, because of the 7-day exception under Passive Activity Loss Rules below)
- $500K+: Generally recommended
- $750K+: Engineering-based study typically justified

### Worked Example: $1M Commercial Property (purchased July 2025)

**Land**: $150,000 | **Depreciable basis**: $850,000

**Without Cost Segregation**:
- $850,000 ÷ 39 years × 5.5/12 = **$9,989** Year 1

**With Cost Segregation**:
- Building (39yr): $600,000 → $600,000 ÷ 39 × 5.5/12 = $7,051 (includes $50,000 of interior improvements the seller made; they aren't QIP to a buyer)
- Personal property (5yr): $150,000 → 100% bonus = $150,000
- Land improvements (15yr): $100,000 → 100% bonus = $100,000
- **Total Year 1: $257,051**

**Year-1 deduction value**:
- Additional depreciation: $247,062
- At 37% rate: **$91,413**
- At 24% rate: **$59,295**

The deduction is only worth this if the investor can use it this year (see Passive Activity Loss Rules below), and the accelerated portion is recaptured at ordinary rates on a sale (see Depreciation Recapture).

### When Cost Segregation Makes Sense

**Ideal Candidates**:
- Commercial $750K+, multifamily $500K+
- Recent purchases (current tax year)
- Properties with high personal property content (hotels, restaurants, medical)
- High-income investors who can utilize losses
- Active business participants (not purely passive)

**Consider Carefully**:
- Properties <$250K (cost may exceed benefit)
- Purchases many years ago (fewer remaining years)
- Passive investors subject to PAL limitations
- Properties planned for near-term sale: depreciation on the 5/7/15-year components is §1245 recapture, taxed at ordinary rates rather than the 25% cap (see Depreciation Recapture)

**Timing**: Can apply retroactively via Form 3115 (change in accounting method).

### Interaction with Passive Activity Loss Rules

**Critical Limitation**: Accelerated depreciation only valuable if you can **use** deductions.

**Real Estate Professional Status** (see Entity Structure section):
- If qualified and materially participating: rental losses NOT passive
- Can fully utilize cost seg deductions against ordinary income
- Without status: passive losses limited to $25K offset (phased out by MAGI $100K-$150K)

**Short-term rental exception**: an activity whose average customer stay is 7 days or less isn't a "rental activity" under §469. If the owner materially participates (for example, 100+ hours and more than anyone else, documented in a time log), its losses, including cost-seg and bonus losses, are non-passive without real estate professional status. This is the main reason cost seg is popular with STR owners. STRs with hotel-like services report on Schedule C and owe self-employment tax.

**Excess Business Loss Limitation (IRC §461(l))**:
- 2025 threshold: $313K (single) / $626K (joint); 2026: $256K / $512K
- Bonus depreciation can trigger limitation
- Consider electing out of bonus for a class (or spreading QIP straight-line) if near the threshold

---

## 1031 Exchange

### Like-Kind Requirements (IRC §1031)

**Post-2017 TCJA**: Real property only (personal property excluded).

**Broad Definition**:
- Apartment → office ✓
- Raw land → retail ✓
- SFR rental → industrial warehouse ✓
- U.S. property only (foreign property NOT like-kind)

**Excluded Property**:
- Primary residence (unless partial investment use per Rev Proc 2005-14)
- Property held for sale (inventory, flips)
- Stocks, bonds, partnership interests

**Use Requirement**: Both properties held for investment/business (intent matters).

### Timeline Requirements

```
Day 0: Close on Relinquished Property
  ↓
Day 45: Identification Deadline (strict; only IRS disaster-relief postponements extend it)
  ↓
Day 180: Exchange Completion Deadline
         OR Tax Return Due Date (whichever is earlier)
```

**45-Day Identification Rules**:
- **3-Property Rule**: Identify up to 3 properties (any value)
- **200% Rule**: Unlimited properties, total FMV ≤200% of relinquished value
- **95% Rule**: Unlimited properties/value, must acquire 95% of identified value

**180-Day Exchange Period**:
- Runs concurrently with 45-day (not in addition)
- Must close by earlier of: (a) 180 days after sale, OR (b) tax return due date (with extensions)

**Critical Example** (Q4 2025 sale):
- Sell: November 1, 2025
- 45-day deadline: December 16, 2025
- 180-day deadline: April 30, 2026
- Tax return due (no extension): April 15, 2026
- **Actual deadline: April 15, 2026** (file extension for full 180 days)

### Boot Calculation

**Boot** = non-like-kind property received (cash, debt relief, personal property). Boot is **taxable**.

**Formula**:
```
Taxable Boot = Cash Boot + Mortgage Boot
Mortgage Boot = MAX(0, Debt Relinquished - Debt Replacement - Cash Added)
```

**Examples**:

| Scenario | Relinquished | Replacement | Boot | Tax Impact |
|----------|--------------|-------------|------|------------|
| Trade down, cash out | $1M value, $300K debt ($700K equity) | $900K value, $250K debt ($650K equity) | $50K cash + $50K mortgage = $100K | $100K taxable |
| Trade down, all equity reinvested | $1M value, $400K debt ($600K equity) | $950K value, $350K debt ($600K equity) | $0 cash + $50K mortgage = $50K | $50K taxable |
| Debt drop offset with cash | $800K value, $300K debt ($500K equity) | $850K value, $250K debt ($600K equity: $500K proceeds + $100K cash added) | Mortgage boot MAX(0, 300K − 250K − 100K) = $0 | $0 taxable |

In each row the boot equals the drop in value or the cash taken out, which is why "trade equal or up and reinvest all equity" avoids it.

**Rules to Avoid Boot**:
1. Trade equal or up (replacement value ≥ relinquished value)
2. Reinvest all equity
3. Replace or exceed debt (new debt ≥ old debt, OR add cash to offset)

### Depreciation Recapture (Section 1250)

**Complete Exchange (No Boot)**:
- Capital gain AND depreciation recapture **fully deferred**
- Recapture carries over to replacement property
- Recognized on eventual taxable sale

**Partial Exchange (Boot Received)**:
- Depreciation recapture taxed **first** (before capital gain)
- Recapture amount = lesser of (a) boot received, or (b) accumulated depreciation
- Straight-line depreciation on the building is unrecaptured §1250 gain, taxed at **up to 25%** (the investor's ordinary rate if lower)
- Depreciation on cost-segregated 5/7-year components is **§1245 recapture, taxed as ordinary income** (up to 37%); bonus or accelerated depreciation on 15-year land improvements is §1250 "additional depreciation", also ordinary
- So split accumulated depreciation into the cost-seg/bonus portion and the straight-line portion before estimating the tax on a sale
- Depreciation is "allowed or allowable": basis drops by the depreciation the owner could have taken even if they never claimed it. An owner who skipped it can catch up with Form 3115 before selling.

**Cost seg and 1031**: if the relinquished property holds §1245 components, §1245(b)(4) can trigger recapture in an exchange unless enough §1245 property is received in the replacement.

**Example** (straight-line only, no cost seg):
- Original cost: $500K (land $100K, building $400K)
- Accumulated depreciation: $150K
- Adjusted basis: $350K | Sale: $800K | Gain: $450K

**If sold outright**: $150K unrecaptured §1250 gain (up to 25%) + $300K capital gain (15-20%)
**If 1031 with $50K boot**: $50K recognized (unrecaptured §1250, up to 25%) + $100K deferred recapture + $300K deferred capital gain

### Reverse and Improvement Exchanges

**Reverse Exchange**:
- Acquire replacement **before** selling relinquished
- Exchange Accommodation Titleholder (EAT) holds property temporarily
- 180-day maximum, 45-day identification of relinquished property
- More complex/expensive (adds $5K-$15K to costs)
- Financing challenges (loans in EAT name)

**Improvement/Construction Exchange**:
- Use exchange funds for construction/improvements during 180-day period
- EAT holds title during construction
- Only **completed** improvements count (unfinished = boot)
- 180 days often insufficient for major projects

### Qualified Intermediary (QI) Requirements

**Independence**: Cannot be taxpayer or disqualified person (within 2 years):
- Employee, attorney, accountant, investment banker, broker, agent
- Family members, related entities (>10% common ownership, per Reg. §1.1031(k)-1(k)(3))

**Fund Control**:
- Taxpayer cannot have "constructive receipt" of proceeds
- Direct receipt = immediate taxation, disqualifies exchange

**Due Diligence** (QI industry largely unregulated):
- Verify E&O insurance, fidelity bond
- Confirm segregated accounts, third-party CPA audit
- Check track record and financial stability

### Common Disqualification Triggers

**Fatal Errors**:
1. **Constructive receipt** of funds (even temporarily)
2. **Missing deadlines** (45-day/180-day; no extensions except IRS disaster-relief postponements)
3. **Disqualified person as QI**
4. **Related party exchange** without 2-year hold requirement
5. **Property not held for investment** (primary residence, immediate flip)
6. **Improper identification** (vague, exceeds limits, late)
7. **Title mismatch** (taxpayer on relinquished ≠ taxpayer on replacement)

**Best Practices**:
- Engage QI before listing property
- Include 1031 cooperation clause in contracts
- Identify replacement well before day 45
- Trade equal or up (value and debt)
- Document investment intent (leases, hold period)
- File tax extension if closing near return due date

---

## Bonus Depreciation

### Current Law: One Big Beautiful Bill Act

- **100% bonus, permanent**, for property **acquired after January 19, 2025** (binding written contract date; Notice 2026-11)
- Acquired before January 20, 2025: prior phase-down by placed-in-service year: 80% (2023), 60% (2024), 40% (2025), 20% (2026), 0% after
- **No retroactive relief** for 2023-2024 purchases

### Qualifying Property

**Recovery Period Requirement**: ≤20 years

**Real Estate Qualifying**:
- 5-year: Appliances, carpeting, furniture
- 7-year: Fixtures, equipment
- 15-year: Land improvements, QIP

**Real Estate NON-Qualifying**:
- 27.5-year: Residential building structure
- 39-year: Commercial building structure
- Land: Not depreciable

**Interaction**: Cost segregation identifies 5/7/15-year components eligible for 100% bonus.

### Qualified Production Property (QPP) — NEW 2025

**Definition** (§168(n), Notice 2026-16): nonresidential property used by the taxpayer in U.S. manufacturing, production or refining. Construction must begin after Jan 19, 2025 and before Jan 1, 2029, and the property must be placed in service after July 4, 2025 and before Jan 1, 2031.

**Significance**: a rare 100% write-off of a 39-year building, but **lessors don't qualify**: the owner must use the property in the production activity, so most landlords can't use it. Office, lodging and similar uses are excluded, and disposing of the use within 10 years triggers §1245 recapture.

### Interaction with Passive Activity Loss Rules

**Passive Activity Limitation (IRC §469)**:
- Rental real estate generally passive
- Passive losses offset passive income only
- $25K allowance for active participants (MAGI <$100K, phased out by $150K)

**Real Estate Professional Exception**:
- Qualifies if: (a) RE professional status, AND (b) material participation
- Rental losses NOT passive → fully deductible against ordinary income
- 100% bonus depreciation fully usable in current year

**Excess Business Loss (IRC §461(l))**:
- 2025 limit: $313K (single) / $626K (joint); 2026: $256K / $512K
- Bonus depreciation can trigger limitation
- Consider electing out of bonus for a class if near the threshold

### Election Out of Bonus Depreciation

**When to Consider**:
- Subject to passive loss limitations
- Prefer spreading deductions over time
- Near excess business loss threshold
- AMT considerations

**How to Elect Out**:
- Make election on timely-filed return (with extensions)
- Applies to entire asset class (cannot cherry-pick)
- Election irrevocable

**QIP Options**:
- 100% bonus (immediate)
- 15-year straight-line (spread evenly)
- Section 179 (limits in Key Figures; limited to active business income). QIP and §179 apply to nonresidential property; for a residential rental, the choice is bonus or regular MACRS.

### Example: Residential with Cost Seg and 100% Bonus

**Property (acquired March 2025)**: $1M purchase | Land: $200K | Depreciable: $800K

**Cost Seg Allocations**:
- Building (27.5yr): $500K
- 5-year property: $200K
- 15-year land improvements: $100K

**Without Bonus** (MACRS table rates already include the half-year convention):
- Building: $500K ÷ 27.5 × 9.5/12 = $14,394
- 5-year: $200K × 20% = $40,000
- 15-year: $100K × 5% = $5,000
- **Total Year 1: $59,394**

**With 100% Bonus**:
- Building: $14,394
- 5-year: $200K × 100% = $200,000
- 15-year: $100K × 100% = $100,000
- **Total Year 1: $314,394**

**Year-1 deduction value (37% bracket)**: $314,394 × 37% = **$116,326**, or $94,350 more than without bonus ($255,000 × 37%). Usable this year only if passive-loss and excess-business-loss limits allow.

---

## Opportunity Zones

### Permanent Status (2025 Legislative Changes)

**OBBBA (July 4, 2025)**:
- Made Opportunity Zones **permanent** (sunset provisions repealed)
- Different rules for investments through 2026 vs. 2027+
- **Redesignation**: governors nominated tracts in a window that opened July 1, 2026; the new designations take effect **January 1, 2027**, with new rounds every 10 years. Existing designations run through December 31, 2028.

Check whether a tract is (or will be) designated on the current Treasury/CDFI Fund opportunity zone map rather than relying on a count.

### Investment Timeline: Through 2026 vs. 2027+

| Timeline | Investments Through Dec 31, 2026 (old regime) | Investments After Dec 31, 2026 |
|----------|----------------------------------|-------------------------------|
| **Gain Deferral** | Ends Dec 31, 2026 at the latest | **5 years from QOF investment** OR earlier sale |
| **5-Year Step-Up** | No longer reachable (needed an investment by end of 2021) | 10% of deferred gain excluded (30% for rural funds) |
| **7-Year Step-Up** | No longer reachable (needed an investment by end of 2019) | Eliminated |
| **10-Year Exclusion** | 100% exclusion of QOF gain | 100% exclusion of QOF gain (appreciation capped after 30 years) |

**Timing note (late 2026)**: a new old-regime investment today gets no step-up and only a few weeks of deferral. Gains realized in 2026 can generally be invested after January 1, 2027 under the new rules (within the 180-day window), which is usually the better choice; confirm with Notice 2026-40.

### QOF and QOZP Requirements

**Qualified Opportunity Fund (QOF)**:
- Corporation or partnership
- 90% of assets in Qualified Opportunity Zone Property (QOZP)
- Self-certifies via Form 8996
- Capital gains invested within **180 days** of realization

**Qualified Opportunity Zone Property (QOZP)**:
1. QO Zone Stock (C-corp at original issue)
2. QO Zone Partnership Interest (acquired for cash)
3. QO Zone Business Property (tangible property, original use OR substantially improved)

**Substantial Improvement**: Improvements within 30 months ≥ adjusted basis (50% of basis for property in an entirely rural QOZ).

### Capital Gains Benefits

**Three Potential Benefits**:

1. **Deferral of Original Gain**
   - Defer recognition until sale or 5-year mark (post-2026 investments)
   - Old-regime investments: deferral ends December 31, 2026

2. **Step-Up in Basis on Deferred Gain**
   - 5-year hold (post-2026 investments): 10% of deferred gain permanently excluded (30% for rural funds)

3. **Exclusion of QOF Gain (10-Year Hold)**
   - Make election to step up basis to FMV on sale
   - **All appreciation** on QOF investment **tax-free**

**Example**:
- Invest $1M gain in QOF
- Hold 5 years: $100K original gain excluded (10%)
- Hold 10 years, QOF grows to $2.5M
- Sell: $1.5M appreciation **100% tax-free** (with election)

### Qualified Rural Opportunity Funds (QROF) — NEW 2025

**Definition**: QOF invested in rural Opportunity Zones. "Rural" means any area other than a city or town of more than 50,000 people and the urbanized area next to it (Notice 2025-50).

**Enhanced Benefit**: **30% step-up** at 5-year hold (vs. 10% for standard QOF), for investments after December 31, 2026.

**Example**:
- Invest $1M in QROF
- Hold 5 years: $300K permanently excluded
- Hold 10 years: still eligible for 100% exclusion of QROF gain

### Interaction with Other Strategies

**1031 vs. Opportunity Zone**:
- 1031: Real estate only, full deferral, no exclusion, reinvest all proceeds
- OZ: Any capital gain, partial deferral, 10-year exclusion, invest gain only
- Can combine: 1031 exchange → later sell replacement → invest gain in QOF

**Cost Seg + OZ**: Depreciation benefits separate from OZ capital gains benefits.

**OZ Real Estate Development**: Ground-up development with large appreciation potential maximizes 10-year exclusion benefit.

### Risks and Considerations

- **Illiquidity**: 10-year hold for maximum benefit
- **Operating business risk**: Must invest in active businesses (not just passive RE)
- **Compliance**: 90% asset test (semi-annual), substantial improvement requirements
- **Fund manager selection**: Varied quality, evaluate track record/fees/alignment
- **Regulatory changes**: OZ rules evolved since 2017, future changes possible

---

## Entity Structure

### Comparison Table

| Entity | Liability Protection | Tax Treatment | Best For | Key Limitation |
|--------|---------------------|---------------|----------|---------------|
| **Single-Member LLC** | Good (state-dependent) | Disregarded (Schedule E) | 1-3 properties, simplicity | Weaker charging order in some states |
| **Series LLC** | Excellent (per series) | Each series separate | 5+ properties, asset isolation | Legal uncertainty, banking challenges |
| **Limited Partnership (LP)** | LP: Limited / GP: Unlimited | Pass-through (Form 1065) | Syndications, estate planning | GP liability (use LLC as GP) |
| **S-Corporation** | Good | Pass-through, no debt basis | Active business (agents, flippers) | **NOT for buy-and-hold** (debt basis issue) |
| **Land Trust** | **NONE** (privacy only) | Disregarded | Privacy + LLC as beneficiary | No asset protection alone |

### Single-Member LLC

**Advantages**:
- Liability protection (legal separation, creditor barrier)
- Pass-through taxation (Schedule E, no entity return)
- Simplicity (low setup/maintenance costs)
- Flexibility (can elect S/C-corp, add members)

**Disadvantages**:
- Limited asset protection in some states (charging order weaker)
- No SE tax savings (ordinary rental income isn't subject to SE tax anyway; STRs with hotel-like services are the exception and report on Schedule C)

**Recommended For**: Individual investors, 1-3 properties, simplicity priority.

### Series LLC

**Structure**: Master LLC + multiple series (sub-LLCs), each with separate assets/liabilities.

**Availability**: Delaware, Illinois, Iowa, Nevada, Oklahoma, Tennessee, Texas, Utah, Wyoming (not all states recognize).

**Advantages**:
- Asset protection per series (liabilities isolated)
- Cost savings (one formation, lower annual fees)
- Simplified management

**Disadvantages**:
- Legal uncertainty (limited case law, bankruptcy conflicts)
- Banking/financing challenges
- Compliance complexity (strict separation required)
- California: $800/year per series (eliminates cost advantage)

**Recommended For**: 5+ properties in recognizing states, experienced investors.

### Limited Partnership (LP)

**Structure**:
- General Partner (GP): Manages, unlimited liability
- Limited Partners (LPs): Passive, limited liability

**Advantages**:
- LP asset protection (charging order, limited liability)
- Ideal for syndications (GP manages, LPs contribute capital)
- Estate planning (gift LP interests at discount)
- Flexible profit/loss allocations

**Disadvantages**:
- GP unlimited liability (**use LLC as GP**)
- Complexity/cost (partnership agreement, Form 1065)
- LP participation restrictions (cannot manage)
- Securities law concerns (Reg D compliance)

**Recommended For**: Syndications, family partnerships, large commercial deals.

**Best Practice**: LP with LLC as GP (limits GP liability).

### S-Corporation

**Advantages (Active Business Only)**:
- Self-employment tax savings (split salary/distributions)
- Pass-through taxation (no double tax)

**Example (Active Business)**:
- RE agent earning $300K
- Sole proprietor: ~$30K SE tax
- S-corp: $100K salary + $200K distribution → ~$15K FICA tax
- **Savings: ~$15K** (must pay "reasonable compensation")

**Disadvantages (Buy-and-Hold Rental)**:
- **Stock basis limitation**: Debt does NOT increase basis (unlike LLC/partnership)
- No step-up in basis on death (property inside S-corp)
- No SE tax savings for rental income (generally not subject to SE tax; STRs with substantial services are the exception)
- Reasonable compensation requirement

**Stock Basis Issue Example**:
- S-corp buys $1M property: $200K equity, $800K mortgage
- Shareholder stock basis: **$200K** (debt excluded)
- LLC/partnership: member outside basis = $200K + $800K = **$1M**
- $300K loss: S-corp shareholder can deduct only $200K | LLC member can deduct full $300K

**Recommended For**: Active business (agents, brokers, flippers, developers).
**NOT Recommended For**: Buy-and-hold rental investors.

### Land Trust

**Structure**: Trust holds legal title | Beneficiary retains control (revocable).

**Advantages**:
- Privacy (beneficiary name not on public deed)
- Ease of transfer (change beneficiaries without deed recording)
- Pass-through taxation (disregarded)

**Disadvantages**:
- **NO asset protection** (creditor can reach beneficial interest)
- Does NOT replace LLC
- Trustee fees ($200-$1,000+/year)
- State-specific recognition (common in Illinois, Florida)

**Recommended Structure**:
- **Title**: Land Trust (privacy)
- **Beneficiary**: Wyoming LLC (asset protection)
- **Result**: Name off deed + charging order protection

### Asset Protection Strategies

**1. Wyoming LLC (or Nevada, Delaware)**

**Why Wyoming**:
- Charging order protection for **single-member** LLCs (rare)
- Anonymity (no public member/manager disclosure)
- No state income tax
- Strong LLC statutes

**Charging Order Protection**:
- Creditor's sole remedy: right to distributions (if/when made)
- Creditor cannot seize assets, force liquidation, take control

**Limitations**:
- Privacy ≠ asset protection (home state creditor remedies may apply)
- Single-member risk in some states → **Solution**: create multi-member LLC (add spouse/child as 1% member)

**Cost**: ~$200-$300/year (formation $100, annual report $75, registered agent $50-$150).

**2. Two-Company Structure (Management + Holding)**

**Strategy**: Separate operations (high liability) from assets (low risk).

**Structure**:
- **Management LLC**: Operates business (minimal assets, high liability)
- **Holding LLC**: Owns real estate (leases to Management LLC)

**Benefits**: Protects property from operational liabilities.

**Complications**: Formal leases, transfer pricing, two tax returns.

**Recommended For**: Active businesses, high-activity properties.

**3. Insurance (Critical Layer)**

**Required Coverage**:
- General liability: $1M-$2M
- Umbrella policy: $1M-$5M+
- Property insurance, loss of rents
- Landlord/rental dwelling policy

**Additional**: Flood, earthquake, workers' comp, EPLI (employment practices).

**Best Practices**:
- Maintain adequate limits (review annually)
- Name LLC as insured (not just individual)
- Verify coverage for rental/investment use

**4. Layered Structure**

**Example**:
1. **Property Title**: Illinois Land Trust (privacy)
2. **Beneficiary**: Wyoming LLC (asset protection)
3. **Member**: Revocable living trust (estate planning)

**Result**: Privacy (name off deed) + asset protection (charging order) + estate planning (avoid probate).

### Syndication Structures (GP/LP)

**Purpose**: Raise capital from passive investors for commercial RE.

**Typical Structure**: Limited Partnership or LLC (treated as partnership).

**Profit Split (Waterfall)**:

| Tier | Distribution | Example |
|------|-------------|---------|
| **1. Return of Capital** | LPs receive 100% of invested capital | $5M investment → $5M to LPs |
| **2. Preferred Return** | LPs receive fixed annual return (6-10%) | 8% × 5 years × $5M = $2M to LPs |
| **3. GP Catch-Up** | GP receives disproportionate share until target split | GP gets 100% until 20% of total profits |
| **4. Final Split** | Remaining cash flow split per ratio | 80/20 LP/GP (matching a 20% catch-up target) |

**Example Waterfall** ($5M LP investment, $8M net proceeds after 5 years, simple pref with a full catch-up):
- Tier 1 (ROC): LPs get $5M
- Tier 2 (8% pref): LPs get $2M
- Tier 3 (GP catch-up to 20% of profits): GP gets $500K ($500K / $2.5M distributed profit = 20%)
- Tier 4 (80/20 split of the last $500K): LPs get $400K, GP gets $100K
- **Total**: LPs $7.4M ($2.4M profit, 48% over 5 years) | GP $600K (20% of the $3M profit)

`scripts/waterfall.py --mode simple` runs this structure (it applies one year of pref, so pass `--pref-rate 0.40` for five years at 8% to reproduce this example); its IRR mode runs the hurdle-based waterfall in advanced-analysis.md. The GP promote is carried interest: under §1061 it needs a 3-year holding period for long-term treatment, though §1231 gain from selling rental property is generally excluded from recharacterization.

**Capital Contributions**: LPs 80-95%, GP 5-20% (plus expertise/time).

**Securities Law**: Must comply with Reg D (506(b) or 506(c)) | Legal costs: $15K-$50K+.

**Recommended For**: Sponsors raising $1M+ equity, commercial RE, experienced operators.

### Passive Activity Loss Rules & Real Estate Professional Status

**General Rule (IRC §469)**: Rental real estate = passive activity.

**Consequence**: Passive losses offset passive income only (excess suspended).

**$25K Special Allowance**:
- Active participants can deduct up to $25K against non-passive income
- Active participation: make management decisions (approve tenants, set rent, repairs)
- Phase-out: $0.50 per $1 MAGI over $100K (fully phased out at $150K)

**Real Estate Professional Exception (IRC §469(c)(7))**:

**Requirements** (must meet BOTH):
1. **>50%** of personal services in real property trades/businesses, AND
2. **>750 hours** in real property trades/businesses

**Material Participation** (also required):
- >500 hours in activity, OR
- Substantially all participation, OR
- >100 hours and no one participates more, OR
- Other IRS tests

**Election to aggregate rental real estate** (§469(c)(7)(A), Reg. §1.469-9(g); RE professionals only): treat all rental real estate as one activity, which makes the 500-hour test easier to meet.

**Benefits**:
- Rental losses NOT passive
- Fully deductible against wages, business income
- No $25K limitation
- **Huge benefit with cost segregation/bonus depreciation**

**Example (RE Professional)**:
- W-2 income: $200K | Rental loss: $100K (cost seg)
- Qualified as RE professional and materially participates
- **Result**: $100K fully deductible → taxable income $100K
- Tax savings at 37%: **$37,000**

**Common Scenarios**:

| Scenario | Hours/Activity | Qualification | Result |
|----------|---------------|---------------|--------|
| Full-time W-2 + rentals | 2,000hr W-2 (non-RE) | Fails >50% test | NOT RE professional, passive losses |
| Full-time RE agent | 2,000hr agent, 200hr rentals | RE professional, lacks material participation | Passive losses (must group + increase to 500hr) |
| Spouse as RE pro | Spouse 800hr RE (>50%), materially participates | Qualifies (joint return) | Non-passive, offset household income |

**Documentation Requirements** (IRS heavily scrutinizes):
- Contemporaneous logs (not reconstructed)
- Detailed service descriptions
- Calendars, time tracking
- Maintenance logs, tenant communications
- **Failure to document = IRS disallows**

---

## Sources

Primary IRS guidance (checked October 2026):
- [Notice 2026-11: 100% bonus depreciation under OBBBA](https://www.irs.gov/pub/irs-drop/n-26-11.pdf)
- [Notice 2026-16: Qualified production property](https://www.irs.gov/pub/irs-drop/n-26-16.pdf)
- [Notice 2026-40: Opportunity zones under OBBBA](https://www.irs.gov/pub/irs-drop/n-26-40.pdf)
- [Rev. Proc. 2025-32: 2026 inflation adjustments](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf)
- [Publication 946 (2025), How To Depreciate Property](https://www.irs.gov/publications/p946)
- [Publication 925 (2025), Passive Activity and At-Risk Rules](https://www.irs.gov/publications/p925)
- [Publication 527 (2025), Residential Rental Property](https://www.irs.gov/publications/p527)
- [Publication 544 (2025), Sales and Other Dispositions of Assets](https://www.irs.gov/publications/p544)
- [Topic 409, Capital gains and losses](https://www.irs.gov/taxtopics/tc409)
- [Instructions for Form 8824, Like-Kind Exchanges](https://www.irs.gov/instructions/i8824)
- [Opportunity Zones FAQs](https://www.irs.gov/credits-deductions/opportunity-zones-frequently-asked-questions)
- [26 U.S.C. §168](https://www.law.cornell.edu/uscode/text/26/168) and [Reg. §1.1031(k)-1](https://www.law.cornell.edu/cfr/text/26/1.1031(k)-1)
- [Final regulations under §1061 (T.D. 9945)](https://www.federalregister.gov/documents/2021/01/19/2021-00427/guidance-under-section-1061)

Practitioner background (secondary; use the IRS sources above for figures):
- [S-Corp Wrong Entity for RE Investments | Cerebral Tax](https://www.cerebraltaxadvisors.com/blog/real-estate-in-an-s-corp/)
- [Improvement and Reverse Exchanges | IPX1031](https://www.ipx1031.com/our-services/reverse-improvement-exchanges/)
- [Distribution Waterfalls | Tactica RES](https://www.tacticares.com/blog-feed/distribution-waterfalls-in-multifamily-investment)
