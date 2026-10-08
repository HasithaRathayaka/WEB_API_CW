from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.district import District
from app.models.province import Province
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.schemas.district import DistrictCreate, DistrictResponse
from app.schemas.summary import DistrictGenerationSummary
from app.core.dependencies import (
    require_any_scope,
    verify_district_read_access,
    AuthenticatedEntity
)
from app.core.exceptions import NotFoundException, ConflictException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/districts", tags=["Districts"])


@router.get(
    "",
    response_model=List[DistrictResponse],
    summary="List districts with optional province filtering"
)
def list_districts(
    request: Request,
    response: Response,
    province_id: Optional[int] = Query(None, description="Filter districts by province ID"),
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """List districts. Scoped to caller's jurisdiction where appropriate."""
    query = db.query(District)

    # Restrict to assigned province if user only has province scope
    if client.role != "admin" and (client.has_scope("analyst-read-province") or client.jurisdiction_type == "province"):
        query = query.filter(District.province_id == client.jurisdiction_id)
    elif province_id:
        query = query.filter(District.province_id == province_id)

    # Restrict to assigned district if user only has district scope
    if client.role != "admin" and (client.has_scope("analyst-read-district") or client.jurisdiction_type == "district"):
        query = query.filter(District.id == client.jurisdiction_id)

    districts = query.order_by(District.name.asc()).all()
    data = [DistrictResponse.model_validate(d).model_dump() for d in districts]

    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return districts


@router.get(
    "/{district_id}",
    response_model=DistrictResponse,
    summary="Retrieve a district by ID"
)
def get_district(
    district_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """Retrieve district details with jurisdiction boundary check and ETag support."""
    verify_district_read_access(district_id, client, db)

    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise NotFoundException(
            message=f"District with ID {district_id} does not exist",
            context={"district_id": district_id}
        )

    data = DistrictResponse.model_validate(district).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return district


@router.post(
    "",
    response_model=DistrictResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new district"
)
def create_district(
    district_in: DistrictCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """Create a new district. Enforces Location header on 201 Created."""
    province = db.query(Province).filter(Province.id == district_in.province_id).first()
    if not province:
        raise NotFoundException(
            message=f"Province with ID {district_in.province_id} does not exist",
            context={"province_id": district_in.province_id}
        )

    existing = db.query(District).filter(
        (District.name == district_in.name) | (District.code == district_in.code)
    ).first()
    if existing:
        raise ConflictException(
            message="District with this name or code already exists",
            context={"name": district_in.name, "code": district_in.code}
        )

    district = District(
        name=district_in.name,
        code=district_in.code,
        province_id=district_in.province_id
    )
    db.add(district)
    db.commit()
    db.refresh(district)

    response.headers["Location"] = f"/api/v1/districts/{district.id}"
    return district


@router.get(
    "/{district_id}/generation-summaries",
    response_model=DistrictGenerationSummary,
    summary="Compute district generation summary (alias)"
)
def get_district_generation_summary(
    district_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """
    Stretch Goal: Compute aggregate generation metrics for all solar installations in the district.
    Strictly prevents cross-jurisdiction data leakage. Supports ETag headers.
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

    # Dynamically aggregate from latest append-only readings (Strict Rule 2)
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
