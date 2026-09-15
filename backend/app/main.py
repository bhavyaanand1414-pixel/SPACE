from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import SIH1518Exception, sih1518_exception_handler, generic_exception_handler
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and teardown lifecycle."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"API Base URL: {settings.API_V1_STR}")
    logger.info(f"CORS origins configured: {settings.CORS_ORIGINS}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ISRO SIH1518 AI-Powered Multi-Temporal Satellite Change Intelligence Platform API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Exception Handlers
    app.add_exception_handler(SIH1518Exception, sih1518_exception_handler)  # type: ignore
    if not settings.DEBUG:
        app.add_exception_handler(Exception, generic_exception_handler)

    # Include API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Mount static files for Semantic Search image tiles
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    
    tiles_dir = Path(settings.LOCAL_STORAGE_PATH) / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    app.mount(f"{settings.API_V1_STR}/tiles", StaticFiles(directory=tiles_dir), name="tiles")

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return app


app = create_application()
