from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = client.get("/api/health")
    assert response.json()["groq_api_key_configured"] is False


def test_health_never_returns_the_key(monkeypatch):
    secret = "gsk_test_secret_value_12345"
    monkeypatch.setenv("GROQ_API_KEY", secret)
    response = client.get("/api/health")
    assert response.json()["groq_api_key_configured"] is True
    assert secret not in response.text


def test_analyze_valid_code():
    response = client.post("/api/analyze", json={"code": "x = 1\n"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_analyze_rejects_empty_code():
    response = client.post("/api/analyze", json={"code": ""})
    assert response.status_code == 422


def test_analyze_rejects_blank_code():
    response = client.post("/api/analyze", json={"code": "    "})
    assert response.status_code == 422


def test_traceback_endpoint_explains_error():
    text = (
        'Traceback (most recent call last):\n'
        '  File "a.py", line 2, in <module>\n'
        "ZeroDivisionError: division by zero"
    )
    response = client.post("/api/traceback/explain", json={"text": text})
    assert response.status_code == 200
    assert response.json()["exception_type"] == "ZeroDivisionError"