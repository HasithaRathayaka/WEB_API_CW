from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.district import DistrictResponse


class GridSubstationBase(BaseModel):
    name: str = Field(..., example="Kolonnawa Grid Substation")
    code: str = Field(..., example="GS-KLN-01")
    district_id: int = Field(..., example=1)
    capacity_mva: Optional[float] = Field(default=None, example=63.0)
    voltage_level_kv: Optional[float] = Field(default=None, example=132.0)


class GridSubstationCreate(GridSubstationBase):
    pass


class GridSubstationResponse(GridSubstationBase):
    id: int
    district: Optional[DistrictResponse] = None

    model_config = ConfigDict(from_attributes=True)
