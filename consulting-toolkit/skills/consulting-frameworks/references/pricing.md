# Pricing Frameworks

## Price-Volume-Mix Decomposition

### What It Is
The first analysis in any revenue or margin diagnostic: splitting a revenue change into how much came from price, how much from volume, and how much from mix (customers/products shifting between price tiers). Growth "from price" and growth "from volume" have opposite strategic implications.

### How to Build
1. Get revenue and units by product/segment for two periods.
2. **Volume effect** = (units₁ − units₀) × price₀, summed by segment
3. **Price effect** = (price₁ − price₀) × units₁, summed by segment
4. **Mix effect** = the residual when segments are aggregated — revenue change caused by the shift of units between higher- and lower-priced segments, holding each segment's own price constant
5. Present as a waterfall: Revenue₀ → +volume → +price → +mix → Revenue₁

### Reading the Result
- **Price-led growth with flat volume**: pricing power, or a demand problem being masked — check share data
- **Volume-led growth with negative price**: buying share; test whether the discounting is disciplined or leakage (see Discount Waterfall)
- **Negative mix with positive price**: customers trading down while list prices rise — often the early signature of competitive erosion

### Common Pitfalls
- Skipping mix and calling everything "price" — with heterogeneous portfolios, mix routinely dominates
- Computing effects at the total-company level instead of segment level (aggregation hides the story)
- Currency effects left inside "price" in multi-currency businesses — strip FX first

### Quality Check
- The three effects sum exactly to the total revenue change (show the reconciliation)
- Decomposition done at segment level, aggregated after
- FX isolated as its own bar in multi-currency cases
- Each bar carries a so-what, not just a number

---

## Van Westendorp Price Sensitivity Meter

### What It Is
A survey technique that locates an acceptable price range by asking four questions about a described product: at what price is it (1) so cheap quality is doubted, (2) a bargain, (3) getting expensive, (4) too expensive to consider.

### How to Apply
1. Survey the target segment (n ≥ 100 per segment for stable curves) with the four open-ended price questions.
2. Plot cumulative distributions of the four answers against price.
3. Read the intersections: the range between the "point of marginal cheapness" and "point of marginal expensiveness" is the acceptable band; the "optimal price point" (too-cheap × too-expensive intersection) minimizes rejection at both ends.
4. Sanity-check the band against unit economics and competitor prices before adopting it.

### When It Misleads
- Stated willingness to pay ≠ actual purchase behavior — treat the output as a range-finder, not a price-setter
- Fails for genuinely novel products where respondents have no reference price
- Respondents anchor on current market prices, so it under-detects headroom for differentiated offers

### Quality Check
- Sample is the actual target segment, not a convenience panel
- Results reported as a band with intersection points, never a single "optimal" number presented as truth
- Cross-checked against at least one behavioral signal (transaction data, test pricing, conjoint)

---

## Conjoint Analysis Basics

### What It Is
A survey method that infers what customers will pay for individual product attributes by forcing trade-offs between realistic product bundles. The workhorse for feature-level willingness-to-pay and price-response simulation.

### How to Apply
1. **Define attributes and levels** (keep to 5-7 attributes; e.g., price at 4 levels, warranty at 3, brand at 3). Attributes must be independent and levels realistic.
2. **Run choice-based conjoint (CBC)**: respondents repeatedly pick one option from sets of 3-4 constructed profiles — mimics real purchase decisions better than ranking.
3. **Estimate part-worth utilities** per attribute level (hierarchical Bayes is standard) — the utility scale converts to willingness-to-pay using the price attribute's utility per currency unit.
4. **Simulate**: build a market simulator to test share shifts for price moves and feature configurations against competitor offers.

### When to Use vs. Van Westendorp
- Van Westendorp: fast, cheap, one product concept, range-finding
- Conjoint: feature-level decisions, portfolio/tier design, price-response curves, competitive simulation — slower and costlier but decision-grade

### Common Pitfalls
- Too many attributes → respondent fatigue → noise presented as insight
- Omitting the competitor context from simulations (share numbers become meaningless)
- Reading absolute predicted shares as forecasts — conjoint is reliable for relative comparisons, not absolute volumes

### Quality Check
- Attribute list grounded in qualitative research, not the team's feature wishlist
- Holdout tasks used to validate the model's predictive accuracy
- Outputs framed as relative share shifts and WTP ranges with confidence intervals

---

## EDLP vs. Hi-Lo

### What It Is
The two archetypal retail price architectures: Every Day Low Price (stable low shelf prices, minimal promotion) versus Hi-Lo (higher base prices punctuated by deep promotions).

### The Economics

| Dimension | EDLP | Hi-Lo |
|-----------|------|-------|
| Margin structure | Thinner but stable; low promo spend | Higher base margin funding deep promos |
| Demand pattern | Smooth — efficient supply chain, low stockouts | Spiky — forward-buying, pantry-loading, higher logistics cost |
| Customer attracted | Time-poor, trust-seeking; builds basket loyalty | Deal-seeking cherry-pickers; drives traffic spikes |
| Communication cost | Low ongoing (the position is the message) | High — every promotion must be marketed |
| Key risk | Position collapses if competitors credibly undercut | Promo addiction: base price loses credibility, margin erodes |

### How to Choose
1. Analyze the transaction data: what share of volume currently sells on promotion, and at what incremental margin? If >40-50% of volume is promoted, base prices have already lost credibility.
2. Segment the customer base: cherry-picker-heavy traffic favors Hi-Lo mechanics; loyalty-driven baskets favor EDLP.
3. Model the transition cost: moving Hi-Lo → EDLP means a visible base-price cut funded by eliminating promos — revenue dips before it stabilizes, and the case must show the bridge.
4. Check competitive response capacity: EDLP only holds if the cost structure supports being the credible low-price player.

### Quality Check
- Recommendation grounded in the client's own promo-lift and margin data, not category folklore
- Transition path modeled, including the trough
- Competitor cost positions assessed before recommending EDLP

---

## Price-Elasticity Estimation from Transaction Data

### What It Is
Estimating how demand responds to price from the client's own sales history — the empirical backbone of any pricing recommendation. Elasticity ε = %Δvolume / %Δprice; ε < −1 means revenue falls when price rises.

### How to Build
1. **Assemble panel data**: SKU × store/customer × week, with net price, units, promotion flags, and stock-out indicators.
2. **Use natural price variation**: promotions ending, list-price changes, regional differences. No variation → no estimate (consider a test-and-learn pilot instead).
3. **Estimate log-log regression**: ln(units) = α + ε·ln(price) + controls. The price coefficient is the elasticity directly.
4. **Control for confounders**: seasonality (week/month effects), promotion display/feature flags, competitor prices where available, stock-outs, and trend.
5. **Segment the estimates**: elasticity by product tier and customer segment — a portfolio-average elasticity hides exactly the differences pricing strategy exploits.

### Common Pitfalls
- **Promo contamination**: estimating "elasticity" mostly from promotion weeks measures deal-seeking response, not base-price response — model them separately
- **Endogeneity**: prices are set in response to demand (managers raise prices when demand is hot), biasing estimates toward zero; use cost shocks or staggered price changes as cleaner variation
- **Stock-outs** read as low demand at high price
- Extrapolating far outside the observed price range

### Quality Check
- Base-price elasticity and promo-lift reported as separate numbers
- Confounder controls listed; the identification source of price variation stated explicitly
- Estimates presented as ranges with the revenue-maximizing implication ("ε ≈ −1.4 → a 5% increase loses ~7% volume; margin-positive if contribution margin > ~55%")
- Recommendation includes a test-and-learn validation step before full rollout

---

## B2B Discount Waterfall

### What It Is
The pocket-price analysis: tracing every leak between list price and the cash actually pocketed per transaction. In most B2B businesses the average waterfall leaks 20-40% of list, and the spread between best and worst transactions is wider than anyone internally believes.

### The Waterfall Structure
```
List price
  − standard discount            (published tier/volume discount)
  − negotiated discount          (deal desk concessions)
= Invoice price
  − payment-terms cost           (early-pay discounts, extended terms)
  − rebates                      (volume, growth, loyalty — often accrued invisibly)
  − co-op / marketing allowances
  − freight absorbed, service given away
= Pocket price
```

### How to Apply
1. Build the waterfall per transaction from ERP data — averages hide the story.
2. Plot the **pocket-price band**: the distribution of pocket price across all transactions for the same product. A wide band (commonly ±25% or more around the mean) is the opportunity.
3. Cross the band with customer size: small customers pocketing large-customer prices is the classic finding — discipline failure, not strategy.
4. Fix the leaks in order of controllability: off-invoice items first (rebates, terms, freight) because nobody "owns" them; then negotiated-discount governance (approval thresholds tied to pocket margin, not invoice discount).
5. Quantify the prize: moving the bottom decile of transactions to the median pocket price is a standard, credible sizing.

### Common Pitfalls
- Analyzing invoice price and declaring victory — most leakage is off-invoice
- Setting sales incentives on revenue or invoice discount, which rewards pocket-price destruction
- One-time cleanup without changing the deal-approval rules that recreate the band

### Quality Check
- Waterfall built from transaction-level data, all off-invoice leaks included
- Pocket-price band shown, segmented by customer size and product
- The prize is sized from moving specific transaction cohorts, not a generic "1% price = X% profit" claim
- Recommendations pair pricing moves with governance changes (approval limits, incentive metrics)
