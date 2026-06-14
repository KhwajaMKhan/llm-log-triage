"""Judge report + pass/fail logic (no LLM)."""

import json

import pytest

from llm_log_triage.judge import JudgeScore, passes_judge
from llm_log_triage.judge_report import (
    build_case_result,
    build_report,
    write_fail_smoke_report,
    write_judge_report,
)
from llm_log_triage.schema import Category, Severity, TriageOutput


def test_passes_judge_accepts_at_threshold():
    score = JudgeScore(coherence=4, actionability=4, rationale="Meets bar.")
    assert passes_judge(score)


@pytest.mark.parametrize(
    "coherence,actionability",
    [(3, 5), (5, 3), (2, 2)],
)
def test_passes_judge_fails_when_either_dimension_low(coherence, actionability):
    score = JudgeScore(
        coherence=coherence,
        actionability=actionability,
        rationale="Below bar on at least one dimension.",
    )
    assert not passes_judge(score)


def test_build_report_overall_fail_when_pass_rate_low():
    report = build_report(
        [
            {"id": "gs-001", "passed": True},
            {"id": "gs-002", "passed": False},
            {"id": "gs-003", "passed": False},
        ],
        pass_rate_threshold=0.9,
    )
    assert report["cases_passed"] == 1
    assert report["pass_rate"] == pytest.approx(0.3333, rel=1e-3)
    assert report["overall_pass"] is False


def test_build_case_result_marks_failed():
    triage = TriageOutput(
        severity=Severity.SEV4,
        category=Category.UNKNOWN,
        likely_cause="Unrelated noise.",
        suggested_action="Ignore the log.",
        confidence=0.2,
        evidence_lines=[],
    )
    score = JudgeScore(coherence=2, actionability=1, rationale="Not actionable.")
    row = build_case_result("gs-fail", "payments-api", "ERROR db down", triage, score)
    assert row["passed"] is False
    assert row["judge"]["coherence"] == 2


def test_write_fail_smoke_report(tmp_path):
    triage = TriageOutput(
        severity=Severity.SEV4,
        category=Category.UNKNOWN,
        likely_cause="No issue detected.",
        suggested_action="No action required.",
        confidence=0.1,
        evidence_lines=[],
    )
    score = JudgeScore(coherence=1, actionability=1, rationale="Contradicts log.")
    path = write_fail_smoke_report(
        "judge-fail-smoke",
        "payments-api",
        "ERROR connection refused",
        triage,
        score,
        tmp_path,
    )
    assert path.name == "judge-fail-smoke-latest.json"
    assert path.exists()
    report = json.loads(path.read_text())
    assert report["case_id"] == "judge-fail-smoke"
    assert report["passed"] is False


def test_write_judge_report(tmp_path):
    report = build_report(
        [
            {
                "id": "gs-001",
                "service_name": "payments-api",
                "log_preview": "ERROR connection refused",
                "triage": {"severity": "SEV2", "category": "connectivity"},
                "judge": {"coherence": 5, "actionability": 4, "rationale": "Clear triage."},
                "passed": True,
            }
        ],
        pass_rate_threshold=0.9,
    )
    path = write_judge_report(report, tmp_path)
    assert path.name == "judge-latest.json"
    assert path.exists()
    stamped = list(tmp_path.glob("judge-*.json"))
    assert len(stamped) == 2  # stamped + latest (same content, two files)
