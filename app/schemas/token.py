from typing import List, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifespan in seconds")
    scopes: List[str] = Field(..., description="Assigned authorization scopes")
    role: str = Field(..., description="Client role")
    jurisdiction_type: str = Field(..., description="Jurisdiction type")
    jurisdiction_id: Optional[int] = Field(default=None, description="Jurisdiction identifier")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="SLSEA User username")
    password: str = Field(..., description="User password")


class DeviceTokenRequest(BaseModel):
    meter_id: str = Field(..., description="Solar installation meter identifier")
    installation_id: int = Field(..., description="Target solar installation ID")
