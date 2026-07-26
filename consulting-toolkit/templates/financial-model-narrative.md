<!--
Template: Financial Model Narrative. Used by the financial-modeler agent and
/business-case as the companion document to every model — a spreadsheet without
a narrative is a black box.
Replace every [bracketed placeholder]; delete guidance comments before delivery.
Rules: every assumption has value, unit, source, and confidence; no magic numbers;
scenario and sensitivity sections are mandatory.
Save as: financial-model-[topic]-narrative.md (alongside financial-model-[topic].xlsx)
-->

# Financial Model Narrative — [Topic]

**Date:** [YYYY-MM-DD] | **Model file:** [financial-model-[topic].xlsx] | **Decision supported:** [the go/no-go question]

## What the Model Says

<!-- The headline answer in one sentence, then the metric table. -->

> [e.g. "The acquisition generates a base-case NPV of €45M at an 18% IRR, with payback in Year 3."]

| Metric | Downside | Base | Upside |
|--------|----------|------|--------|
| NPV | [value] | [value] | [value] |
| IRR | [value] | [value] | [value] |
| Payback | [year] | [year] | [year] |

## Key Assumptions

<!-- Mirror of the model's Assumptions sheet. Every row: value, unit, source, confidence. -->

| Assumption | Value | Unit | Source | Confidence (High/Med/Low) |
|------------|-------|------|--------|---------------------------|
| [e.g. Revenue growth] | [value] | [%/yr] | [Source, Date] | [level] |
| [e.g. Discount rate] | [value] | [%] | [e.g. WACC build: FRED risk-free + premium] | [level] |
| [e.g. Integration cost] | [value] | [currency] | [Source, Date or "estimate — basis"] | [level] |

## What Drives the Answer

<!-- The 2-3 assumptions that most influence the output, with quantified impact. -->

- [e.g. "Revenue growth: a 2pp change swings NPV by ±€12M [Analyst calculation: model sensitivity sheet]"]
- [driver 2 with quantified swing]
- [driver 3 with quantified swing]

## Scenarios

| Scenario | Definition (what changes vs. base) | Key result | So-what |
|----------|-------------------------------------|-----------|---------|
| Base | [assumption set] | [NPV/IRR] | [implication] |
| Upside | [e.g. +20% on drivers X, Y] | [NPV/IRR] | [implication] |
| Downside | [e.g. -20% on drivers X, Y] | [NPV/IRR] | [implication] |

## Sensitivities and Break-Evens

[Two-way sensitivity on the two most impactful variables, and the break-even values where the recommendation flips, e.g. "If integration costs exceed [value] (vs. base [value]), IRR drops below the [x]% hurdle rate."]

## Where the Model Is Most Uncertain

[The inputs with lowest confidence, what risk they carry, and what would resolve them (e.g. "customer retention assumed at [x]% from industry benchmarks [Source, Date] — validate via customer interviews during DD").]

## Recommendation (input to EM synthesis)

[What the analysis supports and under what conditions — framed as input to the Engagement Manager's synthesis, not a final decision.]
