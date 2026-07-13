"""Google Gemini client (free tier via Google AI Studio, no card required).

Free-tier RPM/RPD limits -- and even which model IDs carry a nonzero free
quota -- shift over time and vary per account; confirm current numbers at
https://ai.google.dev/gemini-api/docs/rate-limits before a real run. In
testing, versioned IDs like "gemini-2.0-flash-lite" returned a hard
`limit: 0` free-tier quota on this account while the unversioned alias
"gemini-flash-lite-latest" worked -- if you hit a 429 with `limit: 0` in the
error body (not "quota exceeded" from actual usage), that means this model
ID isn't free-tier-eligible on your account, not that you're rate-limited;
try a different GEMINI_MODEL override. The 4.5s default spacing assumes a
conservative ~13 requests/minute ceiling; override
GEMINI_MIN_INTERVAL_SECONDS if the live limit differs.
"""
from __future__ import annotations

import os

import httpx

from .base import MissingAPIKeyError

DEFAULT_MODEL = "gemini-flash-lite-latest"
DEFAULT_MIN_INTERVAL = 4.5
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def build_payload(prompt: str) -> dict:
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 200},
    }


def parse_response(body: dict) -> str:
    candidates = body.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini response had no candidates: {body}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    if not text:
        raise ValueError(f"Gemini response had no text content: {body}")
    return text


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise MissingAPIKeyError("GEMINI_API_KEY is not set")
        self._api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self.name = f"gemini:{self.model}"
        self.min_interval_seconds = float(os.environ.get("GEMINI_MIN_INTERVAL_SECONDS", DEFAULT_MIN_INTERVAL))
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        url = f"{API_BASE}/{self.model}:generateContent"
        resp = httpx.post(
            url,
            params={"key": self._api_key},
            json=build_payload(prompt),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return parse_response(resp.json())
