from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.district import District
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.schemas.summary import DistrictGenerationSummary
from app.core.dependencies import (
    require_any_scope,
    verify_district_read_access,
    AuthenticatedEntity
)
from app.core.exceptions import NotFoundException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/district-generation-summaries", tags=["District Generation Summaries"])


@router.get(
    "/{district_id}",
    response_model=DistrictGenerationSummary,
    summary="Compute district generation summary (Stretch Goal)"
)
def get_district_generation_summary(
    district_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """
    Stretch Goal: District generation summary resource computing total power and energy
    across all installations within a district.
    Strictly prevents cross-jurisdiction leakage. Supports ETag headers and 304 Not Modified.
    """
    verify_district_read_access(district_id, client, db)

    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise NotFoundException(
            message=f"District with ID {district_id} does not exist",
            context={"district_id": district_id}
        )

    installations = db.query(SolarInstallation).filter(SolarInstallation.district_id == district_id).all()
    total_count = len(installations)
    active_installations = [inst for inst in installations if inst.status == "active"]
    active_count = len(active_installations)
    total_capacity = sum(inst.capacity_kw for inst in installations)

    current_power = 0.0
    total_energy = 0.0
    voltages = []

    # Dynamically compute from append-only series (Strict Rule 2)
    for inst in active_installations:
        latest_reading = (
            db.query(GenerationReading)
            .filter(GenerationReading.installation_id == inst.id)
            .order_by(GenerationReading.timestamp.desc())
            .first()
        )
        if latest_reading:
            current_power += latest_reading.power_kw
            total_energy += latest_reading.energy_kwh
            voltages.append(latest_reading.voltage)

    avg_voltage = (sum(voltages) / len(voltages)) if voltages else None

    summary_obj = DistrictGenerationSummary(
        district_id=district.id,
        district_name=district.name,
        district_code=district.code,
        province_id=district.province.id,
        province_name=district.province.name,
        total_installations_count=total_count,
        active_installations_count=active_count,
        total_installed_capacity_kw=round(total_capacity, 2),
        current_aggregate_power_kw=round(current_power, 2),
        total_cumulative_energy_kwh=round(total_energy, 2),
        average_voltage=round(avg_voltage, 2) if avg_voltage else None,
        timestamp=datetime.now(timezone.utc)
    )

    data = summary_obj.model_dump()
    etag_data = {k: v for k, v in data.items() if k != "timestamp"}
    etag = generate_etag(etag_data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return summary_obj
