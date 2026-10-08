from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DistrictGenerationSummary(BaseModel):
    """
    District generation summary resource computing total power and energy across all installations in a district.
    """
    district_id: int = Field(..., example=1)
    district_name: str = Field(..., example="Colombo")
    district_code: str = Field(..., example="COL")
    province_id: int = Field(..., example=1)
    province_name: str = Field(..., example="Western Province")
    total_installations_count: int = Field(..., description="Total solar installations registered in district", example=45)
    active_installations_count: int = Field(..., description="Number of currently active installations", example=43)
    total_installed_capacity_kw: float = Field(..., description="Total installed DC capacity in kW", example=2250.0)
    current_aggregate_power_kw: float = Field(..., description="Sum of most recent instantaneous power readings across active installations", example=1520.4)
    total_cumulative_energy_kwh: float = Field(..., description="Sum of latest cumulative energy across all installations in district", example=450320.8)
    average_voltage: Optional[float] = Field(default=None, description="Average grid voltage among reporting installations", example=231.2)
    timestamp: datetime = Field(..., description="Time at which summary was computed")
