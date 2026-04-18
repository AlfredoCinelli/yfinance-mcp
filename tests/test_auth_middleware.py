"""Tests for AuthMiddleware – Scalekit client is always mocked."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from finance_mcp_server.middleware.auth import AuthMiddleware

pytestmark = pytest.mark.middleware


@pytest.fixture
def _mock_scalekit():
    """Patch ScalekitClient so it never makes real HTTP calls."""
    with patch("finance_mcp_server.middleware.auth.ScalekitClient") as cls:
        mock_instance = MagicMock()
        cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def app_with_auth(scalekit_settings, _mock_scalekit):
    """Return a FastAPI app with AuthMiddleware and a protected test route."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, settings=scalekit_settings)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/protected")
    async def protected():
        return {"data": "secret"}

    return app


@pytest.fixture
def client(app_with_auth):
    return TestClient(app_with_auth, raise_server_exceptions=False)


class TestPublicPaths:
    """Public paths should bypass authentication."""

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/health", id="health"),
            pytest.param("/.well-known/oauth-protected-resource", id="well-known"),
            pytest.param("/docs", id="docs"),
            pytest.param("/openapi.json", id="openapi"),
        ],
    )
    def test_public_path_bypasses_auth(self, client, path):
        resp = client.get(path)
        # /health returns 200; others may 404, but should NOT be 401
        assert resp.status_code != 401


class TestProtectedPaths:
    """Protected paths require valid Bearer tokens."""

    def test_missing_auth_header_returns_401(self, client):
        resp = client.get("/protected")
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    @pytest.mark.parametrize(
        "header_value",
        [
            pytest.param("Basic abc123", id="basic-scheme"),
            pytest.param("Token abc123", id="token-scheme"),
            pytest.param("bearer lowercase", id="lowercase-bearer"),
            pytest.param("", id="empty"),
        ],
    )
    def test_malformed_auth_header_returns_401(self, client, header_value):
        resp = client.get("/protected", headers={"Authorization": header_value})
        assert resp.status_code == 401

    def test_valid_token_passes(self, client, _mock_scalekit):
        _mock_scalekit.validate_access_token.return_value = True

        resp = client.get("/protected", headers={"Authorization": "Bearer valid-token"})

        assert resp.status_code == 200
        assert resp.json() == {"data": "secret"}
        _mock_scalekit.validate_access_token.assert_called_once_with("valid-token")

    def test_invalid_token_returns_401(self, client, _mock_scalekit):
        _mock_scalekit.validate_access_token.return_value = False

        resp = client.get("/protected", headers={"Authorization": "Bearer bad-token"})

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid token"

    def test_token_validation_exception_returns_401(self, client, _mock_scalekit):
        _mock_scalekit.validate_access_token.side_effect = Exception("Network error")

        resp = client.get("/protected", headers={"Authorization": "Bearer crash-token"})

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Token validation failed"
