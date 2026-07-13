"""Anthropic Claude client, intended to run on the one-time free signup
credit (no card charge). Defaults to Haiku 4.5 -- the fastest/cheapest
current model -- to stretch that credit across as many trials as possible;
override ANTHROPIC_MODEL to use a different model. Size the batch to a
known-safe trial count before running (see scripts/run_batch.py --dry-run)
so the run never risks exceeding the credit.
"""
from __future__ import annotations

import os

import httpx

from .base import MissingAPIKeyError

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MIN_INTERVAL = 1.2
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


def build_payload(prompt: str, model: str) -> dict:
    return {
        "model": model,
        "max_tokens": 200,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}],
    }


def parse_response(body: dict) -> str:
    content = body.get("content") or []
    text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
    if not text:
        raise ValueError(f"Anthropic response had no text content: {body}")
    return text


class AnthropicClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("ANTHROPIC_API_KEY is not set")
        self._api_key = api_key
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.name = f"anthropic:{self.model}"
        self.min_interval_seconds = float(
            os.environ.get("ANTHROPIC_MIN_INTERVAL_SECONDS", DEFAULT_MIN_INTERVAL)
        )
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        resp = httpx.post(
            API_URL,
            headers=headers,
            json=build_payload(prompt, self.model),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return parse_response(resp.json())
