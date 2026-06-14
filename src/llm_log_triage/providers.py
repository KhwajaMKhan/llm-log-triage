"""Predefined model → provider map. Keep routing simple: pick a supported model, set matching API key.

Supported models (Streamlit dropdown, LangSmith workflow, local .env):
  gpt-4o-mini, gpt-4o, claude-sonnet-4-6, claude-opus-4-7

CI merge gate (eval-gate.yml): LOG_TRIAGE_CI_MODEL repo variable (default gpt-4o-mini) + matching API key.
"""

from __future__ import annotations

import os
import sys
from typing import Literal

Provider = Literal["openai", "anthropic"]

# Only models we ship in UI / workflow dropdowns — add here when you test a new one
MODEL_REGISTRY: dict[str, Provider] = {
    "gpt-4o-mini": "openai",
    "gpt-4o": "openai",
    "claude-sonnet-4-6": "anthropic",
    "claude-opus-4-7": "anthropic",
}

SUPPORTED_MODELS: tuple[str, ...] = tuple(MODEL_REGISTRY.keys())

DEFAULT_MODEL = "gpt-4o-mini"


def provider_for_model(model: str) -> Provider:
    """Look up provider for a supported model id."""
    try:
        return MODEL_REGISTRY[model]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_MODELS)
        raise ValueError(
            f"Unsupported model {model!r}. Pick one of: {supported}"
        ) from exc


def api_key_env_for_provider(provider: Provider) -> str:
    return "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"


def check_required_api_key(model: str | None = None) -> Provider:
    """Exit 0 if the required API key is set; else exit 1 (used by CI / manual workflows)."""
    model = model or os.getenv("LOG_TRIAGE_DEFAULT_MODEL", DEFAULT_MODEL)
    provider = provider_for_model(model)
    env_name = api_key_env_for_provider(provider)
    if not os.getenv(env_name):
        print(
            f"::error::{env_name} required for model={model} (provider={provider})",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"OK model={model} provider={provider}")
    return provider


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Check API key for a supported model")
    parser.add_argument("--check-secrets", action="store_true")
    parser.add_argument("--model", help="Model id (default: LOG_TRIAGE_DEFAULT_MODEL)")
    args = parser.parse_args()
    if args.check_secrets:
        check_required_api_key(args.model)
        return
    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
