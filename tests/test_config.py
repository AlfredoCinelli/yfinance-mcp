"""Tests for MCPSettings and ScalekitSettings configuration."""

import pytest

from finance_mcp_server.config import MCPSettings, ScalekitSettings

pytestmark = pytest.mark.config


class TestMCPSettings:
    """Tests for MCPSettings with env-var overrides."""

    def test_defaults(self):
        settings = MCPSettings(_env_file=None)

        assert settings.host == "0.0.0.0"
        assert settings.port == 1000
        assert settings.mcp_path == "/mcp"
        assert settings.mcp_mount_path == "/stocks"
        assert settings.stateless_http is True
        assert settings.mcp_transport == "streamable-http"
        assert settings.auth_metadata == ""

    @pytest.mark.parametrize(
        ("env_var", "env_value", "attr", "expected"),
        [
            pytest.param("HOST", "127.0.0.1", "host", "127.0.0.1", id="custom-host"),
            pytest.param("PORT", "8080", "port", 8080, id="custom-port"),
            pytest.param("MCP_PATH", "/custom", "mcp_path", "/custom", id="custom-mcp-path"),
            pytest.param("MCP_MOUNT_PATH", "/api", "mcp_mount_path", "/api", id="custom-mount"),
            pytest.param("MCP_TRANSPORT", "stdio", "mcp_transport", "stdio", id="stdio-transport"),
        ],
    )
    def test_env_overrides(self, monkeypatch, env_var, env_value, attr, expected):
        monkeypatch.setenv(env_var, env_value)
        settings = MCPSettings(_env_file=None)
        assert getattr(settings, attr) == expected


class TestScalekitSettings:
    """Tests for ScalekitSettings with env-var overrides."""

    def test_required_fields(self, monkeypatch):
        monkeypatch.setenv("CLIENT_ID", "cid")
        monkeypatch.setenv("ENV_URL", "https://auth.example.com")
        monkeypatch.setenv("CLIENT_SECRET", "secret")
        settings = ScalekitSettings(_env_file=None)

        assert settings.client_id == "cid"
        assert settings.env_url == "https://auth.example.com"
        assert settings.client_secret == "secret"

    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("CLIENT_ID", "cid")
        monkeypatch.setenv("ENV_URL", "https://auth.example.com")
        monkeypatch.setenv("CLIENT_SECRET", "secret")
        settings = ScalekitSettings(_env_file=None)

        assert settings.audience == ""
        assert settings.tool_scopes == ["users:read"]
        assert "/health" in settings.public_paths
        assert "/.well-known/" in settings.public_paths

    def test_missing_required_fields_raises(self):
        with pytest.raises(Exception):
            ScalekitSettings(_env_file=None)

    @pytest.mark.parametrize(
        "path,expected",
        [
            pytest.param("/health", True, id="health-is-public"),
            pytest.param("/.well-known/oauth", True, id="well-known-is-public"),
            pytest.param("/docs", True, id="docs-is-public"),
            pytest.param("/openapi.json", True, id="openapi-is-public"),
            pytest.param("/api/private", False, id="api-not-public"),
            pytest.param("/stocks/mcp", False, id="mcp-not-public"),
        ],
    )
    def test_public_paths_membership(self, monkeypatch, path, expected):
        monkeypatch.setenv("CLIENT_ID", "cid")
        monkeypatch.setenv("ENV_URL", "https://auth.example.com")
        monkeypatch.setenv("CLIENT_SECRET", "secret")
        settings = ScalekitSettings(_env_file=None)

        is_public = any(path.startswith(p) for p in settings.public_paths)
        assert is_public is expected
