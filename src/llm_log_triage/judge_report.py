"""Write reviewable JSON reports after judge eval runs.

Produces judge-latest.json and judge-fail-smoke-latest.json under docs/eval-runs/.
Triggered by pytest -m judge (see tests/test_judge.py).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from llm_log_triage.judge import JUDGE_MODEL, PASS_THRESHOLD, passes_judge
from llm_log_triage.schema import TriageOutput

DEFAULT_REPORT_DIR = Path(
    os.getenv("LOG_TRIAGE_JUDGE_REPORT_DIR", "docs/eval-runs"),
)
FAIL_SMOKE_REPORT_NAME = "judge-fail-smoke-latest.json"


def build_case_result(
    case_id: str,
    service_name: str | None,
    log_text: str,
    triage: TriageOutput,
    score,
) -> dict:
    """One row in the judge report."""
    return {
        "id": case_id,
        "service_name": service_name,
        "log_preview": log_text[:200],
        "triage": {
            "severity": triage.severity.value,
            "category": triage.category.value,
            "likely_cause": triage.likely_cause,
            "suggested_action": triage.suggested_action,
            "confidence": triage.confidence,
        },
        "judge": {
            "coherence": score.coherence,
            "actionability": score.actionability,
            "rationale": score.rationale,
        },
        "passed": passes_judge(score),
    }


def build_report(
    case_results: list[dict],
    *,
    judge_model: str = JUDGE_MODEL,
    pass_threshold: int = PASS_THRESHOLD,
    pass_rate_threshold: float = 0.90,
) -> dict:
    passed = sum(1 for c in case_results if c["passed"])
    total = len(case_results)
    rate = passed / total if total else 0.0
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "judge_model": judge_model,
        "pass_threshold_per_dimension": pass_threshold,
        "pass_rate_threshold": pass_rate_threshold,
        "cases_run": total,
        "cases_passed": passed,
        "pass_rate": round(rate, 4),
        "overall_pass": rate >= pass_rate_threshold,
        "cases": case_results,
    }


def write_fail_smoke_report(
    case_id: str,
    service_name: str | None,
    log_text: str,
    triage: TriageOutput,
    score,
    report_dir: Path | None = None,
) -> Path:
    """Write single-case report when deliberate fail-proof judge test runs."""
    row = build_case_result(case_id, service_name, log_text, triage, score)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "judge_model": JUDGE_MODEL,
        "pass_threshold_per_dimension": PASS_THRESHOLD,
        "case_id": case_id,
        "passed": row["passed"],
        "service_name": row["service_name"],
        "log_preview": row["log_preview"],
        "triage": row["triage"],
        "judge": row["judge"],
    }
    directory = report_dir or DEFAULT_REPORT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / FAIL_SMOKE_REPORT_NAME
    path.write_text(json.dumps(report, indent=2))
    return path


def write_judge_report(report: dict, report_dir: Path | None = None) -> Path:
    """Write timestamped JSON + judge-latest.json. Returns path to latest file."""
    directory = report_dir or DEFAULT_REPORT_DIR
    directory.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    stamped = directory / f"judge-{stamp}.json"
    latest = directory / "judge-latest.json"

    payload = json.dumps(report, indent=2)
    stamped.write_text(payload)
    latest.write_text(payload)
    return latest
