# GitHub Actions — llm-log-triage CI

Two workflows run on every **push** and **pull_request** to `main`:

| Workflow | Job name | API keys | Purpose |
|----------|----------|----------|---------|
| [`ci.yml`](ci.yml) | `test (free)` | None | Deterministic tests (`pytest -m "not llm"`) |
| [`eval-gate.yml`](eval-gate.yml) | `eval (golden-set)` | Key for CI model — see below | Merge-blocking golden-set eval (`pytest -m llm`, prompt v3, ≥90%) |

## One-time setup

1. **Repository secrets** (Settings → Secrets and variables → Actions):
   - OpenAI CI (default): `OPENAI_API_KEY`
   - Anthropic CI (optional): `ANTHROPIC_API_KEY`
2. **Repository variable** (Settings → Secrets and variables → Actions → **Variables** tab):
   - `LOG_TRIAGE_CI_MODEL` — default `gpt-4o-mini` if unset. Tested values: `gpt-4o-mini`, `gpt-4o`, `claude-sonnet-4-6`, `claude-opus-4-7`
   - `LOG_TRIAGE_CI_PROVIDER` (optional) — `openai` or `anthropic` when the model id is not yet in `providers.MODEL_REGISTRY`
3. **Branch protection:** Settings → Branches → `main` → Require status checks:
   - `test (free)`
   - `eval (golden-set)`

PRs cannot merge unless both pass.

**CI model rule:** workflows set `LOG_TRIAGE_DEFAULT_MODEL` from `LOG_TRIAGE_CI_MODEL` and run `python -m llm_log_triage.providers --check-secrets` (registry → heuristics → optional `LOG_TRIAGE_CI_PROVIDER`).

## Cost note

`eval (golden-set)` runs ~26 live LLM calls per workflow run (no disk cache on fresh runners).

---

## Manual workflows (adhoc — not PR gates)

Trigger from **Actions** tab → select workflow → **Run workflow**.

| Workflow | Purpose | Secrets |
|----------|---------|---------|
| [`manual-langsmith-eval.yml`](manual-langsmith-eval.yml) | LangSmith experiment (prompt + **model dropdown**) | Matching key for selected model + `LANGCHAIN_API_KEY` |
| [`manual-judge-eval.yml`](manual-judge-eval.yml) | `pytest -m judge` + artifact upload | Key for `LOG_TRIAGE_CI_MODEL` (or default `gpt-4o-mini`) |

Local equivalents: [`scripts/README.md`](../../scripts/README.md).
