"""JSON reports for notebook live runs (mirrors pytest judge-latest pattern).

Writes docs/eval-runs/notebook-latest.json after each notebook session.
Reports written to docs/eval-runs/notebook-latest.json (+ timestamped copies).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from llm_log_triage.judge import passes_judge
from llm_log_triage.notebook_setup import find_repo_root
from llm_log_triage.schema import TriageOutput

NOTEBOOK_INTERFACE = "notebook"
REPORT_DIR_REL = Path("docs/eval-runs")
NOTEBOOK_LATEST_NAME = "notebook-latest.json"


def resolve_report_dir(report_dir: Path | None = None) -> Path:
    """Anchor report paths to repo root (Jupyter cwd is often notebooks/)."""
    if report_dir is not None:
        return report_dir if report_dir.is_absolute() else find_repo_root() / report_dir
    env = os.getenv("LOG_TRIAGE_NOTEBOOK_REPORT_DIR")
    if env:
        p = Path(env)
        return p if p.is_absolute() else find_repo_root() / p
    return find_repo_root() / REPORT_DIR_REL


def triage_to_dict(triage: TriageOutput) -> dict:
    return {
        "severity": triage.severity.value,
        "category": triage.category.value,
        "likely_cause": triage.likely_cause,
        "suggested_action": triage.suggested_action,
        "confidence": triage.confidence,
        "evidence_lines": triage.evidence_lines,
    }


def judge_to_dict(score) -> dict:
    return {
        "coherence": score.coherence,
        "actionability": score.actionability,
        "rationale": score.rationale,
        "passed": passes_judge(score),
    }


def build_run_row(
    *,
    section: str,
    case_id: str,
    log_text: str,
    service_name: str | None,
    triage: TriageOutput | None = None,
    result=None,
    deterministic_checks: dict | None = None,
    judge_score=None,
    injected_triage: bool = False,
    batch_cases: list[dict] | None = None,
    batch_summary: dict | None = None,
) -> dict:
    """One notebook execution row."""
    row: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "section": section,
        "case_id": case_id,
        "interface": NOTEBOOK_INTERFACE,
        "service_name": service_name,
        "log_preview": log_text[:200] if log_text else "",
        "injected_triage": injected_triage,
    }
    if result is not None:
        row["meta"] = {
            "latency_ms": round(result.latency_ms, 1),
            "cached": result.cached,
            "model": result.model,
            "prompt_version": result.prompt_version,
        }
    if triage is not None:
        row["triage"] = triage_to_dict(triage)
    if deterministic_checks is not None:
        row["deterministic_checks"] = deterministic_checks
        row["passed_deterministic"] = deterministic_checks.get("passed")
    if judge_score is not None:
        row["judge"] = judge_to_dict(judge_score)
        row["passed_judge"] = row["judge"]["passed"]
    if batch_cases is not None:
        row["batch_cases"] = batch_cases
    if batch_summary is not None:
        row["batch_summary"] = batch_summary
    return row


def build_session_report(session_started: str, runs: list[dict]) -> dict:
    det_passed = sum(1 for r in runs if r.get("passed_deterministic") is True)
    det_scored = sum(1 for r in runs if r.get("passed_deterministic") is not None)
    judge_passed = sum(1 for r in runs if r.get("passed_judge") is True)
    judge_scored = sum(1 for r in runs if r.get("passed_judge") is not None)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_started": session_started,
        "interface": NOTEBOOK_INTERFACE,
        "runs_count": len(runs),
        "deterministic_passed": det_passed,
        "deterministic_scored": det_scored,
        "judge_passed": judge_passed,
        "judge_scored": judge_scored,
        "runs": runs,
    }


def write_notebook_report(report: dict, report_dir: Path | None = None) -> Path:
    """Write notebook-latest.json + timestamped copy. Returns path to latest."""
    directory = resolve_report_dir(report_dir)
    directory.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stamped = directory / f"notebook-{stamp}.json"
    latest = directory / NOTEBOOK_LATEST_NAME

    payload = json.dumps(report, indent=2)
    stamped.write_text(payload)
    latest.write_text(payload)
    return latest


class NotebookSession:
    """Accumulates live notebook runs and flushes JSON after each execution."""

    def __init__(self, report_dir: Path | None = None) -> None:
        self.report_dir = report_dir
        self.session_started = datetime.now(timezone.utc).isoformat()
        self.runs: list[dict] = []

    def reset(self) -> None:
        self.session_started = datetime.now(timezone.utc).isoformat()
        self.runs = []

    def record(self, row: dict) -> Path:
        self.runs.append(row)
        report = build_session_report(self.session_started, self.runs)
        return write_notebook_report(report, self.report_dir)

    @property
    def latest_path(self) -> Path:
        return resolve_report_dir(self.report_dir) / NOTEBOOK_LATEST_NAME
