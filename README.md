# LLM Log Triage

**Open source (MIT).** Clone, add your own LLM API keys, and run — no license fee, no vendor lock-in. You pay only your provider (OpenAI, Anthropic, etc.) for inference.

**LangChain LCEL app:** raw log text in → structured JSON out (severity, category, cause, action).

Built with **Evaluation-Driven Development (EDD)**: a frozen golden set, **code as reviewer** (deterministic checks in CI), and an optional **LLM as judge** (coherence + actionability). Golden-set evals, pytest CI gate, optional LangSmith tracing/experiments, and three interfaces (CLI, Streamlit, notebook).

**Architecture & diagrams:** system design, module map, and Mermaid flowcharts — see [docs/architecture.md](docs/architecture.md).

## Quick start

```bash
git clone https://github.com/KhwajaMKhan/llm-log-triage.git
cd llm-log-triage
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,obs]"
cp .env.example .env   # add OPENAI_API_KEY + LANGCHAIN_API_KEY (LangSmith default)
```

### Run

```bash
# CLI
python -m llm_log_triage.cli --log-file data/sample.log
echo "ERROR payments-db connection refused" | python -m llm_log_triage.cli

# Streamlit (use project venv — conda/base `streamlit` won't see llm_log_triage)
source .venv/bin/activate
streamlit run ui/streamlit_app.py
# or: ./scripts/run_streamlit.sh

# Notebook (run from repo root or notebooks/)
jupyter notebook notebooks/explore.ipynb
```

**Streamlit — try these logs** (paste into **Paste log text**, click **Triage**):

| Example | Log line |
| ------- | -------- |
| DB down (SEV2) | `2026-05-28T14:02:11Z ERROR payments-api Failed to connect to postgres://payments-db:5432 - connection refused` |
| OOM kill (SEV1) | `2026-05-28T14:05:33Z FATAL auth-service OOMKilled container exceeded memory limit 512Mi` |
| Slow upstream (SEV3) | `2026-05-28T14:08:02Z WARN api-gateway upstream latency p99=3200ms target=500ms service=inventory-svc` |
| Expired JWT (SEV3) | `2026-05-28T14:10:44Z ERROR checkout-web JWT validation failed: token expired for user_id=8821` |

### Example JSON responses

**Triage output** (what `chain.invoke()` returns — one live example for the DB-down log):

```json
{
  "severity": "SEV2",
  "category": "connectivity",
  "likely_cause": "Database is unreachable due to connection refusal.",
  "suggested_action": "Check if the database service is running and accessible from the payments-api.",
  "confidence": 0.9,
  "evidence_lines": [
    "Failed to connect to postgres://payments-db:5432 - connection refused"
  ]
}
```

**LLM judge output** (optional second pass — scores triage quality; sample from `docs/eval-runs/judge-fail-smoke-latest.json` when triage contradicts the log):

```json
{
  "case_id": "judge-fail-smoke",
  "passed": false,
  "triage": {
    "severity": "SEV4",
    "category": "unknown",
    "likely_cause": "No issue detected; log looks healthy.",
    "suggested_action": "No action required.",
    "confidence": 0.1
  },
  "judge": {
    "coherence": 1,
    "actionability": 1,
    "rationale": "The assessment contradicts the log evidence, which clearly indicates a connection failure to the database."
  }
}
```

### Test

```bash
pytest tests/ -m "not llm" -v    # no API keys — start here
pytest tests/ -m llm -v          # golden set gate (prompt v3, ≥90%)
pytest tests/ -m smoke -v        # one live call
```

More detail: `[docs/architecture.md](docs/architecture.md)` · `[data/golden_set.README.md](data/golden_set.README.md)`

## Evaluation-Driven Development (EDD)

This repo is a teaching/reference implementation of EDD for LLM apps — not just “call an API and hope.”

| Layer | Reviewer | What it checks | Merge gate? |
| ----- | -------- | -------------- | ----------- |
| **L0** | Pydantic schema | Valid JSON shape | Yes (`test (free)` CI) |
| **L1** | **Code reviewer** (`eval_checks.py`) | Severity, category, keywords vs `data/golden_set.json` | Yes (`eval (golden-set)` CI) |
| **L2** | **LLM judge** (`judge.py`) | Coherence + actionability ≥ 4/5 | Manual / notebook only |

Same scorer (`eval_checks.score_case`) runs in pytest, the notebook, and LangSmith experiments — **offline parity**. Prompt or model changes must pass the golden set before merge.

Flowcharts (containers, request sequence, eval levels): [docs/architecture.md](docs/architecture.md).

## What's in the box


| Piece                                  | Role                                       |
| -------------------------------------- | ------------------------------------------ |
| `src/llm_log_triage/chain.py`          | LCEL triage pipeline (`invoke`)            |
| `data/golden_set.json`                 | 26 labeled eval cases                      |
| `src/llm_log_triage/eval_checks.py`    | Deterministic scorer (pytest + LangSmith)  |
| `src/llm_log_triage/langsmith_eval.py` | Dataset sync + offline experiments         |
| `src/llm_log_triage/instrumentation/`  | Swap observability backend (`OBS_BACKEND`) |
| `ui/streamlit_app.py`                  | Streamlit demo UI                          |


## Observability (LangSmith)

Default `.env.example` uses `OBS_BACKEND=langsmith`. Add `LANGCHAIN_API_KEY`, then:

```bash
./scripts/run_langsmith_eval_golden.sh
```

Traces go to LangSmith project `llm-log-triage`. Offline experiments use the same `eval_checks` scorer as pytest.

Optional helper: `./scripts/run_streamlit.sh` (same as `streamlit run ui/streamlit_app.py`).

## Interface tags (`interface=`)

Every triage call goes through `chain.invoke(..., interface=...)`. The value labels **where the call came from** — useful in LangSmith traces (`interface:cli`, etc.) and eval reports. There is no `github` interface; CI runs pytest directly.

| Entry point | `interface` value | Set in |
| ----------- | ----------------- | ------ |
| CLI | `cli` | `cli.py` |
| Streamlit | `streamlit` | `ui/streamlit_app.py` |
| Jupyter notebook | `notebook` | `notebook_runner.py` |
| **GitHub Actions CI** | **`pytest`** | `tests/test_golden_set.py`, `tests/test_judge.py` |
| Local pytest | `pytest` | same test files |
| LangSmith eval script | `langsmith_eval` | `langsmith_eval.py` |
| (default if omitted) | `unknown` | `chain.py` |

**CI workflows:** `ci.yml` runs `pytest -m "not llm"` (no live LLM, no interface tag). `eval-gate.yml` runs `pytest -m llm` with **`interface="pytest"`** on each golden-set case. CI sets `OBS_BACKEND=none`, so tags are not sent to LangSmith unless you change that.

## GitHub Actions workflows

Four workflows live under [`.github/workflows/`](.github/workflows/). See also [`.github/workflows/README.md`](.github/workflows/README.md).

### Automatic (every push & pull request to `main`)

| Workflow file | Job name | Trigger | API keys | What it does |
|---------------|----------|---------|----------|--------------|
| [`ci.yml`](.github/workflows/ci.yml) | `test (free)` | **Automatic** — `push` / `pull_request` → `main` | None | Deterministic tests only: `pytest -m "not llm"`. Schema, eval logic, instrumentation mocks — no live LLM calls. |
| [`eval-gate.yml`](.github/workflows/eval-gate.yml) | `eval (golden-set)` | **Automatic** — `push` / `pull_request` → `main` | `OPENAI_API_KEY` (repo secret) | Golden-set regression gate: `pytest tests/test_golden_set.py -m llm`, prompt v3, ≥90% pass. ~26 live LLM calls per run. Sets `OBS_BACKEND=none` and `interface=pytest`. Intended merge gate when branch protection requires this check. |

### Manual only (`workflow_dispatch` — you click Run)

| Workflow file | Job name | Trigger | API keys | What it does |
|---------------|----------|---------|----------|--------------|
| [`manual-langsmith-eval.yml`](.github/workflows/manual-langsmith-eval.yml) | `manual langsmith eval` | **Manual** — Actions → *Manual LangSmith Eval* → Run workflow | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` | Ad-hoc LangSmith experiment over the golden set. Inputs: prompt version, model, max cases, experiment prefix, sync dataset. Uploads `docs/eval-runs/langsmith-eval-latest.json`. Not a PR gate. |
| [`manual-judge-eval.yml`](.github/workflows/manual-judge-eval.yml) | `manual judge eval` | **Manual** — Actions → *Manual Judge Eval* → Run workflow | `OPENAI_API_KEY` (`LANGCHAIN_API_KEY` if `obs_backend=langsmith`) | L2 **LLM-as-judge** eval: `pytest tests/test_judge.py -m judge`. Triage + judge per case; writes `docs/eval-runs/judge-latest.json`. Not a PR gate. |

**One-time setup:** Settings → Secrets and variables → Actions → add `OPENAI_API_KEY`. For LangSmith manual workflows, also add `LANGCHAIN_API_KEY`.

### Run manual judge eval

**On GitHub (Actions):**

1. Open [github.com/KhwajaMKhan/llm-log-triage/actions](https://github.com/KhwajaMKhan/llm-log-triage/actions).
2. Select **Manual Judge Eval** in the left sidebar.
3. Click **Run workflow** (branch: `main`).
4. Choose **obs_backend**: `none` (default, no tracing) or `langsmith` (requires `LANGCHAIN_API_KEY` secret).
5. Click **Run workflow** again to start.
6. When finished, open the run → **Artifacts** → download `judge-eval-report` (`judge-latest.json` and timestamped copies).

**Locally (same tests, faster iteration):**

```bash
cd llm-log-triage
source .venv/bin/activate
./scripts/run_judge_eval.sh
```

Optional:

```bash
# Limit cases (default 5; use "all" for full golden set)
LOG_TRIAGE_JUDGE_MAX_CASES=3 ./scripts/run_judge_eval.sh

# Fail-smoke only (prove judge rejects bad triage)
pytest tests/test_judge.py::test_judge_rejects_deliberately_bad_triage -m judge -v -s

# With LangSmith tracing
OBS_BACKEND=langsmith ./scripts/run_judge_eval.sh
```

Report path: `docs/eval-runs/judge-latest.json`. Fail-smoke sample: `docs/eval-runs/judge-fail-smoke-latest.json`.

## License

Released under the **[MIT License](LICENSE)** — use freely in personal, educational, **commercial**, and **production** projects. Please **keep the copyright notice** in copies and derivatives so attribution stays visible.

**No warranty.** Triage output and eval scores may be wrong or incomplete. Read **[DISCLAIMER.md](DISCLAIMER.md)** before relying on this software for incident severity, on-call, or safety-critical decisions.