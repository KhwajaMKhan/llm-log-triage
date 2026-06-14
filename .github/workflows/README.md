# GitHub Actions — llm-log-triage CI

Two workflows run on every **push** and **pull_request** to `main`:

| Workflow | Job name | API keys | Purpose |
|----------|----------|----------|---------|
| [`ci.yml`](ci.yml) | `test (free)` | None | Deterministic tests (`pytest -m "not llm"`) |
| [`eval-gate.yml`](eval-gate.yml) | `eval (golden-set)` | `OPENAI_API_KEY` | Merge-blocking golden-set eval (`pytest -m llm`, prompt v3, ≥90%) |

## One-time setup

1. **Repository secret:** Settings → Secrets and variables → Actions → `OPENAI_API_KEY`
2. **Branch protection:** Settings → Branches → `main` → Require status checks:
   - `test (free)`
   - `eval (golden-set)`

PRs cannot merge unless both pass.

## Cost note

`eval (golden-set)` runs ~26 live LLM calls per workflow run (no disk cache on fresh runners).

---

## Manual workflows (adhoc — not PR gates)

Trigger from **Actions** tab → select workflow → **Run workflow**.

| Workflow | Purpose | Secrets |
|----------|---------|---------|
| [`manual-langsmith-eval.yml`](manual-langsmith-eval.yml) | LangSmith experiment (prompt/model inputs) | `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` |
| [`manual-judge-eval.yml`](manual-judge-eval.yml) | `pytest -m judge` + artifact upload | `OPENAI_API_KEY` |

Local equivalents: [`scripts/README.md`](../../scripts/README.md).
