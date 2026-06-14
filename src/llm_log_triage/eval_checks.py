"""Shared golden-set scoring — used by pytest, notebook, and LangSmith eval.

Charter eval spec:
  #1 schema (Pydantic in chain)
  #2 exact match severity + category
  #3 must_mention keywords in triage text
  #5 adversarial → unknown + low confidence

Fairness: this module is frozen across all 7 observability tools.
"""

from __future__ import annotations

from llm_log_triage.schema import Category, Severity


def check_must_mention(output_text: str, phrases: list[str]) -> bool:
    lower = output_text.lower()
    return all(p.lower() in lower for p in phrases)


def score_case(result, expected: dict) -> dict:
    """Deterministic eval checks (charter eval spec #1–3, #5).

    Args:
        result: InvokeResult-like object with `.output` (TriageOutput)
        expected: golden-set `expected` dict from golden_set.json
    Returns:
        dict of booleans + `passed` (all True required)
    """
    out = result.output
    checks = {
        "schema": True,
        "severity": out.severity.value == expected["severity"],
        "category": out.category.value == expected["category"],
        "must_mention": check_must_mention(
            " ".join([out.likely_cause, out.suggested_action, *out.evidence_lines]),
            expected.get("must_mention", []),
        ),
    }
    if expected.get("adversarial"):
        max_conf = expected.get("max_confidence", 0.4)
        checks["adversarial"] = (
            out.severity == Severity.UNKNOWN
            and out.category == Category.UNKNOWN
            and out.confidence <= max_conf
        )
    checks["passed"] = all(checks.values())
    return checks


def split_cases(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    normal = [c for c in cases if not c["expected"].get("adversarial")]
    adversarial = [c for c in cases if c["expected"].get("adversarial")]
    return normal, adversarial


def case_by_id(cases: list[dict], case_id: str) -> dict:
    for case in cases:
        if case["id"] == case_id:
            return case
    raise KeyError(f"Case {case_id!r} not in golden set")
