"""Streamlit UI for LLM log triage."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st
from dotenv import load_dotenv

from llm_log_triage.chain import SUPPORTED_MODELS, invoke  # noqa: E402

load_dotenv(ROOT / ".env")

st.set_page_config(page_title="LLM Log Triage", layout="wide")
st.title("LLM Log Triage Summarizer")

with st.sidebar:
    st.header("Config")
    model = st.selectbox("Model", list(SUPPORTED_MODELS))
    prompt_version = st.selectbox("Prompt version", ["v1", "v2", "v3"])
    service_name = st.text_input("Service name (optional)")
    use_cache = st.checkbox("Use response cache", value=True)
    obs_backend = st.selectbox("Obs backend (set OBS_BACKEND env)", ["none", "langsmith", "otel"])

def _clear_log() -> None:
    st.session_state.log_text = ""
    st.session_state.pop("last_result", None)


if "log_text" not in st.session_state:
    st.session_state.log_text = ""

log_text = st.text_area("Paste log text", height=200, key="log_text")

btn_row, _ = st.columns([1, 5])
with btn_row:
    col_triage, col_clear = st.columns(2, gap="small")
    with col_triage:
        triage_clicked = st.button("Triage", type="primary", use_container_width=True)
    with col_clear:
        st.button("Clear", use_container_width=True, on_click=_clear_log)

if triage_clicked:
    if not log_text.strip():
        st.warning("Paste a log line above, then click Triage.")
    else:
        import os

        os.environ["OBS_BACKEND"] = obs_backend
        with st.spinner("Analyzing..."):
            result = invoke(
                log_text,
                service_name or None,
                model=model,
                prompt_version=prompt_version,
                use_cache=use_cache,
                interface="streamlit",
            )
        st.session_state.last_result = {
            "output": result.output.model_dump(),
            "log_snippet": log_text[:200],
            "latency_ms": result.latency_ms,
            "model": result.model,
            "prompt_version": result.prompt_version,
            "cached": result.cached,
        }

last = st.session_state.get("last_result")
if last:
    st.subheader("Result")
    st.json(last["output"])
    st.caption(
        f"Latency: {last['latency_ms']:.0f} ms | Model: {last['model']} | "
        f"Prompt: {last['prompt_version']} | Cached: {last['cached']}"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Good"):
            st.session_state.setdefault("feedback", []).append(
                {"log": last["log_snippet"], "rating": "up", "output": last["output"]}
            )
            st.success("Thanks!")
    with col2:
        if st.button("👎 Bad"):
            st.session_state.setdefault("feedback", []).append(
                {"log": last["log_snippet"], "rating": "down", "output": last["output"]}
            )
            st.warning("Noted — add to golden set via notebook")

if st.session_state.get("feedback"):
    with st.expander("Session feedback"):
        st.json(st.session_state["feedback"])
