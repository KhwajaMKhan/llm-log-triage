"""Notebook live-run helpers — always interface=notebook + JSON report.

Thin wrapper over chain.invoke() for explore.ipynb cells.
Each RUN_* cell calls these functions; results append to notebook-latest.json.
Same eval_checks as pytest — offline parity with CI.
"""

from __future__ import annotations

from llm_log_triage.chain import invoke
from llm_log_triage.eval_checks import score_case
from llm_log_triage.judge import judge_triage, passes_judge
from llm_log_triage.notebook_report import (
    NOTEBOOK_INTERFACE,
    NotebookSession,
    build_run_row,
)
from llm_log_triage.schema import TriageOutput

# Module-level session; reset in notebook setup cell.
_session = NotebookSession()


def get_session() -> NotebookSession:
    return _session


def reset_session() -> NotebookSession:
    _session.reset()
    return _session


def _record(row: dict) -> Path:
    return _session.record(row)


def run_triage(
    log_text: str,
    service_name: str | None,
    *,
    case_id: str,
    section: str,
    use_cache: bool = True,
):
    """Single triage call — LangSmith tag interface:notebook."""
    return invoke(
        log_text,
        service_name,
        use_cache=use_cache,
        interface=NOTEBOOK_INTERFACE,
        case_id=case_id,
    )


def eval_golden_case(case: dict, *, section: str, use_cache: bool = True) -> tuple:
    """Triage + deterministic checks + report row."""
    result = run_triage(
        case["log_text"],
        case.get("service_name"),
        case_id=case["id"],
        section=section,
        use_cache=use_cache,
    )
    checks = score_case(result, case["expected"])
    path = _record(
        build_run_row(
            section=section,
            case_id=case["id"],
            log_text=case["log_text"],
            service_name=case.get("service_name"),
            triage=result.output,
            result=result,
            deterministic_checks=checks,
        )
    )
    return result, checks, path


def run_custom_log(
    log_text: str,
    service_name: str | None,
    *,
    section: str = "custom",
    case_id: str = "custom",
    use_cache: bool = True,
) -> tuple:
    """Ad-hoc log — no golden labels."""
    result = run_triage(
        log_text,
        service_name,
        case_id=case_id,
        section=section,
        use_cache=use_cache,
    )
    path = _record(
        build_run_row(
            section=section,
            case_id=case_id,
            log_text=log_text,
            service_name=service_name,
            triage=result.output,
            result=result,
        )
    )
    return result, path


def eval_with_judge(case: dict, *, section: str = "judge", use_cache: bool = True) -> tuple:
    """Triage + deterministic + judge + one report row."""
    result = run_triage(
        case["log_text"],
        case.get("service_name"),
        case_id=case["id"],
        section=section,
        use_cache=use_cache,
    )
    checks = score_case(result, case["expected"])
    score = judge_triage(
        case["log_text"],
        result.output,
        interface=NOTEBOOK_INTERFACE,
        case_id=case["id"],
    )
    path = _record(
        build_run_row(
            section=section,
            case_id=case["id"],
            log_text=case["log_text"],
            service_name=case.get("service_name"),
            triage=result.output,
            result=result,
            deterministic_checks=checks,
            judge_score=score,
        )
    )
    return result, checks, score, passes_judge(score), path


def run_judge_fail_proof(
    log_text: str,
    bad_triage: TriageOutput,
    *,
    section: str = "judge_fail",
    case_id: str = "judge-fail-smoke",
) -> tuple:
    """Judge only on injected bad triage."""
    score = judge_triage(
        log_text,
        bad_triage,
        interface=NOTEBOOK_INTERFACE,
        case_id=case_id,
    )
    path = _record(
        build_run_row(
            section=section,
            case_id=case_id,
            log_text=log_text,
            service_name=None,
            triage=bad_triage,
            judge_score=score,
            injected_triage=True,
        )
    )
    return score, passes_judge(score), path


def run_batch(cases: list[dict], *, section: str = "batch", use_cache: bool = True) -> tuple:
    """Run N golden cases; one summary row in the report (no per-case rows)."""
    rows = []
    for case in cases:
        result = run_triage(
            case["log_text"],
            case.get("service_name"),
            case_id=case["id"],
            section=section,
            use_cache=use_cache,
        )
        checks = score_case(result, case["expected"])
        rows.append({"id": case["id"], "passed": checks["passed"], "checks": checks})

    passed = sum(1 for r in rows if r["passed"])
    total = len(rows)
    rate = passed / total if total else 0.0
    summary = {
        "cases_run": total,
        "cases_passed": passed,
        "pass_rate": round(rate, 4),
    }
    path = _record(
        build_run_row(
            section=section,
            case_id=f"batch-{total}",
            log_text="",
            service_name=None,
            batch_cases=rows,
            batch_summary=summary,
        )
    )
    return rows, summary, path
