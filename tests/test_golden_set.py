"""Golden-set eval harness — deterministic checks + optional LLM runs.

Markers:
  @pytest.mark.llm  — live chain.invoke() over golden set (≥90% gate)
  (no marker)       — schema/structure tests only

Scorecard: CI/CD + offline parity; uses eval_checks.score_case.
"""

from __future__ import annotations

import os

import pytest

from llm_log_triage.chain import invoke
from llm_log_triage.eval_checks import score_case
from llm_log_triage.schema import Severity

PASS_THRESHOLD = 0.90


@pytest.mark.llm
def test_golden_set_pass_rate(normal_cases):
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key configured")

    passed = 0
    failures = []
    for case in normal_cases:
        result = invoke(case["log_text"], case.get("service_name"), use_cache=True, interface="pytest")
        checks = score_case(result, case["expected"])
        if checks["passed"]:
            passed += 1
        else:
            failures.append({"id": case["id"], "checks": checks})

    rate = passed / len(normal_cases)
    assert rate >= PASS_THRESHOLD, f"Pass rate {rate:.0%} < {PASS_THRESHOLD:.0%}. Failures: {failures[:3]}"


@pytest.mark.llm
def test_adversarial_cases(adversarial_cases):
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key configured")

    for case in adversarial_cases:
        result = invoke(case["log_text"], case.get("service_name"), use_cache=True, interface="pytest")
        checks = score_case(result, case["expected"])
        assert checks.get("adversarial", False), f"{case['id']} failed adversarial checks: {checks}"


@pytest.mark.smoke
@pytest.mark.llm
def test_smoke_single_invoke():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    result = invoke(
        "2026-05-28T14:02:11Z ERROR payments-api connection refused postgres",
        "payments-api",
        use_cache=True,
        interface="pytest",
    )
    assert result.output.severity in (Severity.SEV2, Severity.SEV1, Severity.SEV3)
    assert result.latency_ms >= 0 or result.cached
