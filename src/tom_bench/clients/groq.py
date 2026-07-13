"""Groq client (free tier, OpenAI-compatible chat completions endpoint).

Free-tier RPM/TPM limits vary by model and shift over time -- confirm
current numbers at https://console.groq.com/docs/rate-limits before a real
run. The 2.5s default spacing is a conservative starting point; override
GROQ_MIN_INTERVAL_SECONDS if the live limit differs.
"""
from __future__ import annotations

import os

import httpx

from .base import MissingAPIKeyError

DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_MIN_INTERVAL = 2.5
API_URL = "https://api.groq.com/openai/v1/chat/completions"


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
        raise ValueError(f"Groq response had no choices: {body}")
    content = choices[0].get("message", {}).get("content")
    if not content:
        raise ValueError(f"Groq response had no message content: {body}")
    return content


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0):
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("GROQ_API_KEY is not set")
        self._api_key = api_key
        self.model = model or os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
        self.name = f"groq:{self.model}"
        self.min_interval_seconds = float(os.environ.get("GROQ_MIN_INTERVAL_SECONDS", DEFAULT_MIN_INTERVAL))
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
