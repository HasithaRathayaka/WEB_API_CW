from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Consistent JSON error schema across the entire API as mandated by specification.
    Contains code, message, and detailed context.
    """
    code: str = Field(..., description="Machine-readable error code", example="RESOURCE_NOT_FOUND")
    message: str = Field(..., description="Human-readable error description", example="The requested solar installation was not found")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Detailed context or error metadata", example={"installation_id": 42})
