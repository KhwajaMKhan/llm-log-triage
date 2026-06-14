# Architecture

System design for **LLM Log Triage** (`src/llm_log_triage/`). Quick start: [README.md](../README.md).

---

## 1. Context (C4 — Level 1)

Helps on-call engineers turn raw log text into structured triage JSON (severity, category, cause, action).

**Users:** SRE / platform engineer via CLI, Streamlit, or Jupyter notebook.

**External systems:** OpenAI or Anthropic (inference), optional LangSmith / OpenTelemetry (observability only).

---

## 2. Containers (C4 — Level 2)

```mermaid
flowchart TB
  subgraph interfaces [Interfaces — thin wrappers]
    CLI[llm_log_triage.cli]
    UI[ui/streamlit_app.py]
    NB[notebooks/explore.ipynb]
    PY[pytest / langsmith_eval]
  end

  subgraph core [Frozen core]
    INV[chain.invoke]
    PR[prompts.py v1-v3]
    SCH[schema.py]
    CACHE[cache.py]
  end

  subgraph eval [Eval — shared scorer]
    EC[eval_checks.score_case]
    JUD[judge.py optional 2nd LLM]
  end

  subgraph obs [Observability — optional]
    INS[instrumentation/]
  end

  subgraph data [Data]
    GS[(golden_set.json)]
    ER[(docs/eval-runs/*.json)]
  end

  CLI --> INV
  UI --> INV
  NB --> INV
  PY --> INV
  INV --> PR
  INV --> SCH
  INV --> CACHE
  INV --> INS
  PY --> EC
  PY --> JUD
  EC --> GS
  INS -.-> LangSmith[(LangSmith cloud)]
  INV --> OpenAI[(OpenAI / Anthropic API)]
```

**Observability swap:** only `instrumentation/` + `OBS_BACKEND` change; chain, prompts, and golden set stay fixed.

---

## 3. Request flow (single triage call)

```mermaid
sequenceDiagram
  participant User
  participant IF as Interface
  participant CH as chain.invoke
  participant CA as cache
  participant PR as prompts
  participant LLM as OpenAI/Anthropic
  participant OBS as LangSmith trace

  User->>IF: log_text, service_name
  IF->>CH: invoke(..., interface=cli|notebook|...)
  CH->>CA: get_cached?
  alt cache hit
    CA-->>CH: TriageOutput
  else cache miss
    CH->>PR: get_prompt(v3)
    CH->>LLM: structured output
    LLM-->>CH: TriageOutput
    CH->>CA: set_cached
  end
  CH-->>OBS: spans if OBS_BACKEND=langsmith
  CH-->>IF: InvokeResult
  IF-->>User: JSON
```

---

## 4. Eval architecture (three levels)

```mermaid
flowchart LR
  subgraph L0 [L0 Schema]
    P1[pytest test_schema]
  end

  subgraph L1 [L1 Code reviewer]
    EC[eval_checks]
    T1[pytest -m llm]
    T2[langsmith_eval]
    T3[notebook_runner]
  end

  subgraph L2 [L2 LLM judge]
    J[judge_triage]
    T4[pytest -m judge]
  end

  GS[(golden_set.json)] --> EC
  EC --> T1
  EC --> T2
  EC --> T3
  J --> T4
  T1 --> CI[eval-gate.yml PR]
  T2 --> LS[LangSmith experiments manual]
  T4 --> MAN[judge manual]
```

| Level | Reviewer | CI merge gate? | Manual scripts |
|-------|----------|----------------|----------------|
| L0 | Pydantic | `test (free)` | — |
| L1 | `eval_checks` | **`eval (golden-set)`** | `scripts/run_langsmith_eval_golden.sh` |
| L2 | `judge.py` | No | `scripts/run_judge_eval.sh` |

---

## 5. Module map (`src/llm_log_triage/`)

| Module | Responsibility |
|--------|----------------|
| `chain.py` | **Single entry:** `invoke()` — LCEL prompt \| LLM → `TriageOutput` |
| `providers.py` | **Provider routing:** `MODEL_REGISTRY`, `LOG_TRIAGE_PROVIDER`, CI `--check-secrets` |
| `prompts.py` | Prompt templates v1→v3 (`get_prompt`) |
| `schema.py` | `TriageInput`, `TriageOutput`, enums |
| `eval_checks.py` | **Single scorer** for golden set (parity) |
| `judge.py` | Second LLM — coherence/actionability (charter #4) |
| `cache.py` | Disk cache keyed by log+model+prompt |
| `cli.py` | CLI wrapper |
| `notebook_runner.py` | Notebook live runs + report rows |
| `notebook_report.py` | JSON session reports → repo-root `docs/eval-runs/` |
| `notebook_setup.py` | `.env`, kernel check, `find_repo_root()` |
| `langsmith_eval.py` | Sync dataset + `langsmith.evaluate()` |
| `judge_report.py` | Judge JSON artifacts |
| `instrumentation/` | `OBS_BACKEND` switch (langsmith, otel, …) |

---

## 6. Prompt management

Prompts are **versioned Python strings** in `prompts.py`:

| Version | Change |
|---------|--------|
| v1 | Baseline + category rubric |
| v2 | + severity rubric |
| v3 | + log-level rules, adversarial rules, few-shot |

**Selection:** `LOG_TRIAGE_DEFAULT_PROMPT_VERSION` env var or `--prompt-version` on CLI.

**Tracing:** tags `prompt:v3` on every LangSmith run.

Prompts live in **git** (`prompts.py`) — readable, diffable, version-controlled. Optional: mirror copies in LangSmith Prompts hub; git remains source of truth.

---

## 7. If you want to change X, edit Y

| Goal(X)| Where(Y) |
|------|--------|
| Triage behavior / model | `chain.py`, `.env` `LOG_TRIAGE_DEFAULT_MODEL` |
| Prompt text | `prompts.py` (new version → re-run golden eval) |
| Pass/fail rules | `eval_checks.py` + `data/golden_set.json` labels |
| Judge bar | `judge.py` `PASS_THRESHOLD` |
| Observability tool | `src/llm_log_triage/instrumentation/`, `OBS_BACKEND` |
| LangSmith experiment | `langsmith_eval.py`, `scripts/run_langsmith_eval_*.sh` |
| CI merge gate | `.github/workflows/eval-gate.yml` |
| Manual eval / judge | `scripts/run_*.sh`, `.github/workflows/manual-*.yml` |

---

## 8. Data & artifacts

```
data/golden_set.json          ← source of truth (26 cases)
docs/eval-runs/
  notebook-latest.json        ← notebook session
  judge-latest.json           ← judge runs
  langsmith-eval-latest.json  ← last experiment metadata
```

LangSmith dataset `log-triage-golden-set-v3` is a **synced copy** for experiments, not the git source of truth.

---

## 9. Related docs

| Doc | Purpose |
|-----|---------|
| [`../README.md`](../README.md) | Clone, setup, run, test |
| [`../data/golden_set.README.md`](../data/golden_set.README.md) | Golden-set case schema |
| [`eval-runs/README.md`](eval-runs/README.md) | Sample eval report artifacts |
| [`../scripts/README.md`](../scripts/README.md) | Manual LangSmith / judge scripts |
| [`../.github/workflows/README.md`](../.github/workflows/README.md) | CI workflows |
