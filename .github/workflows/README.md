# GitHub Actions — llm-log-triage CI

Two workflows run on every **push** and **pull_request** to `main`:

| Workflow | Job name | API keys | Purpose |
|----------|----------|----------|---------|
| [`ci.yml`](ci.yml) | `test (free)` | None | Deterministic tests (`pytest -m "not llm"`) |
| [`eval-gate.yml`](eval-gate.yml) | `eval (golden-set)` | `OPENAI_API_KEY` | Golden-set eval — **fixed** `gpt-4o-mini`, prompt v3, ≥90% |

## One-time setup

1. **Repository secret:** Settings → Secrets → Actions → `OPENAI_API_KEY`
2. **Branch protection:** Settings → Branches → `main` → Require status checks:
   - `test (free)`
   - `eval (golden-set)`

**Note:** CI uses OpenAI + `gpt-4o-mini` only (EDD baseline). Anthropic models work **locally** via Streamlit / `.env` — see README.

## Cost note

`eval (golden-set)` runs ~26 live LLM calls per workflow run (no disk cache on fresh runners).

---

## Manual workflows (adhoc — not PR gates)

Trigger from **Actions** tab → select workflow → **Run workflow**.

| Workflow | Purpose | Secrets |
|----------|---------|---------|
| [`manual-langsmith-eval.yml`](manual-langsmith-eval.yml) | LangSmith experiment — **model dropdown** (4 supported models) | Matching key + `LANGCHAIN_API_KEY` |
| [`manual-judge-eval.yml`](manual-judge-eval.yml) | `pytest -m judge` | `OPENAI_API_KEY` (+ `LANGCHAIN_API_KEY` if tracing) |

Local equivalents: [`scripts/README.md`](../../scripts/README.md).
