#!/usr/bin/env python3
"""A/B prompt evaluation harness for the prompt-optimizer skill.

Compares two prompt variants (A and B) against the same eval cases and reports
per-case diffs plus a judge-based win rate. Companion guide (case selection,
expected_behavior phrasing, when a win rate is meaningful):
references/evals.md.

Case file format - JSONL, one case per line:

    {"input": "user message text", "expected_behavior": "what a good response does"}

For each case, the harness:

1. Sends ``input`` as the user message with variant A as the system prompt,
   then again with variant B (sequential, small sleep between calls - rate
   limit friendly).
2. Shows both responses to a judge model, with A/B presentation order
   randomized per case to avoid position bias, and asks which response better
   satisfies ``expected_behavior``.
3. Prints a per-case diff and verdict, then an overall win rate.

Usage:

    export ANTHROPIC_API_KEY=sk-ant-...
    python ab_eval.py cases.jsonl --prompt-a prompt_a.txt --prompt-b prompt_b.txt

    # See exactly what would run, with no API calls and no SDK required:
    python ab_eval.py cases.jsonl --prompt-a a.txt --prompt-b b.txt --dry-run

    # Different candidate / judge models, save full transcript:
    python ab_eval.py cases.jsonl --prompt-a a.txt --prompt-b b.txt \
        --model claude-sonnet-5 --judge-model claude-opus-5 --output results.json

Requires: pip install anthropic (not needed for --dry-run).
Exits 0 on success, 1 on usage/data errors, 2 on missing API key or SDK.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import random
import sys
import time

DEFAULT_MODEL = "claude-sonnet-5"
VERDICT_PREFIX = "VERDICT:"

JUDGE_SYSTEM = (
    "You are an impartial evaluator comparing two candidate responses to the "
    "same input. Judge only how well each response satisfies the stated "
    "expected behavior - not length, confidence, or style, unless the "
    "expected behavior mentions them."
)

JUDGE_TEMPLATE = """Compare the two responses below.

<input>
{case_input}
</input>

<expected_behavior>
{expected_behavior}
</expected_behavior>

<response_1>
{response_1}
</response_1>

<response_2>
{response_2}
</response_2>

Which response better satisfies the expected behavior? Briefly justify (2-3
sentences), then end your reply with exactly one final line in this format:

VERDICT: 1
VERDICT: 2
VERDICT: TIE
"""


def load_cases(path: str) -> list[dict]:
    """Load and validate the JSONL case file."""
    cases: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                except json.JSONDecodeError as exc:
                    sys.exit(f"ERROR: {path}:{lineno} is not valid JSON: {exc}")
                if not isinstance(case, dict) or "input" not in case or "expected_behavior" not in case:
                    sys.exit(
                        f"ERROR: {path}:{lineno} must be an object with "
                        f"'input' and 'expected_behavior' keys"
                    )
                cases.append(case)
    except OSError as exc:
        sys.exit(f"ERROR: cannot read case file: {exc}")
    if not cases:
        sys.exit(f"ERROR: no cases found in {path}")
    return cases


def read_prompt(path: str, label: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
    except OSError as exc:
        sys.exit(f"ERROR: cannot read prompt {label} ({path}): {exc}")
    if not text:
        sys.exit(f"ERROR: prompt {label} ({path}) is empty")
    return text


def preview(text: str, width: int = 90) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 3] + "..."


def make_client():
    """Create the Anthropic client, with graceful errors for missing deps/key."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY is not set.\n"
            "Export it (export ANTHROPIC_API_KEY=sk-ant-...) or use --dry-run "
            "to preview the run without API calls.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        import anthropic
    except ImportError:
        print(
            "ERROR: the 'anthropic' package is not installed.\n"
            "Run: pip install anthropic  (or use --dry-run, which needs no SDK)",
            file=sys.stderr,
        )
        sys.exit(2)
    return anthropic, anthropic.Anthropic()


def call_model(
    anthropic_mod,
    client,
    model: str,
    system: str,
    user_content: str,
    max_tokens: int,
    max_retries: int = 3,
) -> str:
    """One sequential API call with basic rate-limit/5xx retries."""
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            # Join text blocks; skip thinking blocks.
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
        except anthropic_mod.RateLimitError as exc:
            last_exc = exc
            retry_after = 30
            try:
                retry_after = int(exc.response.headers.get("retry-after", "30"))
            except (AttributeError, ValueError):
                pass
            print(f"    rate limited; retrying in {retry_after}s", file=sys.stderr)
            time.sleep(retry_after)
        except anthropic_mod.APIStatusError as exc:
            if exc.status_code >= 500:
                last_exc = exc
                wait = 5 * (attempt + 1)
                print(f"    server error {exc.status_code}; retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"giving up after {max_retries} attempts: {last_exc}")


def parse_verdict(judge_text: str) -> str | None:
    """Return '1', '2', or 'TIE' from the judge's final VERDICT line."""
    for line in reversed(judge_text.strip().splitlines()):
        line = line.strip()
        if line.upper().startswith(VERDICT_PREFIX):
            value = line[len(VERDICT_PREFIX):].strip().upper().rstrip(".")
            if value in ("1", "2", "TIE"):
                return value
    return None


def unified_diff(a: str, b: str, max_lines: int = 30) -> list[str]:
    lines = list(
        difflib.unified_diff(
            a.splitlines(), b.splitlines(), fromfile="variant_a", tofile="variant_b", lineterm=""
        )
    )
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... diff truncated ({len(lines) - max_lines} more lines)"]
    return lines


def dry_run(cases: list[dict], args, orders: list[bool]) -> None:
    n = len(cases)
    print("DRY RUN - no API calls will be made.\n")
    print(f"Candidate model: {args.model}   (max_tokens={args.max_tokens})")
    print(f"Judge model:     {args.judge_model}   (max_tokens={args.judge_max_tokens})")
    print(f"Prompt A: {args.prompt_a}")
    print(f"Prompt B: {args.prompt_b}")
    print(f"Cases:    {n} from {args.cases}")
    print(f"API calls that would run: {2 * n} candidate + {n} judge = {3 * n} total,")
    print(f"sequential with a {args.sleep:.1f}s sleep between calls (seed={args.seed}).\n")
    for i, (case, a_first) in enumerate(zip(cases, orders), 1):
        order = "A shown as response 1" if a_first else "B shown as response 1"
        print(f"Case {i}: {preview(case['input'])}")
        print(f"  expected_behavior: {preview(case['expected_behavior'])}")
        print(f"  judge order: {order}")
    print("\nRe-run without --dry-run (with ANTHROPIC_API_KEY set) to execute.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="A/B eval harness: compare two prompt variants with a judge-based win rate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("cases", help="JSONL file of {'input': ..., 'expected_behavior': ...} cases")
    parser.add_argument("--prompt-a", required=True, help="file containing system prompt variant A")
    parser.add_argument("--prompt-b", required=True, help="file containing system prompt variant B")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="candidate model for both variants")
    parser.add_argument("--judge-model", default=DEFAULT_MODEL, help="judge model")
    parser.add_argument("--max-tokens", type=int, default=1024, help="max_tokens per candidate call")
    parser.add_argument(
        "--judge-max-tokens", type=int, default=1024, help="max_tokens per judge call"
    )
    parser.add_argument(
        "--sleep", type=float, default=1.0, help="seconds to sleep between API calls"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="seed for per-case judge position randomization"
    )
    parser.add_argument("--output", default=None, help="write full results as JSON to this path")
    parser.add_argument(
        "--dry-run", action="store_true", help="print what would run; no API calls, no SDK needed"
    )
    args = parser.parse_args()

    cases = load_cases(args.cases)
    # Per-case presentation order, deterministic for a given seed:
    # True -> variant A is shown to the judge as response_1.
    rng = random.Random(args.seed)
    orders = [rng.random() < 0.5 for _ in cases]

    if args.dry_run:
        # Validate the prompts exist even in dry-run so a typo surfaces early.
        read_prompt(args.prompt_a, "A")
        read_prompt(args.prompt_b, "B")
        dry_run(cases, args, orders)
        return 0

    prompt_a = read_prompt(args.prompt_a, "A")
    prompt_b = read_prompt(args.prompt_b, "B")
    anthropic_mod, client = make_client()

    wins = {"A": 0, "B": 0, "TIE": 0, "UNPARSED": 0}
    results: list[dict] = []

    for i, (case, a_first) in enumerate(zip(cases, orders), 1):
        print(f"\n=== Case {i}/{len(cases)}: {preview(case['input'])}")

        response_a = call_model(
            anthropic_mod, client, args.model, prompt_a, case["input"], args.max_tokens
        )
        time.sleep(args.sleep)
        response_b = call_model(
            anthropic_mod, client, args.model, prompt_b, case["input"], args.max_tokens
        )
        time.sleep(args.sleep)

        print(f"  A: {preview(response_a)}")
        print(f"  B: {preview(response_b)}")
        diff_lines = unified_diff(response_a, response_b)
        if diff_lines:
            print("  diff (A -> B):")
            for line in diff_lines:
                print(f"    {line}")
        else:
            print("  responses are identical")

        first, second = (response_a, response_b) if a_first else (response_b, response_a)
        judge_prompt = JUDGE_TEMPLATE.format(
            case_input=case["input"],
            expected_behavior=case["expected_behavior"],
            response_1=first,
            response_2=second,
        )
        judge_text = call_model(
            anthropic_mod, client, args.judge_model, JUDGE_SYSTEM, judge_prompt,
            args.judge_max_tokens,
        )
        time.sleep(args.sleep)

        raw_verdict = parse_verdict(judge_text)
        if raw_verdict is None:
            winner = "UNPARSED"
        elif raw_verdict == "TIE":
            winner = "TIE"
        elif raw_verdict == "1":
            winner = "A" if a_first else "B"
        else:  # "2"
            winner = "B" if a_first else "A"
        wins[winner] += 1

        order_note = "A=response_1" if a_first else "B=response_1"
        print(f"  judge ({order_note}): {winner}")

        results.append(
            {
                "case_index": i,
                "input": case["input"],
                "expected_behavior": case["expected_behavior"],
                "response_a": response_a,
                "response_b": response_b,
                "a_shown_first": a_first,
                "judge_raw": judge_text,
                "winner": winner,
            }
        )

    n = len(cases)
    judged = n - wins["UNPARSED"]
    print("\n" + "=" * 60)
    print(f"Win rate over {n} cases (judge: {args.judge_model}):")
    print(f"  A wins:  {wins['A']}/{n} ({wins['A'] / n:.0%})")
    print(f"  B wins:  {wins['B']}/{n} ({wins['B'] / n:.0%})")
    print(f"  Ties:    {wins['TIE']}/{n}")
    if wins["UNPARSED"]:
        print(f"  Unparsed judge verdicts (excluded): {wins['UNPARSED']}")
    if judged and abs(wins["A"] - wins["B"]) <= max(1, n // 5):
        print(
            "  Note: with this few cases, a gap this small is within noise - "
            "treat it as a tie or add cases (see references/evals.md)."
        )

    if args.output:
        summary = {
            "model": args.model,
            "judge_model": args.judge_model,
            "prompt_a": args.prompt_a,
            "prompt_b": args.prompt_b,
            "seed": args.seed,
            "wins": wins,
            "cases": results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\nFull results written to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
