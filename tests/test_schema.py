"""Deterministic schema and golden-set structure tests (no LLM)."""

import json
from pathlib import Path

import pytest

from llm_log_triage.schema import Category, Severity, TriageInput, TriageOutput

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "data" / "golden_set.json"


def test_golden_set_loads():
    data = json.loads(GOLDEN_PATH.read_text())
    assert data["version"] == "1.0"
    cases = data["cases"]
    assert 20 <= len([c for c in cases if not c["expected"].get("adversarial")]) <= 25
    assert 3 <= len([c for c in cases if c["expected"].get("adversarial")]) <= 5


def test_golden_set_case_ids_unique():
    data = json.loads(GOLDEN_PATH.read_text())
    ids = [c["id"] for c in data["cases"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "severity",
    ["SEV1", "SEV2", "SEV3", "SEV4", "unknown"],
)
def test_severity_enum(severity):
    assert Severity(severity)


def test_triage_output_valid():
    out = TriageOutput(
        severity=Severity.SEV2,
        category=Category.CONNECTIVITY,
        likely_cause="DB unreachable",
        suggested_action="Check postgres connectivity",
        confidence=0.85,
        evidence_lines=["connection refused"],
    )
    assert out.severity == Severity.SEV2


def test_triage_input_strips():
    inp = TriageInput(log_text="  hello  ", service_name="svc")
    assert inp.log_text == "hello"
