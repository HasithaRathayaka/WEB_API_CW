from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., example="colombo_analyst")
    role: str = Field(default="analyst", description="admin, analyst, device")
    jurisdiction_type: str = Field(default="district", description="national, province, district, installation")
    jurisdiction_id: Optional[int] = Field(default=None, example=1)
    scopes: str = Field(default="analyst-read-district", description="Space-separated scopes")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
