# M&A and Due Diligence Frameworks

## Synergy Sizing and Phasing

### What It Is
A disciplined method for estimating and time-phasing the value created by combining two businesses. Deals are priced on synergies; overstated or front-loaded synergies are the single most common way acquirers overpay.

### Revenue vs. Cost Synergies

| Dimension | Cost synergies | Revenue synergies |
|-----------|----------------|-------------------|
| Typical sources | Overlapping G&A, procurement scale, facility consolidation, IT rationalization | Cross-sell, geographic expansion, pricing power, bundling |
| Realization confidence | High — within management's control | Low — depends on customer behavior |
| Typical haircut in valuation | Credit 80-100% of a well-built estimate | Credit 0-50%; many deal committees credit zero |
| Timing | 12-36 months | 24-48 months, if ever |
| Dis-synergies to net against | Integration distraction, retention packages | Customer overlap churn, channel conflict, brand confusion |

### How to Apply
1. **Build bottom-up, by line item**: "8% of combined SG&A" is a target, not an estimate. Name the overlapping functions, headcount, facilities, and contracts, and cost each one.
2. **Net out dis-synergies**: every deal loses some revenue (overlapping customers dual-sourcing on purpose, competitor poaching during integration) and incurs retention costs. A synergy case with zero dis-synergies is a red flag in itself.
3. **Phase with a realization curve**: synergies ramp, they don't switch on. Revenue synergies typically start in Year 2 at the earliest. A defensible default phasing:

| Synergy type | Year 1 | Year 2 | Year 3 | Year 4 |
|--------------|--------|--------|--------|--------|
| Headcount / G&A overlap | 30-40% | 70-80% | 100% | 100% |
| Procurement scale | 20-30% | 60-70% | 90-100% | 100% |
| Facility / footprint consolidation | 0-10% | 40-50% | 80-90% | 100% |
| Revenue synergies (haircut applied) | 0% | 10-25% | 40-60% | 60-80% |

   Percentages are of run-rate; treat them as defaults to be replaced by the integration plan's bottom-up phasing, not as evidence in themselves.
4. **Subtract cost-to-achieve**: severance, system migration, rebranding, advisor fees. Rule of thumb: one-time cost-to-achieve of 1.0-1.5x the annual run-rate cost synergies (source deal-specific benchmarks before relying on this).
5. **Assign ownership**: each synergy line item needs a named post-close owner and a tracking metric, or it will not be realized.

### Common Pitfalls
- Crediting revenue synergies at full value in the purchase price — the seller captures the value, the buyer keeps the risk
- Double counting: procurement savings already in the standalone plan reappearing as deal synergies
- Ignoring the realization curve and valuing Year-3 run-rate as if it starts at close
- "Synergy" line items that are really standalone cost programs the target could do alone (these justify no premium)

### Quality Check
- Every synergy line item is named, costed bottom-up, phased, and owner-assigned
- Dis-synergies and cost-to-achieve are explicit lines, not footnotes
- Revenue synergies are separated and haircut, with the haircut rationale stated
- The NPV of synergies is compared to the control premium — if premium > synergy NPV, the deal transfers value to the seller

---

## Valuation Triangulation

### What It Is
Cross-checking a valuation with three independent lenses — DCF, trading comparables, and precedent transactions — because each lens fails in a different, predictable way. A valuation supported by one lens is an opinion; supported by three, it's a range you can defend.

### The Three Lenses

| Lens | What it measures | When it misleads |
|------|------------------|------------------|
| DCF | Intrinsic value of projected cash flows | Garbage-in: terminal value is often 60-80% of the total, so small changes in perpetuity growth or WACC swing the answer more than all the near-year forecasting combined. Misleads most when projections come from the seller. |
| Trading comps | What the market pays today for similar public companies | Misleads when the "comps" aren't comparable (different growth/margin/mix), when the sector is in a bubble or trough, and for illiquid or controlled companies. Reflects minority-stake value — no control premium. |
| Precedent transactions | What acquirers actually paid for control of similar assets | Misleads when precedents are stale (different rate environment), scarce (n=3 is an anecdote, not a benchmark), or strategic outliers (a desperate buyer's multiple is not the market). Embeds historical control premiums and synergy expectations. |

### How to Apply
1. Run all three lenses independently — do not tune one to match another.
2. Present as a "football field": the value range from each lens on one chart, with the proposed price marked.
3. Interrogate divergence: if DCF is far above comps, the projections are probably optimistic; if precedents are far above trading comps, that gap is the control premium plus synergy expectations — ask whether this deal justifies it.
4. State which lens you weight most and why (e.g., stable cash generator → DCF; hot sector with good comps → trading multiples).

### Quality Check
- Comp set membership is justified company-by-company (growth, margin, business mix), not just SIC code
- DCF sensitivity table on WACC × terminal growth is shown, and terminal value share of total NPV is stated
- Precedent set notes deal date, rate environment, and any strategic-outlier bids
- The recommendation is a range with a walk-away price, not a point estimate

---

## Integration Cost Benchmarks

### What It Is
Order-of-magnitude heuristics for what integration actually costs, used to sanity-check deal models that treat integration as a rounding error.

### Benchmarks (heuristics — source deal-specific data before relying on them)
- **Total one-time integration cost**: commonly 1-3% of deal value for large deals, or 1.0-1.5x annual run-rate cost synergies — whichever framing the deal team uses, it must appear as an explicit cost line
- **IT/systems integration**: frequently the largest single line, especially in ERP-heavy or regulated businesses; full systems consolidation typically runs 2-3+ years
- **Retention**: key-talent retention packages commonly 25-100% of base salary for the critical population, paid over 12-24 months
- **Integration management office**: a dedicated IMO for 12-24 months; deals without one systematically under-deliver synergies
- **Timing**: integration costs land in Years 0-2 while synergies ramp on the realization curve — the deal's cash-flow trough is Year 1, and the model should show it

### Quality Check
- Integration costs appear as explicit, phased lines in the model — never netted invisibly against synergies
- IT integration is separately estimated for any deal where systems are core to operations
- The Year-1 cash-flow trough is visible and financeable
- Benchmarks are replaced with bottom-up estimates as DD data becomes available

---

## Red-Flag Taxonomy

### What It Is
A classification of the recurring patterns that signal deal risk, mapped to the severity ratings used in the due-diligence agent's risk register (Critical / Material / Minor) and its red-flag table (revenue concentration, margin decline, management turnover, cash-flow/earnings divergence, related-party transactions, regulatory actions, declining growth, unusual audit opinions).

### Taxonomy

| Red flag | Typical rating | Deal implication |
|----------|----------------|------------------|
| Customer concentration >20% single customer | Critical-Material | Value the at-risk revenue separately; condition close on contract extensions |
| Cash flow / earnings divergence (profit up, OCF flat) | Critical until explained | Quality-of-earnings review; possible aggressive revenue recognition |
| Unusual audit opinions, auditor changes, going-concern language | Critical | Full forensic accounting before any price discussion |
| Undisclosed related-party transactions | Critical | Governance failure — question everything else management has represented |
| Regulatory actions, consent orders, open investigations | Critical-Material | Quantify liability range; consider indemnity escrow |
| CFO/CEO turnover within 12 months, multiple C-suite exits | Material | Management interviews pre-LOI; probe the real reason |
| Margin decline without stated cause | Material | Test whether pricing power is eroding — affects terminal value, not just next year |
| Decelerating growth 3+ quarters | Material | Re-underwrite the growth assumptions in the model; the thesis may be aging |
| Normal-course litigation, minor compliance gaps | Minor | Document in risk register; standard reps & warranties |

### How to Apply
1. A red flag is a signal, not a conclusion — investigate before rating. Many have benign explanations; the rating reflects what remains after investigation.
2. Rate every flag using the DD risk register scale so findings flow directly into the memo's risk table.
3. Escalate any Critical rating to the EM immediately — do not hold it for the final memo.

### Quality Check
- Every flag investigated before final rating, with the explanation (or its absence) documented
- Ratings map 1:1 to the risk register — no unrated observations
- Each Critical/Material flag carries a quantified impact estimate or an explicit "cannot quantify from public sources"

---

## Deal-Breaker vs. Price-Chip Framing

### What It Is
The negotiation lens for DD findings: a finding only matters through how it changes the deal. Every Critical or Material finding must be classified into one of four buckets, or the DD memo leaves value on the table.

### The Four Buckets
1. **Deal-breaker**: no price fixes it — walk away unless it is resolved before signing. Examples: fraud indicators, a regulatory bar to the transaction, loss of the asset the thesis depends on.
2. **Price chip**: real, quantifiable, and priceable. Convert to a valuation adjustment (e.g., value at-risk revenue at a lower multiple; deduct remediation capex from the price). A price chip without a number is just a complaint.
3. **Reps & warranties / indemnity item**: possible but unverifiable exposure — allocate the risk contractually (specific indemnity, escrow, earnout) rather than pricing it.
4. **Post-close fix**: manageable through the integration plan; goes in the 100-day plan with an owner, not in the price negotiation.

### How to Apply
1. Classify every Critical/Material finding into exactly one bucket; state the rationale in one line.
2. Quantify every price chip — the sum of chips versus the premium is the negotiation map.
3. Test the deal-breaker list honestly: teams under deal momentum reclassify breakers as chips. Ask "would we still do this deal at any price?" — if no, it's a breaker.
4. Present the classification in the DD memo (the dd-memo template carries a section for it) so the EM and Consultant see the negotiation posture, not just a risk list.

### Common Pitfalls
- Deal momentum bias: every finding becomes a "post-close fix" as the close date approaches
- Unquantified chips: "customer concentration should be reflected in price" — by how much?
- Using indemnities for known, quantifiable problems (those belong in price) or price for unknowable ones (those belong in indemnities)

### Quality Check
- Every Critical/Material finding classified into exactly one bucket with rationale
- Every price chip has a currency value or valuation-multiple impact
- The deal-breaker test ("still do it at any price?") is documented for each breaker candidate
- The classification is consistent with the DD memo's overall recommendation
