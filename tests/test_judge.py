"""LLM-as-Judge evals — coherence + actionability ≥ 4/5 (charter eval spec #4).

Two-step eval per case:
  1. invoke() — triage model produces JSON (may use .cache/llm-log-triage/)
  2. judge_triage() — reviewer model scores that JSON (always a live LLM call)

Run: pytest tests/ -m judge -v -s
Report: docs/eval-runs/judge-latest.json (written every pass-rate run)
"""

from __future__ import annotations

import os
import sys

import pytest

from llm_log_triage.chain import invoke
from llm_log_triage.judge import JUDGE_MODEL, PASS_THRESHOLD, judge_triage, passes_judge
from llm_log_triage.judge_report import (
    build_case_result,
    build_report,
    write_fail_smoke_report,
    write_judge_report,
)

FAIL_SMOKE_CASE_ID = "judge-fail-smoke"

JUDGE_PASS_RATE = 0.90


def _max_cases() -> int | None:
    """Limit judge runs to control API cost. Default 5; set LOG_TRIAGE_JUDGE_MAX_CASES=all for 22."""
    raw = os.getenv("LOG_TRIAGE_JUDGE_MAX_CASES", "5")
    if raw.lower() == "all":
        return None
    return int(raw)


def _run_judge_cases(cases: list[dict]) -> tuple[list[dict], dict]:
    """Run triage + judge for each case; return per-case rows and full report dict."""
    case_results = []
    for case in cases:
        result = invoke(
            case["log_text"],
            case.get("service_name"),
            use_cache=True,
            interface="pytest",
            case_id=case["id"],
        )
        score = judge_triage(
            case["log_text"],
            result.output,
            interface="pytest",
            case_id=case["id"],
        )
        case_results.append(
            build_case_result(
                case["id"],
                case.get("service_name"),
                case["log_text"],
                result.output,
                score,
            )
        )

    report = build_report(
        case_results,
        judge_model=JUDGE_MODEL,
        pass_threshold=PASS_THRESHOLD,
        pass_rate_threshold=JUDGE_PASS_RATE,
    )
    return case_results, report


@pytest.mark.llm
@pytest.mark.judge
def test_judge_pass_rate(normal_cases):
    """Run triage + judge on N golden-set cases; require >=90% to pass judge."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key configured")

    cap = _max_cases()
    cases = normal_cases if cap is None else normal_cases[:cap]

    case_results, report = _run_judge_cases(cases)
    report_path = write_judge_report(report)

    print(f"\nJudge report written: {report_path}", file=sys.stderr)
    print(
        f"  {report['cases_passed']}/{report['cases_run']} passed "
        f"({report['pass_rate']:.0%})",
        file=sys.stderr,
    )

    failures = [c for c in case_results if not c["passed"]]
    rate = report["pass_rate"]
    assert rate >= JUDGE_PASS_RATE, (
        f"Judge pass rate {rate:.0%} < {JUDGE_PASS_RATE:.0%} "
        f"(threshold={PASS_THRESHOLD}/5, model={JUDGE_MODEL}, n={len(cases)}). "
        f"Report: {report_path}. Failures: {failures[:3]}"
    )


@pytest.mark.llm
@pytest.mark.judge
def test_judge_single_sample():
    """Quick sanity: one log must pass judge with scores >= 4/4."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    log = "2026-05-28T14:02:11Z ERROR payments-api Failed to connect to postgres - connection refused"
    result = invoke(log, "payments-api", use_cache=True, interface="pytest")
    score = judge_triage(log, result.output, interface="pytest", case_id="smoke")

    assert score.coherence >= 1
    assert score.actionability >= 1
    assert passes_judge(score), f"Judge scores: {score.model_dump()}"


@pytest.mark.llm
@pytest.mark.judge
def test_judge_rejects_deliberately_bad_triage():
    """Prove the judge gate can fail: garbage triage vs a real error log."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from llm_log_triage.schema import Category, Severity, TriageOutput

    log = (
        "2026-05-28T14:02:11Z ERROR payments-api pid=4421 "
        "Failed to connect to postgres://payments-db:5432 - connection refused"
    )
    bad = TriageOutput(
        severity=Severity.SEV4,
        category=Category.UNKNOWN,
        likely_cause="No issue detected; log looks healthy.",
        suggested_action="No action required.",
        confidence=0.1,
        evidence_lines=[],
    )
    score = judge_triage(log, bad, interface="pytest", case_id=FAIL_SMOKE_CASE_ID)
    report_path = write_fail_smoke_report(
        FAIL_SMOKE_CASE_ID,
        "payments-api",
        log,
        bad,
        score,
    )
    print(f"\nFail smoke report written: {report_path}", file=sys.stderr)
    assert not passes_judge(score), (
        f"Expected judge to reject contradictory triage; got {score.model_dump()}. "
        f"Report: {report_path}"
    )
