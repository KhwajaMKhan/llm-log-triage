# Scripts

**What is llm-log-triage?** Paste a log line → structured JSON (severity, category, likely cause, suggested action, evidence). Small LangChain app with a golden set and CI merge gates — see [README § What is llm-log-triage?](../README.md#what-is-llm-log-triage).

Helper scripts for local runs. **CI merge gates** are GitHub Actions — see [`.github/workflows/README.md`](../.github/workflows/README.md).

## Run interfaces

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_streamlit.sh`](run_streamlit.sh) | Streamlit UI (`ui/streamlit_app.py`) | Matching key for selected model (see [README model table](../README.md#pick-a-model-4-supported)) |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_streamlit.sh
```

## Manual eval scripts

Ad-hoc runs — **not** merge gates.

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_langsmith_eval_golden.sh`](run_langsmith_eval_golden.sh) | Full golden-set LangSmith experiment | Matching key for `LOG_TRIAGE_DEFAULT_MODEL` + `LANGCHAIN_API_KEY` |
| [`run_langsmith_eval_anthropic_v3.sh`](run_langsmith_eval_anthropic_v3.sh) | v3 + Claude (`claude-sonnet-4-6`) | `ANTHROPIC_API_KEY`, `LANGCHAIN_API_KEY` |
| [`run_judge_eval.sh`](run_judge_eval.sh) | LLM-as-judge over golden set | Matching key for `LOG_TRIAGE_DEFAULT_MODEL` (judge uses same model by default) |

```bash
cd llm-log-triage && source .venv/bin/activate
./scripts/run_langsmith_eval_golden.sh
./scripts/run_judge_eval.sh
```

GitHub equivalents: **Actions → Manual LangSmith Eval** / **Manual Judge Eval** (see [README workflows](../README.md#github-actions-workflows)).

## Jev benchmark (optional)

Compare **llm-log-triage** vs direct chat LLM vs [TypeSafe Jev](https://typesafe.ai) on golden-set cases — **not** a merge gate.

| Script | Purpose | Keys |
|--------|---------|------|
| [`run_jev_benchmark.sh`](run_jev_benchmark.sh) | Full A+B+C bakeoff | `OPENAI_API_KEY`, `TYPESAFE_API_KEY` |

See [`jev_benchmark/README.md`](jev_benchmark/README.md).
