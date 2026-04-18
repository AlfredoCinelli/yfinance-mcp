"""Entrypoint for the Finance MCP Server."""

import uvicorn

from .app import create_app
from .config import get_mcp_settings
from .misc.art import _print_banner


def main() -> None:
    """Start the Finance MCP Server."""
    settings = get_mcp_settings()
    _print_banner(settings.host, settings.port, settings.mcp_transport)
    app = create_app()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()