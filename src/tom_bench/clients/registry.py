"""Builds the set of model clients to run against, based on which free-tier
API keys are present in the environment. Never logs key values -- only
which provider was found or skipped."""
from __future__ import annotations

from .base import MissingAPIKeyError, ModelClient


def get_configured_clients(*, verbose: bool = True) -> dict[str, ModelClient]:
    from .anthropic import AnthropicClient
    from .gemini import GeminiClient
    from .groq import GroqClient

    clients: dict[str, ModelClient] = {}
    for label, factory in (
        ("Gemini", GeminiClient),
        ("Groq", GroqClient),
        ("Anthropic", AnthropicClient),
    ):
        try:
            client = factory()
        except MissingAPIKeyError:
            if verbose:
                print(f"[clients] {label}: no API key configured, skipping")
            continue
        clients[client.name] = client
        if verbose:
            print(f"[clients] {label}: configured as {client.name}")
    return clients
