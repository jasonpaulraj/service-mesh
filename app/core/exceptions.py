"""
Custom exceptions and exception handlers.
"""
import logging
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Error response model for API errors."""
    
    status: str = "error"
    message: str
    detail: Optional[Any] = None


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers for the application.
    
    Args:
        app: FastAPI application
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle validation errors.
        
        Args:
            request: Request object
            exc: Exception
            
        Returns:
            JSONResponse: Error response
        """
        errors = exc.errors()
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                message="Validation error",
                detail=errors,
            ).dict(),
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle generic exceptions.
        
        Args:
            request: Request object
            exc: Exception
            
        Returns:
            JSONResponse: Error response
        """
        logger.exception(f"Unhandled exception: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                message="Internal server error",
                detail=str(exc),
            ).dict(),
        )
