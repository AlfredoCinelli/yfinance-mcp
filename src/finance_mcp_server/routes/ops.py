"""Operational endpoints (health, info, OAuth metadata)."""

import json

from fastapi import APIRouter

from ..config import get_mcp_settings
from ..mcp_servers.stock import mcp as stock_mcp

router = APIRouter(tags=["ops"])

_INFO = {
    "name": "Finance MCP Server",
    "description": "Provides MCP tools to fetch historical stock price data via Yahoo Finance.",
    "mcp_endpoint": "/stocks/mcp",
}


@router.get("/health")
async def health() -> dict:
    """Return service liveness status."""
    return {"status": "ok"}


@router.get("/info")
async def info() -> dict:
    """Return service metadata and available MCP tools."""
    tools = {t.name: t.description for t in await stock_mcp.list_tools()}
    return {**_INFO, "tools": tools}


@router.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata() -> dict:
    """Return OAuth protected resource metadata for client discovery."""
    settings = get_mcp_settings()
    return json.loads(settings.auth_metadata)
