"""LangSmith eval helpers — no API calls.

Tests evaluators and dataset sync logic offline (mocked LangSmith client).
Scorecard: Eval integration + offline parity dimensions.
"""

import json
from unittest.mock import MagicMock

import pytest

from llm_log_triage.langsmith_eval import (
    category_match_evaluator,
    golden_pass_evaluator,
    load_golden_cases,
    severity_match_evaluator,
    sync_dataset,
)


def test_load_golden_cases():
    cases = load_golden_cases(limit=3)
    assert len(cases) == 3
    assert "log_text" in cases[0]


def test_golden_pass_evaluator_pass():
    run = MagicMock()
    run.outputs = {
        "severity": "SEV2",
        "category": "connectivity",
        "likely_cause": "postgres connection refused",
        "suggested_action": "check postgres connectivity",
        "confidence": 0.9,
        "evidence_lines": ["connection refused"],
    }
    example = MagicMock()
    example.outputs = {
        "expected": {
            "severity": "SEV2",
            "category": "connectivity",
            "must_mention": ["postgres", "connection refused"],
            "adversarial": False,
        }
    }
    result = golden_pass_evaluator(run, example)
    assert result["key"] == "golden_pass"
    assert result["score"] == 1


def test_severity_match_evaluator_fail():
    run = MagicMock()
    run.outputs = {"severity": "SEV3", "category": "connectivity"}
    example = MagicMock()
    example.outputs = {"expected": {"severity": "SEV2", "category": "connectivity"}}
    assert severity_match_evaluator(run, example)["score"] == 0
    assert category_match_evaluator(run, example)["score"] == 1


def test_sync_dataset_calls_client(monkeypatch):
    created = []

    class FakeClient:
        def has_dataset(self, dataset_name):
            return False

        def create_dataset(self, **kwargs):
            ds = MagicMock()
            ds.id = "ds-1"
            return ds

        def list_examples(self, dataset_id):
            return []

        def create_example(self, **kwargs):
            created.append(kwargs)

    cases = load_golden_cases(limit=1)
    sync_dataset(cases, dataset_name="test-dataset", client=FakeClient())
    assert len(created) == 1
    assert created[0]["inputs"]["case_id"] == cases[0]["id"]


def test_main_no_sync_skips_sync_dataset(monkeypatch):
    from llm_log_triage import langsmith_eval as mod

    calls = []

    def fake_sync(*args, **kwargs):
        calls.append(kwargs.get("dataset_name"))

    def fake_run_evaluation(**kwargs):
        return {
            "experiment_name": "test-exp",
            "dataset": kwargs["dataset_name"],
            "max_cases": kwargs["max_cases"],
            "experiment_prefix": kwargs["experiment_prefix"],
            "project": "test-project",
            "timestamp": "now",
            "ui_hint": "",
        }

    def fake_write_report(summary, report_dir=None):
        return mod.DEFAULT_REPORT_DIR / "langsmith-eval-latest.json"

    monkeypatch.setenv("LANGCHAIN_API_KEY", "test-key")
    monkeypatch.setattr(mod, "sync_dataset", fake_sync)
    monkeypatch.setattr(mod, "run_evaluation", fake_run_evaluation)
    monkeypatch.setattr(mod, "write_eval_report", fake_write_report)

    rc = mod.main(
        [
            "--run",
            "--no-sync",
            "--dataset",
            "curated-dataset-2",
            "--max-cases",
            "all",
            "--experiment-prefix",
            "log-triage-v1-curated",
        ]
    )

    assert rc == 0
    assert calls == []


def test_main_sync_dataset_and_no_sync_exits(monkeypatch):
    from llm_log_triage import langsmith_eval as mod

    monkeypatch.setenv("LANGCHAIN_API_KEY", "test-key")
    with pytest.raises(SystemExit):
        mod.main(["--run", "--sync-dataset", "--no-sync"])
