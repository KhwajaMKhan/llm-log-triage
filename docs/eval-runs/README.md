# Eval run artifacts (samples)

Optional structured JSON from eval runs. **Regenerate locally** after you run evals — the committed files are **examples only**, not required to use the app.

| File | Producer |
|------|----------|
| `langsmith-eval-latest.json` | `./scripts/run_langsmith_eval_golden.sh` or `python -m llm_log_triage.langsmith_eval --run` |
| `judge-latest.json` | `pytest -m judge` or `./scripts/run_judge_eval.sh` |
| `judge-fail-smoke-latest.json` | `pytest tests/test_judge.py::test_judge_rejects_deliberately_bad_triage -m judge -v -s` |
| `notebook-latest.json` | notebook `RUN_*` cells (created on first live run) |

Each producer also writes timestamped copies (e.g. `langsmith-eval-2026-06-07T120000Z.json`). Those are typically **not** committed.
