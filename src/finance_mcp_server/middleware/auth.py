"""Scalekit-based authentication middleware for FastAPI."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from scalekit import ScalekitClient
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import ScalekitSettings, get_scalekit_settings

#import json
#import logging
#from fastapi import HTTPException, Request
#from fastapi.security import HTTPBearer
#from fastapi.responses import JSONResponse
#from scalekit import ScalekitClient
#from scalekit.common.scalekit import TokenValidationOptions
#from starlette.middleware.base import BaseHTTPMiddleware





class AuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer tokens on incoming requests using Scalekit.

    Requests to public paths (health, docs, well-known, etc.) bypass
    authentication. All other requests must carry a valid
    ``Authorization: Bearer <token>`` header.
    """

    def __init__(self, app, settings: ScalekitSettings) -> None:
        """Initialize AuthMiddleware with Scalekit client configuration.

        Args:
            app: FastAPI application instance.
            settings: Scalekit configuration settings.
        """
        super().__init__(app)
        self.settings = settings
        self.client = ScalekitClient(
            env_url=settings.env_url,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
        )
        logger.info("AuthMiddleware initialised (env_url={})", settings.env_url)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Intercept every request and enforce Bearer-token auth.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.

        Returns:
            The response after processing authorization checks.
        """
        if self._is_public(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or malformed Authorization header"},
            )

        token = auth_header.removeprefix("Bearer ")

        try:
            if not self.client.validate_access_token(token):
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})
        except Exception:
            logger.exception("Token validation error")
            return JSONResponse(status_code=401, content={"detail": "Token validation failed"})

        return await call_next(request)

    def _is_public(self, path: str) -> bool:
        """Return True if *path* matches any configured public prefix."""
        return any(path.startswith(prefix) for prefix in self.settings.public_paths)




#security = HTTPBearer()
#
#
## Authentication middleware
#class AuthMiddleware(BaseHTTPMiddleware):
#    def __init__(self, app, settings: ScalekitSettings | None = None):
#        super().__init__(app)
#        self.settings = settings or get_scalekit_settings()
#        self.scalekit_client = ScalekitClient(
#            env_url=self.settings.env_url,
#            client_id=self.settings.client_id,
#            client_secret=self.settings.client_secret,
#        )
#
#    async def dispatch(self, request: Request, call_next):
#        if request.url.path.startswith("/.well-known/"):
#            return await call_next(request)
#
#        try:
#            auth_header = request.headers.get("Authorization")
#            if not auth_header or not auth_header.startswith("Bearer "):
#                raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
#
#            token = auth_header.split(" ")[1]
#
#            request_body = await request.body()
#            
#            # Parse JSON from bytes
#            try:
#                request_data = json.loads(request_body.decode('utf-8'))
#            except (json.JSONDecodeError, UnicodeDecodeError):
#                request_data = {}
#            
#            validation_options = TokenValidationOptions(
#                issuer=self.settings.env_url,
#                audience=[self.settings.audience],
#            )
#            
#            is_tool_call = request_data.get("method") == "tools/call"
#            
#            required_scopes = []
#            if is_tool_call:
#                required_scopes = self.settings.tool_scopes
#                validation_options.required_scopes = required_scopes  
#            
#            try:
#                self.scalekit_client.validate_token(token, options=validation_options)
#                
#            except Exception as e:
#                logger.warning("Token validation error: %s", e)
#                raise HTTPException(status_code=401, detail="Token validation failed")
#
#        except HTTPException as e:
#            return JSONResponse(
#                status_code=e.status_code,
#                content={"error": "unauthorized" if e.status_code == 401 else "forbidden", "error_description": e.detail},
#                headers={
#                    "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{self.settings.resource_metadata_url}"',
#                }
#            )
#
#        return await call_next(request)