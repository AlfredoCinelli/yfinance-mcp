"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.utilities.lifespan import combine_lifespans

from .config import get_mcp_settings, get_scalekit_settings
from .mcp_servers.stock import mcp as stock_mcp
from .middleware import AuthMiddleware
from .routes.ops import router as ops_router


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application.

    Returns:
        FastAPI app.    
    """
    settings = get_mcp_settings()
    scalekit_settings = get_scalekit_settings()

    stock_mcp_app = stock_mcp.http_app(
        path=settings.mcp_path,
        transport=settings.mcp_transport,
        stateless_http=settings.stateless_http,
    )

    app = FastAPI(
        title="Finance MCP Server",
        lifespan=combine_lifespans(stock_mcp_app.lifespan),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(AuthMiddleware, settings=scalekit_settings)

    app.include_router(ops_router)

    app.mount(
        path=settings.mcp_mount_path,
        app=stock_mcp_app,
    )

    return app
