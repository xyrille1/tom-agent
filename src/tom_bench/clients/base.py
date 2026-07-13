"""Model-agnostic client interface (FR7). Every provider client implements
`generate(prompt) -> str` and exposes `.name` / `.min_interval_seconds`
(the last used by the batch runner to pace requests within a provider's
free-tier rate limit -- see each client module for the specific numbers and
the caveat that free-tier limits shift over time and should be reconfirmed
live before a real run)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class MissingAPIKeyError(Exception):
    """Raised when a provider's API key env var is not set. The batch
    runner treats this as "skip this model" rather than a fatal error."""


@runtime_checkable
class ModelClient(Protocol):
    name: str
    min_interval_seconds: float

    def generate(self, prompt: str) -> str:
        """Return the raw text response for a single prompt. Must raise on
        failure (network error, non-2xx, malformed response) rather than
        returning an empty string, so the runner can distinguish a real
        (if unparseable) answer from a failed call."""
        ...
