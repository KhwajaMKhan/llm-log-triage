"""CLI entry point: python -m llm_log_triage.cli

Thin wrapper — parses args, reads log text, calls chain.invoke(), prints JSON.
No business logic here; same pattern for Streamlit and notebook.
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

from llm_log_triage.chain import invoke


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="LLM Log Triage Summarizer")
    parser.add_argument("--log-file", type=str, help="Path to log file")
    parser.add_argument("--service-name", type=str, default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--prompt-version", type=str, default=None, choices=["v1", "v2", "v3"])
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)

    if args.log_file:
        log_text = open(args.log_file).read()
    elif not sys.stdin.isatty():
        log_text = sys.stdin.read()
    else:
        parser.error("Provide --log-file or pipe log text on stdin")

    kwargs: dict = {"use_cache": not args.no_cache, "interface": "cli"}
    if args.model:
        kwargs["model"] = args.model
    if args.prompt_version:
        kwargs["prompt_version"] = args.prompt_version

    result = invoke(log_text, args.service_name, **kwargs)
    payload = {
        **result.output.model_dump(),
        "_meta": {
            "latency_ms": round(result.latency_ms, 1),
            "model": result.model,
            "prompt_version": result.prompt_version,
            "cached": result.cached,
            "interface": "cli",
        },
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
