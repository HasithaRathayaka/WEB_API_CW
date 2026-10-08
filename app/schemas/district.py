from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.province import ProvinceResponse


class DistrictBase(BaseModel):
    name: str = Field(..., example="Colombo")
    code: str = Field(..., example="COL")
    province_id: int = Field(..., example=1)


class DistrictCreate(DistrictBase):
    pass


class DistrictResponse(DistrictBase):
    id: int
    province: Optional[ProvinceResponse] = None

    model_config = ConfigDict(from_attributes=True)
