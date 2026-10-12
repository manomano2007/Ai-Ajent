from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from groq import APIConnectionError, APIStatusError, Groq, RateLimitError

from app import main
from app.services import groq_service
from app.services.groq_service import GroqServiceError, create_chat_completion

client = TestClient(main.app)

FAKE_KEY = "gsk_test_key_for_unit_tests_only"


class FakeClient:
    def __init__(self, create_fn):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create_fn))


def _completion(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _status_exc(cls, status_code):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return cls("simulated error", response=response, body=None)


def _use_fake(monkeypatch, create_fn):
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)
    monkeypatch.setattr(groq_service, "get_client", lambda: FakeClient(create_fn))


def test_get_client_builds_groq_with_settings(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)
    assert isinstance(groq_service.get_client(), Groq)


def test_missing_key_raises_friendly_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == 500
    assert "GROQ_API_KEY" in info.value.user_message


def test_success_returns_stripped_text(monkeypatch):
    _use_fake(monkeypatch, lambda **kwargs: _completion("  Hello there  "))
    assert create_chat_completion([{"role": "user", "content": "hi"}]) == "Hello there"


def test_model_comes_from_environment(monkeypatch):
    seen = {}

    def fake_create(**kwargs):
        seen.update(kwargs)
        return _completion("ok")

    _use_fake(monkeypatch, fake_create)
    monkeypatch.setenv("GROQ_MODEL", "test-model-name")
    create_chat_completion([{"role": "user", "content": "hi"}])
    assert seen["model"] == "test-model-name"


def test_empty_answer_is_an_error(monkeypatch):
    _use_fake(monkeypatch, lambda **kwargs: _completion("   "))
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == 502


def test_malformed_response_is_an_error(monkeypatch):
    _use_fake(monkeypatch, lambda **kwargs: SimpleNamespace(choices=[]))
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == 502


def test_rate_limit_maps_to_429(monkeypatch):
    def fake_create(**kwargs):
        raise _status_exc(RateLimitError, 429)

    _use_fake(monkeypatch, fake_create)
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == 429


def test_connection_error_maps_to_502(monkeypatch):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")

    def fake_create(**kwargs):
        raise APIConnectionError(request=request)

    _use_fake(monkeypatch, fake_create)
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == 502


@pytest.mark.parametrize(
    "http_status, expected_status",
    [(401, 401), (403, 401), (404, 502), (400, 400), (500, 503), (503, 503)],
)
def test_status_codes_are_mapped(monkeypatch, http_status, expected_status):
    def fake_create(**kwargs):
        raise _status_exc(APIStatusError, http_status)

    _use_fake(monkeypatch, fake_create)
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert info.value.status_code == expected_status


def test_error_messages_never_contain_the_key(monkeypatch):
    def fake_create(**kwargs):
        raise _status_exc(APIStatusError, 401)

    _use_fake(monkeypatch, fake_create)
    with pytest.raises(GroqServiceError) as info:
        create_chat_completion([{"role": "user", "content": "hi"}])
    assert FAKE_KEY not in info.value.user_message


def test_chat_endpoint_success(monkeypatch):
    _use_fake(monkeypatch, lambda **kwargs: _completion("A list is ordered."))
    response = client.post("/api/chat", json={"message": "What is a list?"})
    assert response.status_code == 200
    assert response.json()["reply"] == "A list is ordered."


def test_chat_endpoint_rejects_blank_message():
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_endpoint_shows_missing_key_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 500
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_ping_endpoint_returns_reply(monkeypatch):
    _use_fake(monkeypatch, lambda **kwargs: _completion("PyMate AI connected"))
    response = client.post("/api/ai/ping")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["reply"] == "PyMate AI connected"