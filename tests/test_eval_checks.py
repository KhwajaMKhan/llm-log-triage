"""eval_checks unit tests — mirrors pytest golden-set scoring (no LLM).

Validates score_case() for normal and adversarial expected dicts.
Charter eval spec #2–3, #5.
"""

from llm_log_triage.eval_checks import score_case, split_cases


def test_score_case_normal_pass():
    from llm_log_triage.schema import Category, Severity, TriageOutput

    class FakeResult:
        output = TriageOutput(
            severity=Severity.SEV2,
            category=Category.CONNECTIVITY,
            likely_cause="postgres connection refused",
            suggested_action="check postgres connectivity",
            confidence=0.9,
            evidence_lines=["connection refused"],
        )

    checks = score_case(
        FakeResult(),
        {
            "severity": "SEV2",
            "category": "connectivity",
            "must_mention": ["postgres", "connection refused"],
        },
    )
    assert checks["passed"] is True


def test_split_cases_counts():
    cases = [
        {"expected": {"adversarial": False}},
        {"expected": {"adversarial": True}},
    ]
    normal, adv = split_cases(cases)
    assert len(normal) == 1
    assert len(adv) == 1
