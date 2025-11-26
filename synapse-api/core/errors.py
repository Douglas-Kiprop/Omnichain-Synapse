from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class SynapseAPIError(Exception):
    """Base exception for Synapse API"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(SynapseAPIError):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationError(SynapseAPIError):
    """Authorization related errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class ValidationError(SynapseAPIError):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 422)

class ConflictError(SynapseAPIError):
    """Resource conflict errors (e.g., duplicate unique keys)"""
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, 409)

# Add NotFoundError to support strategy service/router
class NotFoundError(SynapseAPIError):
    """Resource not found errors"""
    def __init__(self, message: str = "Not found"):
        super().__init__(message, 404)


async def synapse_exception_handler(request: Request, exc: SynapseAPIError):
    """Handle custom Synapse API exceptions"""
    logger.error(f"SynapseAPIError: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": type(exc).__name__}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Database error occurred", "type": "DatabaseError"}
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": "InternalError"}
    )


def add_exception_handlers(app: FastAPI):
    """Add all exception handlers to the FastAPI app"""
    app.add_exception_handler(SynapseAPIError, synapse_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)