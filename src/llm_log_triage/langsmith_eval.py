"""LangSmith dataset sync + offline eval experiment.

WHAT GETS PUSHED TO LANGSMITH (not your repo source code):
  --sync-dataset  → inputs, reference outputs, metadata per golden-set row
  --run           → traces (spans) + experiment scores from local chain.invoke()

WHAT STAYS LOCAL:
  chain.py, prompts, eval_checks, evaluators — all run locally

Results appear under LangSmith → Datasets & Experiments (not Evaluators sidebar).

Run:
  python -m llm_log_triage.langsmith_eval --sync-dataset
  python -m llm_log_triage.langsmith_eval --run --max-cases 5
  python -m llm_log_triage.langsmith_eval --run --no-sync --dataset curated-dataset-2
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATASET = os.getenv("LOG_TRIAGE_LANGSMITH_DATASET", "log-triage-golden-set-v3")
DEFAULT_REPORT_DIR = Path(os.getenv("LOG_TRIAGE_LANGSMITH_EVAL_REPORT_DIR", "docs/eval-runs"))
GOLDEN_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_set.json"
EVAL_INTERFACE = "langsmith_eval"


def load_golden_cases(limit: int | None = None) -> list[dict]:
    """Read data/golden_set.json; optional limit for smoke runs."""
    data = json.loads(GOLDEN_PATH.read_text())
    cases = data["cases"]
    if limit is not None:
        return cases[:limit]
    return cases


def _parse_triage_output(run_outputs: dict | None):
    """Convert LangSmith run.outputs dict into a validated TriageOutput."""
    from llm_log_triage.schema import TriageOutput

    if not run_outputs:
        raise ValueError("run has no outputs")
    return TriageOutput.model_validate(run_outputs)


# --- Inline evaluators (not registered in LangSmith Evaluators UI) ---
# These run inside langsmith.evaluate() and appear as score columns on the experiment.


def golden_pass_evaluator(run, example) -> dict:
    """Row evaluator — 1 if score_case passes, else 0. Same logic as pytest."""
    from llm_log_triage.eval_checks import score_case

    expected = example.outputs["expected"]
    triage = _parse_triage_output(run.outputs)
    fake_result = type("InvokeResult", (), {"output": triage})()
    checks = score_case(fake_result, expected)
    return {
        "key": "golden_pass",
        "score": 1 if checks["passed"] else 0,
        "comment": json.dumps(checks),
    }


def severity_match_evaluator(run, example) -> dict:
    """Row evaluator — 1 if severity string equals golden label."""
    expected = example.outputs["expected"]["severity"]
    actual = (run.outputs or {}).get("severity")
    return {"key": "severity_match", "score": 1 if actual == expected else 0}


def category_match_evaluator(run, example) -> dict:
    """Row evaluator — 1 if category string equals golden label."""
    expected = example.outputs["expected"]["category"]
    actual = (run.outputs or {}).get("category")
    return {"key": "category_match", "score": 1 if actual == expected else 0}


def pass_rate_summary_evaluator(runs, examples) -> dict:
    """Experiment-level pass rate (mirrors pytest threshold)."""
    scores = []
    for run, example in zip(runs, examples):
        row = golden_pass_evaluator(run, example)
        scores.append(row["score"])
    rate = sum(scores) / len(scores) if scores else 0.0
    return {"key": "pass_rate", "score": rate}


def sync_dataset(
    cases: list[dict],
    *,
    dataset_name: str = DEFAULT_DATASET,
    client=None,
) -> str:
    """Upload/update LangSmith dataset from golden_set.json (reference labels only)."""
    from langsmith import Client

    ls = client or Client()
    if ls.has_dataset(dataset_name=dataset_name):
        dataset = ls.read_dataset(dataset_name=dataset_name)
    else:
        dataset = ls.create_dataset(
            dataset_name=dataset_name,
            description="LLM log triage golden set (synced from data/golden_set.json)",
        )

    existing = {
        (ex.metadata or {}).get("case_id"): ex
        for ex in ls.list_examples(dataset_id=dataset.id)
    }

    for case in cases:
        case_id = case["id"]
        inputs = {
            "log_text": case["log_text"],
            "service_name": case.get("service_name"),
            "case_id": case_id,
        }
        outputs = {"expected": case["expected"]}
        metadata = {
            "case_id": case_id,
            "adversarial": case["expected"].get("adversarial", False),
        }
        if case_id in existing:
            ls.update_example(
                existing[case_id].id,
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
            )
        else:
            ls.create_example(
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
                dataset_id=dataset.id,
            )

    return dataset_name


def predict(inputs: dict) -> dict:
    """Target for langsmith.evaluate() — runs frozen chain locally, returns JSON."""
    from llm_log_triage.chain import invoke
    from llm_log_triage.instrumentation.base import configure_observability

    configure_observability()
    result = invoke(
        inputs["log_text"],
        inputs.get("service_name"),
        use_cache=False,
        interface=EVAL_INTERFACE,
        case_id=inputs.get("case_id"),
    )
    return result.output.model_dump(mode="json")


def run_evaluation(
    *,
    dataset_name: str = DEFAULT_DATASET,
    max_cases: int | None = 5,
    experiment_prefix: str = "log-triage-v3",
    client=None,
) -> dict:
    """Run LangSmith experiment; returns summary dict + experiment name."""
    from langsmith import Client
    from langsmith.evaluation import evaluate

    ls = client or Client()

    if max_cases is not None:
        dataset = ls.read_dataset(dataset_name=dataset_name)
        examples = list(ls.list_examples(dataset_id=dataset.id, limit=max_cases))
        data: Any = examples
    else:
        data = dataset_name

    os.environ.setdefault("OBS_BACKEND", "langsmith")
    from llm_log_triage.instrumentation.langsmith import configure_langsmith

    configure_langsmith()

    results = evaluate(
        predict,
        data=data,
        evaluators=[golden_pass_evaluator, severity_match_evaluator, category_match_evaluator],
        summary_evaluators=[pass_rate_summary_evaluator],
        experiment_prefix=experiment_prefix,
        description="LLM log triage golden-set eval via langsmith.evaluate (same scorers as pytest)",
        metadata={
            "app": "llm-log-triage",
            "prompt_version": os.getenv("LOG_TRIAGE_DEFAULT_PROMPT_VERSION", "v3"),
            "model": os.getenv("LOG_TRIAGE_DEFAULT_MODEL", "gpt-4o-mini"),
            "interface": EVAL_INTERFACE,
        },
        max_concurrency=2,
    )

    experiment_name = results.experiment_name
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment_name": experiment_name,
        "dataset": dataset_name,
        "max_cases": max_cases,
        "experiment_prefix": experiment_prefix,
        "project": os.getenv("LANGCHAIN_PROJECT", "llm-log-triage"),
        "ui_hint": "LangSmith → Evaluations → find experiment by name",
    }

    return summary


def write_eval_report(summary: dict, report_dir: Path | None = None) -> Path:
    """Write experiment metadata to langsmith-eval-latest.json (+ timestamped copy)."""
    directory = report_dir or DEFAULT_REPORT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    latest = directory / "langsmith-eval-latest.json"
    stamped = directory / f"langsmith-eval-{stamp}.json"
    payload = json.dumps(summary, indent=2)
    latest.write_text(payload)
    stamped.write_text(payload)
    return latest


def main(argv: list[str] | None = None) -> int:
    """CLI entry: --sync-dataset uploads golden set; --run executes evaluate()."""
    parser = argparse.ArgumentParser(description="LLM log triage LangSmith dataset + eval experiment")
    parser.add_argument("--sync-dataset", action="store_true", help="Upload golden set to LangSmith")
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Skip golden_set.json upload on --run (for UI-curated datasets only)",
    )
    parser.add_argument("--run", action="store_true", help="Run evaluate() experiment")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="LangSmith dataset name")
    parser.add_argument(
        "--max-cases",
        default=os.getenv("LOG_TRIAGE_LANGSMITH_EVAL_MAX_CASES", "5"),
        help="Limit eval examples (default 5); use 'all' for full set",
    )
    parser.add_argument("--experiment-prefix", default="log-triage-v3")
    args = parser.parse_args(argv)

    if not os.getenv("LANGCHAIN_API_KEY"):
        raise SystemExit("LANGCHAIN_API_KEY required (set in .env)")

    if args.sync_dataset and args.no_sync:
        raise SystemExit("Use either --sync-dataset or --no-sync, not both")

    limit = None if str(args.max_cases).lower() == "all" else int(args.max_cases)
    cases = load_golden_cases()

    if args.sync_dataset:
        name = sync_dataset(cases, dataset_name=args.dataset)
        print(f"Dataset synced: {name} ({len(cases)} examples)")

    if args.run:
        if not args.sync_dataset and not args.no_sync:
            sync_dataset(cases, dataset_name=args.dataset)
            print(f"Dataset auto-synced: {args.dataset} ({len(cases)} examples)")
        elif args.no_sync:
            print(f"Skipping sync — evaluating LangSmith dataset as-is: {args.dataset}")
        summary = run_evaluation(
            dataset_name=args.dataset,
            max_cases=limit,
            experiment_prefix=args.experiment_prefix,
        )
        path = write_eval_report(summary)
        print(f"Experiment: {summary['experiment_name']}")
        print(f"Report: {path}")
        print(f"Open LangSmith → Project {summary['project']} → Evaluations")

    if not args.sync_dataset and not args.run:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
