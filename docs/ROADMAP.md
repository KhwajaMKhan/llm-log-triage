# Roadmap (future)

Not in scope for the initial public release. Items below are planned enhancements for later iterations.

## Integrations

| Item | Interface | Notes |
|------|-----------|-------|
| **Email team about triage** | CLI, Streamlit | Send structured triage JSON (severity, cause, action) to on-call or service owners |
| **Human-in-the-loop (HITL)** | CLI, Streamlit | Pause for human approve/reject/edit before acting on triage output |
| **Human annotation** | CLI, Streamlit | Label or correct triage results; feed back into `golden_set.json` or LangSmith dataset |

## Eval / quality

| Item | Notes |
|------|-------|
| Human annotation workflow tests | pytest + optional LangSmith annotation queue sync |
| Annotation export | JSON/CSV from Streamlit sessions for golden-set curation |

## Current scope (shipped)

- L0 schema, L1 code reviewer (`eval_checks`), L2 LLM judge (manual)
- Pre-labeled `data/golden_set.json` (26 cases) — expert labels in git, not live annotation UI

See [architecture.md](architecture.md) for the eval model today.
