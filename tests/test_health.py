"""Tests for health check and system information endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Verify health endpoint returns 200 OK and valid status json."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "version" in data
    assert "app_name" in data


def test_root_endpoint(client: TestClient) -> None:
    """Verify root landing endpoint provides API navigation info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/health"
    assert "app" in data
