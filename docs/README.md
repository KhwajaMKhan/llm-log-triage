# Documentation

Deep-dive docs for **LLM Log Triage**. Start at the root [README](../README.md) for clone, EDD overview, and quick start.

## Why `docs/` instead of the repo root?

| Location | What belongs there |
| -------- | ------------------ |
| **Root** | Entry point only — `README.md`, `LICENSE`, `DISCLAIMER.md`. First-time visitors land here on GitHub. |
| **`docs/`** | Reference material you open *after* setup — architecture diagrams, roadmap, eval artifact samples. |

Keeping architecture and roadmap here is standard OSS practice: the root README stays scannable; long Mermaid diagrams and module maps do not push quick start below the fold.

## Index

| Doc | When to read it |
| --- | --------------- |
| [architecture.md](architecture.md) | System design, C4 diagrams, L0/L1/L2 eval flow, module map, model selection |
| [ROADMAP.md](ROADMAP.md) | Future features and golden-set baselines (not shipped yet) |
| [eval-runs/README.md](eval-runs/README.md) | Sample JSON from judge / LangSmith / notebook runs |
| [../data/golden_set.README.md](../data/golden_set.README.md) | Golden-set case schema and scoring rules |
| [../scripts/README.md](../scripts/README.md) | Local helper scripts (Streamlit, LangSmith, judge) |
| [../.github/workflows/README.md](../.github/workflows/README.md) | CI merge gates and manual workflows |
