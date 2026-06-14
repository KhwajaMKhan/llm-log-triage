# GitHub Actions — llm-log-triage CI

Two workflows run on every **push** and **pull_request** to `main`:

| Workflow | Job name | API keys | Purpose |
|----------|----------|----------|---------|
| [`ci.yml`](ci.yml) | `test (free)` | None | Deterministic tests (`pytest -m "not llm"`) |
| [`eval-gate.yml`](eval-gate.yml) | `eval (golden-set)` | Matching key for CI model | Golden-set eval — same **4 models** as app |

## One-time setup

1. **Repository secrets** (Settings → Secrets → Actions):
   - `OPENAI_API_KEY` — required for OpenAI models
   - `ANTHROPIC_API_KEY` — required for Claude models
2. **Repository variable** (Settings → Variables):
   - `LOG_TRIAGE_CI_MODEL` — one of: `gpt-4o-mini` (default), `gpt-4o`, `claude-sonnet-4-6`, `claude-opus-4-7`
3. **Branch protection:** require `test (free)` + `eval (golden-set)`

CI uses the **same model list** as Streamlit / `.env`. Pick your model once in repo variables; workflows call `python -m llm_log_triage.providers --check-secrets` to verify the matching key is set.

## Cost note

`eval (golden-set)` runs ~26 live LLM calls per workflow run (no disk cache on fresh runners).

---

## Manual workflows (adhoc — not PR gates)

| Workflow | Purpose | Secrets |
|----------|---------|---------|
| [`manual-langsmith-eval.yml`](manual-langsmith-eval.yml) | LangSmith experiment — model **dropdown** (4 models) | Matching key + `LANGCHAIN_API_KEY` |
| [`manual-judge-eval.yml`](manual-judge-eval.yml) | `pytest -m judge` | Uses `LOG_TRIAGE_CI_MODEL` + matching key |

Local equivalents: [`scripts/README.md`](../../scripts/README.md).
