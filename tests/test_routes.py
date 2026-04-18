"""Tests for operational routes (/health, /info)."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from finance_mcp_server.routes.ops import router

pytestmark = pytest.mark.routes


@pytest.fixture
def client():
    """Create a test client with just the ops router (no auth middleware)."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestInfoEndpoint:
    """Tests for GET /info."""

    def test_info_returns_metadata(self, client):
        resp = client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Finance MCP Server"
        assert data["mcp_endpoint"] == "/stocks/mcp"
        assert "tools" in data
        assert isinstance(data["tools"], dict)

    def test_info_includes_expected_tools(self, client):
        resp = client.get("/info")
        tools = resp.json()["tools"]
        assert "get_stock_price" in tools
        assert "get_multiple_stocks_prices" in tools


class TestOAuthMetadata:
    """Tests for GET /.well-known/oauth-protected-resource."""

    @patch("finance_mcp_server.routes.ops.get_mcp_settings")
    def test_returns_parsed_metadata(self, mock_settings, client):
        from unittest.mock import MagicMock

        settings = MagicMock()
        settings.auth_metadata = '{"resource": "https://example.com", "scopes_supported": ["read"]}'
        mock_settings.return_value = settings

        resp = client.get("/.well-known/oauth-protected-resource")

        assert resp.status_code == 200
        data = resp.json()
        assert data["resource"] == "https://example.com"
        assert "scopes_supported" in data
