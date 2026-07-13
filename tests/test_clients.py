import json

import pytest

from tom_bench.clients.anthropic import build_payload as anthropic_payload
from tom_bench.clients.anthropic import parse_response as anthropic_parse
from tom_bench.clients.base import MissingAPIKeyError
from tom_bench.clients.cloudflare import build_payload as cloudflare_payload
from tom_bench.clients.cloudflare import parse_response as cloudflare_parse
from tom_bench.clients.gemini import build_payload as gemini_payload
from tom_bench.clients.gemini import parse_response as gemini_parse
from tom_bench.clients.groq import build_payload as groq_payload
from tom_bench.clients.groq import parse_response as groq_parse
from tom_bench.clients.huggingface import build_payload as hf_payload
from tom_bench.clients.huggingface import parse_response as hf_parse
from tom_bench.clients.mock import MockClient


def test_gemini_payload_shape():
    payload = gemini_payload("hello")
    assert payload["contents"][0]["parts"][0]["text"] == "hello"


def test_gemini_parse_response():
    body = {"candidates": [{"content": {"parts": [{"text": '{"assist_location": "kitchen"}'}]}}]}
    assert gemini_parse(body) == '{"assist_location": "kitchen"}'


def test_gemini_parse_response_raises_on_empty_candidates():
    with pytest.raises(ValueError):
        gemini_parse({"candidates": []})


def test_groq_payload_shape():
    payload = groq_payload("hello", "llama-3.1-8b-instant")
    assert payload["messages"][0]["content"] == "hello"
    assert payload["model"] == "llama-3.1-8b-instant"


def test_groq_parse_response():
    body = {"choices": [{"message": {"content": '{"answer": "A"}'}}]}
    assert groq_parse(body) == '{"answer": "A"}'


def test_anthropic_payload_shape():
    payload = anthropic_payload("hello", "claude-haiku-4-5-20251001")
    assert payload["messages"][0]["content"] == "hello"
    assert payload["model"] == "claude-haiku-4-5-20251001"


def test_anthropic_parse_response():
    body = {"content": [{"type": "text", "text": '{"assist_location": "attic"}'}]}
    assert anthropic_parse(body) == '{"assist_location": "attic"}'


def test_gemini_missing_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tom_bench.clients.gemini import GeminiClient

    with pytest.raises(MissingAPIKeyError):
        GeminiClient()


def test_huggingface_payload_shape():
    payload = hf_payload("hello", "meta-llama/Llama-3.1-8B-Instruct")
    assert payload["messages"][0]["content"] == "hello"
    assert payload["model"] == "meta-llama/Llama-3.1-8B-Instruct"


def test_huggingface_parse_response():
    body = {"choices": [{"message": {"content": '{"assist_location": "garage"}'}}]}
    assert hf_parse(body) == '{"assist_location": "garage"}'


def test_huggingface_parse_response_raises_on_empty_choices():
    with pytest.raises(ValueError):
        hf_parse({"choices": []})


def test_huggingface_missing_key_raises(monkeypatch):
    monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)
    from tom_bench.clients.huggingface import HuggingFaceClient

    with pytest.raises(MissingAPIKeyError):
        HuggingFaceClient()


def test_cloudflare_payload_shape():
    payload = cloudflare_payload("hello")
    assert payload["messages"][0]["content"] == "hello"


def test_cloudflare_parse_response():
    body = {"success": True, "result": {"response": '{"answer": "B"}'}}
    assert cloudflare_parse(body) == '{"answer": "B"}'


def test_cloudflare_parse_response_raises_on_failure():
    with pytest.raises(ValueError):
        cloudflare_parse({"success": False, "errors": ["bad token"]})


def test_cloudflare_parse_response_reserializes_dict_shaped_response():
    # Some Workers AI models auto-detect JSON-shaped output and return it
    # already parsed as an object instead of a raw string.
    body = {"success": True, "result": {"response": {"assist_location": "kitchen"}}}
    raw = cloudflare_parse(body)
    assert isinstance(raw, str)
    assert json.loads(raw) == {"assist_location": "kitchen"}


def test_cloudflare_missing_creds_raises(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    from tom_bench.clients.cloudflare import CloudflareClient

    with pytest.raises(MissingAPIKeyError):
        CloudflareClient()


def test_cloudflare_missing_only_account_id_raises(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "dummy-token")
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    from tom_bench.clients.cloudflare import CloudflareClient

    with pytest.raises(MissingAPIKeyError):
        CloudflareClient()


def test_mock_client_returns_valid_room_from_interactive_prompt():
    client = MockClient(name="mock", seed=1)
    prompt = "blah blah\nValid locations: kitchen, garage, attic\n\nRespond..."
    raw = client.generate(prompt)
    assert raw.strip().startswith("{")
    assert any(room in raw for room in ("kitchen", "garage", "attic"))


def test_mock_client_deterministic_for_same_prompt():
    client_a = MockClient(name="mock", seed=1)
    client_b = MockClient(name="mock", seed=1)
    prompt = "Valid locations: kitchen, garage, attic"
    assert client_a.generate(prompt) == client_b.generate(prompt)
