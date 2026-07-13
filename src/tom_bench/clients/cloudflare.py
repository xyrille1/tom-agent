"""Cloudflare Workers AI client (free tier: a daily allotment of "neurons"
included on every Cloudflare account, no card required).

Needs two env vars, not just the API token: CLOUDFLARE_ACCOUNT_ID (visible
on any page of the Cloudflare dashboard -- not secret, but required to build
the request URL) and CLOUDFLARE_API_TOKEN (must have the "Workers AI ->
Read/Edit" permission scope, or calls will 401/403). Free-tier neuron limits
shift over time -- confirm the current allowance at
https://developers.cloudflare.com/workers-ai/platform/pricing/ before a
real run. Override CLOUDFLARE_MODEL if the default isn't available on your
account.
"""
from __future__ import annotations

import os

import httpx

from .base import MissingAPIKeyError

DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct"
DEFAULT_MIN_INTERVAL = 2.5
API_BASE = "https://api.cloudflare.com/client/v4/accounts"


def build_payload(prompt: str) -> dict:
    return {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 200,
    }


def parse_response(body: dict) -> str:
    if not body.get("success", False):
        raise ValueError(f"Cloudflare Workers AI request failed: {body.get('errors')}")
    result = body.get("result") or {}
    text = result.get("response")
    if not text:
        raise ValueError(f"Cloudflare Workers AI response had no text content: {body}")
    if isinstance(text, dict):
        # Some Workers AI models auto-detect JSON-shaped output and return it
        # already parsed instead of as a raw string -- re-serialize so the
        # rest of the pipeline (which expects raw text it parses itself)
        # sees a consistent contract regardless of provider.
        import json

        text = json.dumps(text)
    return text


class CloudflareClient:
    def __init__(
        self,
        api_token: str | None = None,
        account_id: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN")
        account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        missing = [
            name
            for name, val in (("CLOUDFLARE_API_TOKEN", api_token), ("CLOUDFLARE_ACCOUNT_ID", account_id))
            if not val
        ]
        if missing:
            raise MissingAPIKeyError(f"{' and '.join(missing)} not set")
        self._api_token = api_token
        self._account_id = account_id
        self.model = model or os.environ.get("CLOUDFLARE_MODEL", DEFAULT_MODEL)
        self.name = f"cloudflare:{self.model}"
        self.min_interval_seconds = float(
            os.environ.get("CLOUDFLARE_MIN_INTERVAL_SECONDS", DEFAULT_MIN_INTERVAL)
        )
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        url = f"{API_BASE}/{self._account_id}/ai/run/{self.model}"
        headers = {"Authorization": f"Bearer {self._api_token}"}
        resp = httpx.post(url, headers=headers, json=build_payload(prompt), timeout=self._timeout)
        resp.raise_for_status()
        return parse_response(resp.json())
