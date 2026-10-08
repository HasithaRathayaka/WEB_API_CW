from typing import Any, Dict, Optional
from fastapi import status


class APIException(Exception):
    """Base API Exception complying with consistent JSON error schema."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        message: str = "An error occurred while processing the request",
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.context = context or {}
        self.headers = headers or {}
        super().__init__(message)


class NotFoundException(APIException):
    def __init__(self, message: str = "Resource not found", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=message,
            context=context
        )


class UnauthorizedException(APIException):
    def __init__(self, message: str = "Authentication credentials were not provided or are invalid", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
            context=context,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(APIException):
    def __init__(self, message: str = "Access forbidden for current jurisdiction or scope", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
            context=context
        )


class ConflictException(APIException):
    def __init__(self, message: str = "Resource conflict detected", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=message,
            context=context
        )


class ValidationException(APIException):
    def __init__(self, message: str = "Validation failed for request parameters or payload", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            context=context
        )
