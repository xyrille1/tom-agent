"""Hugging Face Inference Providers client (free tier via a Hugging Face
account's included monthly credits, no card required for free-tier usage).

Uses the OpenAI-compatible chat-completions router
(https://huggingface.co/docs/inference-providers), which federates to
whichever backing provider serves a given model -- pricing/free-tier terms
are set per model/provider and shift over time, so confirm the current free
allowance at https://huggingface.co/settings/billing before a real run.
Override HUGGINGFACE_MODEL if the default isn't currently free for you.
"""
from __future__ import annotations

import os

import httpx

from .base import MissingAPIKeyError

DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_MIN_INTERVAL = 2.5
API_URL = "https://router.huggingface.co/v1/chat/completions"


def build_payload(prompt: str, model: str) -> dict:
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 200,
    }


def parse_response(body: dict) -> str:
    choices = body.get("choices") or []
    if not choices:
        raise ValueError(f"Hugging Face response had no choices: {body}")
    content = choices[0].get("message", {}).get("content")
    if not content:
        raise ValueError(f"Hugging Face response had no message content: {body}")
    return content


class HuggingFaceClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 60.0):
        api_key = api_key or os.environ.get("HUGGINGFACE_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("HUGGINGFACE_API_KEY is not set")
        self._api_key = api_key
        self.model = model or os.environ.get("HUGGINGFACE_MODEL", DEFAULT_MODEL)
        self.name = f"huggingface:{self.model}"
        self.min_interval_seconds = float(
            os.environ.get("HUGGINGFACE_MIN_INTERVAL_SECONDS", DEFAULT_MIN_INTERVAL)
        )
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        resp = httpx.post(
            API_URL,
            headers=headers,
            json=build_payload(prompt, self.model),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return parse_response(resp.json())
