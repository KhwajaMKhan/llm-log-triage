# Roadmap (future)

Not in scope for the v1.0 public release. Items below are planned for later iterations.

## Integrations

| Item | Interface | Notes |
|------|-----------|-------|
| **Email team about triage** | CLI, Streamlit | Send structured triage JSON to on-call or service owners |
| **Human-in-the-loop (HITL)** | CLI, Streamlit | Approve/reject/edit before acting on triage output |
| **Human annotation** | CLI, Streamlit | Label/correct results → `golden_set.json` or LangSmith |

## Eval / quality (future)

| Item | Notes |
|------|-------|
| **Anthropic CI gate** | Optional second merge check (today: CI is OpenAI `gpt-4o-mini` only) |
| **Dual-provider CI matrix** | Parallel eval jobs with per-provider pass thresholds |
| **Cross-model judge baselines** | Triage + judge on different providers (experiment today, no baseline) |
| Human annotation workflow tests | pytest + LangSmith annotation queue |
| Add model to registry | New tested model → update `providers.MODEL_REGISTRY` + dropdowns |

### Golden-set baselines (prompt v3, local eval)

| Model | Normal pass rate | Adversarial | CI today? |
|-------|------------------|-------------|-----------|
| `gpt-4o-mini` | ≥90% | 4/4 | **Yes** (merge gate) |
| `claude-sonnet-4-6` | 21/22 (95.5%) | 4/4 | Local / LangSmith manual only |

## Current scope (shipped)

- **4 predefined models** — pick in Streamlit or `.env`; matching API key only
- **CI:** fixed `gpt-4o-mini` + `OPENAI_API_KEY` (EDD L1 gate)
- L0 schema, L1 code reviewer, L2 LLM judge (manual)
- Pre-labeled `golden_set.json` (26 cases)

See [architecture.md](architecture.md) for the eval model today.
