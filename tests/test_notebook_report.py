"""Notebook report writer unit tests (no LLM)."""

import json
from pathlib import Path

from llm_log_triage.judge import JudgeScore
from llm_log_triage.notebook_report import (
    NOTEBOOK_INTERFACE,
    NotebookSession,
    build_run_row,
    build_session_report,
    resolve_report_dir,
    write_notebook_report,
)
from llm_log_triage.schema import Category, Severity, TriageOutput


def test_build_run_row_includes_interface():
    triage = TriageOutput(
        severity=Severity.SEV2,
        category=Category.CONNECTIVITY,
        likely_cause="db down",
        suggested_action="check db",
        confidence=0.9,
        evidence_lines=["err"],
    )
    row = build_run_row(
        section="good_case",
        case_id="gs-001",
        log_text="ERROR db",
        service_name="api",
        triage=triage,
        deterministic_checks={"passed": True},
    )
    assert row["interface"] == NOTEBOOK_INTERFACE
    assert row["section"] == "good_case"


def test_session_record_writes_latest(tmp_path):
    session = NotebookSession(report_dir=tmp_path)
    session.record(
        build_run_row(
            section="good_case",
            case_id="gs-001",
            log_text="ERROR",
            service_name="api",
            judge_score=JudgeScore(coherence=5, actionability=5, rationale="ok"),
        )
    )
    latest = tmp_path / "notebook-latest.json"
    assert latest.exists()
    data = json.loads(latest.read_text())
    assert data["runs_count"] == 1
    assert data["interface"] == "notebook"
    assert len(list(tmp_path.glob("notebook-*.json"))) == 2


def test_write_notebook_report(tmp_path):
    report = build_session_report("2026-01-01T00:00:00+00:00", [])
    path = write_notebook_report(report, tmp_path)
    assert path.name == "notebook-latest.json"


def test_resolve_report_dir_from_notebooks_cwd(monkeypatch):
    """Reports must land in repo-root docs/, not notebooks/docs/."""
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root / "notebooks")
    resolved = resolve_report_dir()
    assert resolved == root / "docs" / "eval-runs"
