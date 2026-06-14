# Golden set — `golden_set.json`

**Purpose:** Fixed labeled examples for regression evals and fair tool comparison.  
**Used by:** `pytest -m llm` (CI merge gate), notebook EDD cells, `langsmith_eval --sync-dataset`.

**CI model:** same 4 supported models as the app — GitHub variable `LOG_TRIAGE_CI_MODEL` (see [architecture.md](../docs/architecture.md#6-model-selection-app--ci)).

## Schema (each case)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable id e.g. `gs-001`, `adv-002` |
| `service_name` | string \| null | Optional hint passed to `chain.invoke()` |
| `log_text` | string | Raw log input to the triage LLM |
| `expected.severity` | enum | `SEV1` … `SEV4` or `unknown` |
| `expected.category` | enum | `connectivity`, `resource`, … or `unknown` |
| `expected.must_mention` | string[] | Phrases that must appear in triage text |
| `expected.adversarial` | bool | If true, require `unknown` + low confidence |
| `expected.max_confidence` | float | Adversarial only (default 0.4) |

## Counts

- **22 normal** cases (`gs-*`) — severity/category/must_mention must match
- **4 adversarial** cases (`adv-*`) — empty, garbage, truncated, spam logs

## Scoring

Logic lives in `src/llm_log_triage/eval_checks.py` (`score_case`). Same function for pytest, notebook, and LangSmith evaluators — **offline parity**.

## Do not

- Change labels when comparing observability tools (fairness invariant)
- Add cases without re-running `pytest tests/ -m llm -v`
