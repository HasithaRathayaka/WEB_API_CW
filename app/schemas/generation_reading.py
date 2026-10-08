from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GenerationReadingBase(BaseModel):
    timestamp: datetime = Field(..., description="Measurement timestamp with timezone")
    power_kw: float = Field(..., ge=0.0, description="Instantaneous power output in kilowatts (kW)", example=14.5)
    energy_kwh: float = Field(..., ge=0.0, description="Cumulative generation energy in kilowatt-hours (kWh)", example=1285.4)
    voltage: float = Field(..., gt=0.0, description="AC Grid voltage in Volts (V)", example=230.2)


class GenerationReadingCreate(GenerationReadingBase):
    pass


class GenerationReadingResponse(GenerationReadingBase):
    id: int
    installation_id: int

    model_config = ConfigDict(from_attributes=True)


class PaginatedReadingsResponse(BaseModel):
    """
    Pagination response conforming to REST standards with count, total_count, and next/prev links.
    """
    count: int = Field(..., description="Number of items returned in current page")
    total_count: int = Field(..., description="Total count matching query filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size limit")
    next: Optional[str] = Field(default=None, description="URL link to next page")
    prev: Optional[str] = Field(default=None, description="URL link to previous page")
    results: List[GenerationReadingResponse] = Field(..., description="Array of generation readings")
