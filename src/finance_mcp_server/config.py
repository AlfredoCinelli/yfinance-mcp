"""Application configuration loaded from environment variables and .env file."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / "local" / ".env"


class MCPSettings(BaseSettings):
    """MCP settings with validation and .env support."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: Annotated[str, Field(default="0.0.0.0", description="Server bind address")]
    port: Annotated[int, Field(default=1000, ge=1, le=65535, description="Server bind port")]

    # MCP
    mcp_path: Annotated[str, Field(default="/mcp", description="MCP endpoint sub-path")]
    mcp_mount_path: Annotated[str, Field(default="/stocks", description="FastAPI mount path for the MCP app")]
    stateless_http: Annotated[bool, Field(default=True, description="Run MCP in stateless HTTP mode")]
    mcp_transport: Annotated[
        Literal["stdio", "http", "streamable-http"],
        Field(default="streamable-http", description="MCP Client-Server communication transport"),
    ]

    # Auth metadata (raw JSON string from .env)
    auth_metadata: Annotated[str, Field(default="", description="OAuth protected resource metadata JSON")]


class ScalekitSettings(BaseSettings):
    """Scalekit settings with .env support."""
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    client_id: Annotated[str, Field(..., description="Scalekit client identifier")]
    env_url: Annotated[str, Field(..., description="Scalekit environment url")]
    client_secret: Annotated[str, Field(..., description="Scalekit client secret")]
    audience: Annotated[str, Field(default="", description="Expected token audience")]
    resource_metadata_url: Annotated[
        str,
        Field(default="/.well-known/oauth-protected-resource", description="OAuth resource metadata URL"),
    ]
    tool_scopes: Annotated[list[str], Field(default=["users:read"], description="Required scopes for tool calls")]
    public_paths: Annotated[
        list[str],
        Field(default=["/.well-known/", "/health", "/docs", "/openapi.json"], description="Paths that bypass auth"),
    ]


@lru_cache(maxsize=1)
def get_mcp_settings() -> MCPSettings:
    """Return cached MCP settings singleton."""
    return MCPSettings()


@lru_cache(maxsize=1)
def get_scalekit_settings() -> ScalekitSettings:
    """Return cached Scalekit settings singleton."""
    return ScalekitSettings()
