from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.district import DistrictResponse
from app.schemas.grid_substation import GridSubstationResponse
from app.schemas.generation_reading import GenerationReadingResponse


class SolarInstallationBase(BaseModel):
    name: str = Field(..., example="Kelaniya Industrial Solar 01")
    meter_id: str = Field(..., description="Inverter/Meter identifier strictly modeled on installation", example="MTR-WP-COL-0012")
    inverter_serial: Optional[str] = Field(default=None, example="INV-SMA-892348")
    capacity_kw: float = Field(..., gt=0.0, description="Installed DC capacity in kW", example=50.0)
    installation_type: str = Field(default="rooftop", description="rooftop, ground-mounted, floating", example="rooftop")
    status: str = Field(default="active", description="active, maintenance, decommissioned", example="active")
    district_id: int = Field(..., example=1)
    grid_substation_id: int = Field(..., example=1)
    commissioned_date: Optional[date] = Field(default=None, example="2023-01-15")


class SolarInstallationCreate(SolarInstallationBase):
    pass


class SolarInstallationResponse(SolarInstallationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SolarInstallationComposite(SolarInstallationResponse):
    """
    Composite operational resource combining installation, geographic hierarchy,
    substation, and dynamically derived operational metrics (derived without storing last-values on entity).
    """
    district: Optional[DistrictResponse] = None
    grid_substation: Optional[GridSubstationResponse] = None
    last_known_reading: Optional[GenerationReadingResponse] = Field(
        default=None,
        description="Dynamically computed most recent reading (Strict Rule 2 compliant)"
    )

    model_config = ConfigDict(from_attributes=True)
