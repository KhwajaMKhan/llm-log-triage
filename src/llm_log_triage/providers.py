"""LLM provider routing — single source of truth for OpenAI vs Anthropic.

Resolution order:
  1. LOG_TRIAGE_PROVIDER env (openai | anthropic) — use for new/unknown model ids
  2. MODEL_REGISTRY — tested models shipped with the app
  3. Name-prefix heuristics (fallback for common id patterns)
  4. ValueError with actionable message

GitHub Actions call: python -m llm_log_triage.providers --check-secrets
"""

from __future__ import annotations

import os
import sys
from typing import Literal

Provider = Literal["openai", "anthropic"]

# Tested models — update when adding dropdown / Streamlit options
MODEL_REGISTRY: dict[str, Provider] = {
    "gpt-4o-mini": "openai",
    "gpt-4o": "openai",
    "claude-sonnet-4-6": "anthropic",
    "claude-opus-4-7": "anthropic",
}

SUPPORTED_MODELS: tuple[str, ...] = tuple(MODEL_REGISTRY.keys())

_VALID_PROVIDERS = frozenset({"openai", "anthropic"})


def provider_for_model(model: str, *, provider_override: str | None = None) -> Provider:
    """Return openai or anthropic for a model id."""
    if provider_override:
        p = provider_override.strip().lower()
        if p not in _VALID_PROVIDERS:
            raise ValueError(
                f"LOG_TRIAGE_PROVIDER must be 'openai' or 'anthropic', got {provider_override!r}"
            )
        return p  # type: ignore[return-value]

    if model in MODEL_REGISTRY:
        return MODEL_REGISTRY[model]

    lower = model.lower()
    if lower.startswith("claude") or lower.startswith("anthropic"):
        return "anthropic"
    if lower.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
        return "openai"

    raise ValueError(
        f"Cannot infer provider for model {model!r}. "
        "Add it to MODEL_REGISTRY in providers.py or set LOG_TRIAGE_PROVIDER=openai|anthropic"
    )


def resolve_provider(model: str) -> Provider:
    """Resolve provider using LOG_TRIAGE_PROVIDER env override when set."""
    return provider_for_model(model, provider_override=os.getenv("LOG_TRIAGE_PROVIDER"))


def api_key_env_for_provider(provider: Provider) -> str:
    return "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"


def check_required_api_key(model: str | None = None) -> Provider:
    """Exit 0 if the required API key env var is set; else exit 1 (CI-friendly)."""
    model = model or os.getenv("LOG_TRIAGE_DEFAULT_MODEL", "gpt-4o-mini")
    provider = resolve_provider(model)
    env_name = api_key_env_for_provider(provider)
    if not os.getenv(env_name):
        print(
            f"::error::{env_name} required for provider={provider} model={model}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Provider {provider} for model {model} ({env_name} present)")
    return provider


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="LLM provider helpers for CI and local runs")
    parser.add_argument(
        "--check-secrets",
        action="store_true",
        help="Verify API key for LOG_TRIAGE_DEFAULT_MODEL (and optional LOG_TRIAGE_PROVIDER)",
    )
    parser.add_argument("--model", help="Override model id (default: LOG_TRIAGE_DEFAULT_MODEL)")
    args = parser.parse_args()
    if args.check_secrets:
        check_required_api_key(args.model)
        return
    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
