# Roadmap (future)

Planned enhancements beyond the v1.0 public release. For what ships today, see [architecture.md](architecture.md) and [README](../README.md).

## Integrations

| Item | Interface | Notes |
|------|-----------|-------|
| **Email team about triage** | CLI, Streamlit | Send structured triage JSON to on-call or service owners |
| **Human-in-the-loop (HITL)** | CLI, Streamlit | Approve/reject/edit before acting on triage output |
| **Human annotation** | CLI, Streamlit | Label/correct results → `golden_set.json` or LangSmith |

## Eval / quality (future)

| Item | Notes |
|------|-------|
| **Dual-provider CI matrix** | Parallel eval jobs (OpenAI + Anthropic) with per-provider pass thresholds |
| **Cross-model judge baselines** | Triage + judge on different providers — experiment only today |
| Human annotation workflow tests | pytest + LangSmith annotation queue |
| Add model to registry | Update `providers.MODEL_REGISTRY` + Streamlit / workflow dropdowns |

### Golden-set baselines (prompt v3)

| Model | Normal pass rate | Adversarial | CI |
|-------|------------------|-------------|-----|
| `gpt-4o-mini` | ≥90% | 4/4 | Default — set `LOG_TRIAGE_CI_MODEL` or leave unset |
| `claude-sonnet-4-6` | 21/22 (95.5%) | 4/4 | Set `LOG_TRIAGE_CI_MODEL` + `ANTHROPIC_API_KEY` |

## Shipped in v1.0.0

- **4 predefined models** — `providers.MODEL_REGISTRY`; pick in Streamlit or `.env`
- **CI** — same 4 models via `LOG_TRIAGE_CI_MODEL` (default `gpt-4o-mini`)
- **EDD** — L0 schema, L1 code reviewer (merge gate), L2 LLM judge (manual)
- **Observability** — LangSmith default; OTel optional via `OBS_BACKEND`
- Pre-labeled `golden_set.json` (26 cases)

See [architecture.md](architecture.md) for diagrams and module map.
