# Jev benchmark — llm-log-triage vs direct LLM vs Jev

**What is llm-log-triage?** Paste a log line → structured JSON (severity, category, likely cause, suggested action, evidence). Small LangChain app with a golden set and CI merge gates — see [README § What is llm-log-triage?](../../README.md#what-is-llm-log-triage).

Optional bakeoff script (not part of CI). Compares three lanes on golden-set cases:

| Lane | What |
|------|------|
| **A** | `llm-log-triage` — structured JSON via CLI chain |
| **B** | Direct chat LLM — think out loud first (same model, no app) |
| **C** | Jev — TypeSafe Choice API for category + severity |

## Keys

- **A / B:** `OPENAI_API_KEY` in `.env`
- **C:** `TYPESAFE_API_KEY` in `.env`

Set `OBS_BACKEND=none` automatically for lane A (no LangSmith noise during timing).

## Run

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_jev_benchmark.sh              # full lab (3 cases × 3 runs × ABC)
python scripts/jev_benchmark/run_lab.py --lanes A --cases gs-001 --runs 1   # smoke
```

Results: `docs/jev-benchmark-runs/SUMMARY.md` + timestamped JSON (gitignored locally).

Blog write-up and figures are **not** in this repo — publish separately (e.g. Medium).
