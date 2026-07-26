# Prompt Evals Reference

How to measure whether a prompt change actually helped: build a small eval set, run the bundled A/B harness (`scripts/ab_eval.py`), and read the win rate honestly. This is workflow step 5 ("Measure") from SKILL.md — never assume a prompt change helped without checking.

## Contents

- Why 10–20 cases
- Case selection
- Phrasing `expected_behavior`
- Avoiding leakage
- Running `scripts/ab_eval.py`
- When a win rate is meaningful

## Why 10–20 cases

A 10–20 case set is the sweet spot for prompt iteration: large enough to catch regressions and give a directional signal, small enough to build in under an hour and run in a few minutes. It is **not** a benchmark — it tells you "variant B is probably better / probably worse / indistinguishable", which is exactly the decision you need during optimization. Scale up only when two variants keep coming out indistinguishable and the difference matters.

## Case selection

Each case is one line of JSONL:

```json
{"input": "the exact user message you would send in production", "expected_behavior": "what a good response does, stated as observable behavior"}
```

Pick cases in roughly this mix:

1. **Real failures (5–8 cases).** The concrete inputs that made you want to change the prompt — verbatim from logs or transcripts, not paraphrased. Paraphrasing smooths away the exact phrasing that triggered the failure.
2. **Currently-working cases (3–6 cases).** Inputs the current prompt handles well. These are your regression guard: a variant that fixes the failures but breaks these is a net loss, and without them the eval can't tell you.
3. **Edge cases (2–4 cases).** Ambiguous requests, adversarial phrasings, empty-ish inputs, very long inputs — whatever your production distribution actually contains at the tails.
4. **One behavior per case.** A case that checks formatting AND tone AND tool mentions gives the judge a three-way tradeoff to arbitrate; you learn nothing from its verdict. Split it into three cases.

Keep inputs production-shaped: same length, same formality, same language mix as real traffic. A tidy hand-written test set measures a distribution you don't serve.

## Phrasing `expected_behavior`

The judge is told to evaluate only how well each response satisfies `expected_behavior`, so its phrasing is the eval's spec. Rules:

- **Describe observable behavior, not internals.** "Answers in 2–3 sentences without markdown headers" — checkable. "Understands the user wants brevity" — not.
- **Be concrete enough to disagree with.** If you can't imagine a response that clearly violates it, it's too vague ("responds helpfully") and every verdict will be a coin flip.
- **State scope.** "Every list item gets a citation, not just the first" — the latest models are literal, and so are judges.
- **Don't over-specify wording.** Requiring an exact phrase makes the judge do string matching and penalizes good responses that phrase things differently. Specify the property ("acknowledges the refund cannot be processed and offers the two alternatives"), not the sentence.
- **Positive framing.** "Uses plain text math with / and ^" beats "does not use LaTeX" — the judge evaluates the presence of a behavior more reliably than the absence of one.

## Avoiding leakage

Leakage is when the eval can be passed without the behavior actually improving:

- **Never paste `expected_behavior` text into the prompt variants.** If variant B contains "answer in 2–3 sentences" because you copied it from a case, the eval measures whether the model can follow an instruction it was literally given — always yes — not whether your prompt change generalizes.
- **Don't use eval inputs as few-shot examples** in either variant. The variant then wins on those cases by memorization, not behavior.
- **Hold out cases across iterations.** If you tune the prompt against the same 15 cases ten times, you are fitting to them. Either add fresh cases each round, or keep 5 cases you never look at while editing and check them last.
- **Same model for both variants.** The harness enforces this (one `--model` for A and B); don't compare a prompt change and a model change in one run.

## Running `scripts/ab_eval.py`

The harness runs each case's `input` under variant A's system prompt, then variant B's, then shows both responses to a judge model with **presentation order randomized per case** (seeded, so runs are reproducible) to avoid position bias. Calls are sequential with a small sleep — rate-limit friendly.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Preview the run first - no API calls, no SDK needed:
python scripts/ab_eval.py cases.jsonl --prompt-a current.txt --prompt-b candidate.txt --dry-run

# Real run (defaults: claude-sonnet-5 for candidates and judge):
python scripts/ab_eval.py cases.jsonl --prompt-a current.txt --prompt-b candidate.txt

# Stronger judge, full transcript saved for inspection:
python scripts/ab_eval.py cases.jsonl --prompt-a current.txt --prompt-b candidate.txt \
    --judge-model claude-opus-5 --output results.json
```

Key options:

| Flag | Default | Meaning |
|---|---|---|
| `--model` | `claude-sonnet-5` | Model that runs both variants (keep identical for A and B) |
| `--judge-model` | `claude-sonnet-5` | Model that picks the winner per case |
| `--sleep` | `1.0` | Seconds between API calls (raise if you hit rate limits) |
| `--seed` | `42` | Controls per-case judge presentation order |
| `--max-tokens` | `1024` | Per candidate call |
| `--output` | — | Write full responses + judge reasoning as JSON |
| `--dry-run` | — | Print the plan (cases, judge order, call count) without calling the API |

Per case it prints both responses, a unified diff, and the judge's verdict; at the end, the win rate (A wins / B wins / ties / unparsed verdicts).

## When a win rate is meaningful

- **Big gaps are signal, small gaps are noise.** With 15 cases, a single flipped verdict moves the rate by ~7 points. Treat anything under roughly a 20-point gap (e.g. 8–6 with a tie) as "indistinguishable" — the harness prints a note when a run lands in this zone. 12–3 is real; 8–7 is a coin flip.
- **Check ties and unparsed verdicts first.** Many ties usually mean `expected_behavior` is too vague to discriminate — fix the cases before trusting the rate. Unparsed verdicts are excluded from the tally; more than one or two means the judge output format broke and the run should be inspected via `--output`.
- **Re-run before believing a surprising result.** Change `--seed` (different presentation order) or the judge model; a real win survives both. Position randomization removes systematic position bias but not judge variance.
- **The judge shares model biases.** An LLM judge tends to reward confident, well-structured, longer responses. If your `expected_behavior` is about concision or restraint, spell that out in the case ("a shorter response that covers X beats a longer one") — the harness already instructs the judge to ignore length and style unless the expected behavior mentions them, but per-case reinforcement helps.
- **Win rate complements, never replaces, reading transcripts.** Before shipping the winner, read the `--output` JSON for at least the flipped cases: judges occasionally reward a response that satisfies the letter of `expected_behavior` while being worse in a way your cases didn't encode. That's a missing case — add it.
