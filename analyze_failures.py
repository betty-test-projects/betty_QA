"""
analyze_failures.py

Reads pytest-output.txt, extracts failed test blocks,
calls Claude API for bug vs flaky analysis,
and prints the result to CI log.
"""

import os
import sys
import re
import anthropic

REPORT_PATH = "reports/pytest-output.txt"
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap for CI analysis


# ── 1. Read report ────────────────────────────────────────────────────────────

def read_report(path: str) -> str:
    if not os.path.exists(path):
        print(f"[analyze] ERROR: Report file not found at '{path}'")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── 2. Extract summary line ───────────────────────────────────────────────────

def extract_summary(text: str) -> str:
    """Extract the final pytest summary line, e.g. '3 failed, 10 passed in 5.2s'"""
    for line in reversed(text.splitlines()):
        if re.search(r"(passed|failed|error)", line, re.IGNORECASE):
            return line.strip().strip("=").strip()
    return "Summary not found"


# ── 3. Extract failed blocks ──────────────────────────────────────────────────

def extract_failed_blocks(text: str) -> list[dict]:
    """
    Parse pytest output and return a list of dicts:
      { "test_id": str, "error_block": str }

    Handles two common pytest output sections:
      - FAILURES section (detailed traceback per test)
      - Short FAILED lines when --tb=no is used
    """
    failed_tests = []

    # ── Strategy A: parse the FAILURES section (detailed tracebacks) ──────────
    # Pytest wraps each failure like:
    #   _________________________ test_name _________________________
    #   ... traceback ...
    #   E   AssertionError: ...
    #   (blank line or next divider)

    failures_section_match = re.search(
        r"={3,}\s*FAILURES\s*={3,}(.*?)(?:={3,}|\Z)",
        text,
        re.DOTALL,
    )

    if failures_section_match:
        section = failures_section_match.group(1)

        # Split on the underline dividers that separate individual failures
        # e.g. "_______ test_something _______"
        blocks = re.split(r"_{5,}.*?_{5,}", section)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # First non-empty line is usually the test id
            lines = [l for l in block.splitlines() if l.strip()]
            if not lines:
                continue

            test_id = lines[0].strip()

            # Keep only the most relevant lines to save tokens:
            # error lines (starting with E), assert lines, and last few context lines
            error_lines = [l for l in block.splitlines() if re.match(r"\s*E\s+", l)]
            context_lines = block.splitlines()[-10:]  # last 10 lines for context

            trimmed = "\n".join(error_lines or context_lines)

            failed_tests.append({
                "test_id": test_id,
                "error_block": trimmed[:1500],  # cap at 1500 chars per test
            })

    # ── Strategy B: fallback — scan for "FAILED" lines ───────────────────────
    # Used when tracebacks are minimal or --tb=short produced no FAILURES section
    if not failed_tests:
        for line in text.splitlines():
            if line.strip().startswith("FAILED"):
                # e.g. "FAILED tests/test_create_task.py::test_add_task - AssertionError"
                parts = line.strip().split(" - ", 1)
                test_id = parts[0].replace("FAILED", "").strip()
                error_msg = parts[1] if len(parts) > 1 else "No detail available"
                failed_tests.append({
                    "test_id": test_id,
                    "error_block": error_msg[:1500],
                })

    return failed_tests


# ── 4. Build prompt ───────────────────────────────────────────────────────────

def build_prompt(failed_tests: list[dict], summary: str) -> str:
    failures_text = ""
    for i, t in enumerate(failed_tests, 1):
        failures_text += f"""
--- Failure {i} ---
Test: {t['test_id']}
Error:
{t['error_block']}
"""

    return f"""You are a QA analyst reviewing automated test failures from a CI pipeline.

The test suite runs against a simple Flask Task Manager app with a SQLite database.
Tests use pytest + Playwright (UI tests) and requests (API tests).

## Run summary
{summary}

## Failed tests
{failures_text}

## Your task
For each failed test, assess:
1. Is this likely a REAL BUG (consistent, reproducible, points to a code defect)?
2. Or is this likely a FLAKY TEST (timing issue, environment instability, selector fragility)?

Then give an overall recommendation:
- APPROVE: failures look like flaky tests, safe to re-run or ignore
- REJECT: at least one failure looks like a real bug, needs investigation

## Response format
Reply in this exact structure:

### Analysis per test
[For each failure: test name, verdict (BUG / FLAKY), one-sentence reasoning]

### Overall verdict
APPROVE or REJECT

### Reasoning
2-3 sentences explaining the overall decision.
"""


# ── 5. Call Claude API ────────────────────────────────────────────────────────

def call_claude(prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[analyze] ERROR: ANTHROPIC_API_KEY environment variable is not set")
        sys.exit(1)

    print("[analyze] Calling Claude API for failure analysis...")
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


# ── 6. Print result ───────────────────────────────────────────────────────────

def print_result(analysis: str, failed_count: int, summary: str):
    separator = "=" * 60
    print(f"\n{separator}")
    print("  Claude AI — Test Failure Analysis")
    print(separator)
    print(f"  Summary : {summary}")
    print(f"  Failures: {failed_count} test(s) analysed")
    print(separator)
    print(analysis)
    print(f"{separator}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"[analyze] Reading report from: {REPORT_PATH}")
    text = read_report(REPORT_PATH)

    summary = extract_summary(text)
    print(f"[analyze] Summary: {summary}")

    # If no failures, skip API call
    if "failed" not in summary.lower() and "error" not in summary.lower():
        print("[analyze] No failures detected — skipping Claude analysis.")
        sys.exit(0)

    failed_tests = extract_failed_blocks(text)
    print(f"[analyze] Extracted {len(failed_tests)} failure block(s)")

    if not failed_tests:
        print("[analyze] WARNING: Failures detected in summary but no blocks extracted.")
        print("[analyze] Sending raw summary to Claude for basic analysis.")
        failed_tests = [{"test_id": "unknown", "error_block": summary}]

    prompt = build_prompt(failed_tests, summary)
    analysis = call_claude(prompt)

    print_result(analysis, len(failed_tests), summary)


if __name__ == "__main__":
    main()