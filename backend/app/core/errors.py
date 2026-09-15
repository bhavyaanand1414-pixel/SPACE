from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class SIH1518Exception(Exception):
    """Base exception class for SIH1518 application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ImageValidationError(SIH1518Exception):
    """Raised when satellite imagery fails CRS, overlap, or format validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AnalysisNotFoundError(SIH1518Exception):
    """Raised when an analysis job cannot be found."""

    def __init__(self, analysis_id: str):
        super().__init__(
            message=f"Analysis job '{analysis_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"analysis_id": analysis_id},
        )


async def sih1518_exception_handler(request: Request, exc: SIH1518Exception) -> JSONResponse:
    """Centralized handler for custom domain exceptions."""
    logger.error(
        f"Domain Exception on {request.method} {request.url.path}: {exc.message} (Status: {exc.status_code})"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled internal exceptions."""
    logger.exception(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred while processing the request.",
            }
        },
    )
