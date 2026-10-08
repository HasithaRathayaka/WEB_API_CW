from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.solar_installation import SolarInstallation
from app.models.grid_substation import GridSubstation
from app.models.district import District
from app.models.generation_reading import GenerationReading
from app.schemas.solar_installation import (
    SolarInstallationCreate,
    SolarInstallationResponse,
    SolarInstallationComposite
)
from app.schemas.generation_reading import GenerationReadingResponse
from app.core.dependencies import (
    require_any_scope,
    verify_jurisdiction_read_access,
    AuthenticatedEntity
)
from app.core.exceptions import NotFoundException, ConflictException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/solar-installations", tags=["Solar Installations"])


@router.get(
    "",
    response_model=List[SolarInstallationResponse],
    summary="List solar installations scoped by jurisdiction"
)
def list_solar_installations(
    request: Request,
    response: Response,
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    substation_id: Optional[int] = Query(None, description="Filter by grid substation ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (active, maintenance, decommissioned)"),
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """
    List solar installations. Automatically enforces jurisdiction boundary:
    District analysts only view installations inside their assigned district.
    Province analysts only view installations inside their assigned province.
    Supports ETag conditional caching.
    """
    query = db.query(SolarInstallation)

    # Scoping by jurisdiction
    if client.role != "admin":
        if client.has_scope("analyst-read-district") or client.jurisdiction_type == "district":
            query = query.filter(SolarInstallation.district_id == client.jurisdiction_id)
        elif client.has_scope("analyst-read-province") or client.jurisdiction_type == "province":
            query = query.join(District).filter(District.province_id == client.jurisdiction_id)

    if district_id:
        query = query.filter(SolarInstallation.district_id == district_id)
    if substation_id:
        query = query.filter(SolarInstallation.grid_substation_id == substation_id)
    if status_filter:
        query = query.filter(SolarInstallation.status == status_filter)

    installations = query.order_by(SolarInstallation.id.asc()).all()
    data = [SolarInstallationResponse.model_validate(inst).model_dump() for inst in installations]

    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return installations


@router.get(
    "/{installation_id}",
    response_model=SolarInstallationComposite,
    summary="Retrieve composite operational resource for a solar installation"
)
def get_solar_installation_composite(
    installation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """
    Operational Read Path: Builds a composite resource combining installation details,
    geographic hierarchy (district, province), grid substation, and dynamically derived
    operational metrics without violating Strict Rule 2 (no last-value fields on entity).
    Enforces strict jurisdiction boundaries and ETag conditional GETs.
    """
    installation = db.query(SolarInstallation).filter(SolarInstallation.id == installation_id).first()
    if not installation:
        raise NotFoundException(
            message=f"Solar installation with ID {installation_id} does not exist",
            context={"installation_id": installation_id}
        )

    verify_jurisdiction_read_access(installation, client, db)

    # Dynamically derive last-known reading from append-only series (Strict Rule 2 compliant)
    latest_reading = (
        db.query(GenerationReading)
        .filter(GenerationReading.installation_id == installation.id)
        .order_by(GenerationReading.timestamp.desc())
        .first()
    )

    last_reading_schema = GenerationReadingResponse.model_validate(latest_reading) if latest_reading else None

    composite_obj = SolarInstallationComposite(
        id=installation.id,
        name=installation.name,
        meter_id=installation.meter_id,
        inverter_serial=installation.inverter_serial,
        capacity_kw=installation.capacity_kw,
        installation_type=installation.installation_type,
        status=installation.status,
        district_id=installation.district_id,
        grid_substation_id=installation.grid_substation_id,
        commissioned_date=installation.commissioned_date,
        created_at=installation.created_at,
        district=installation.district,
        grid_substation=installation.grid_substation,
        last_known_reading=last_reading_schema
    )

    data = composite_obj.model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return composite_obj


@router.get(
    "/{installation_id}/last-known-reading",
    response_model=GenerationReadingResponse,
    summary="Retrieve derived last-known-reading resource per installation"
)
def get_last_known_reading(
    installation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """
    Operational Read Path: Derived 'last-known-reading' resource per installation.
    Derived dynamically from the append-only time series; never stored as last-value on entity (Strict Rule 2).
    Enforces strict jurisdiction boundaries and ETag conditional GETs.
    """
    installation = db.query(SolarInstallation).filter(SolarInstallation.id == installation_id).first()
    if not installation:
        raise NotFoundException(
            message=f"Solar installation with ID {installation_id} does not exist",
            context={"installation_id": installation_id}
        )

    verify_jurisdiction_read_access(installation, client, db)

    latest_reading = (
        db.query(GenerationReading)
        .filter(GenerationReading.installation_id == installation.id)
        .order_by(GenerationReading.timestamp.desc())
        .first()
    )

    if not latest_reading:
        raise NotFoundException(
            message=f"No generation readings recorded yet for installation ID {installation_id}",
            context={"installation_id": installation_id}
        )

    data = GenerationReadingResponse.model_validate(latest_reading).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return latest_reading


@router.post(
    "",
    response_model=SolarInstallationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new solar installation"
)
def create_solar_installation(
    installation_in: SolarInstallationCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """
    Register a new solar installation with meter_id attribute (Strict Rule 1).
    Enforces Location header on 201 Created.
    """
    district = db.query(District).filter(District.id == installation_in.district_id).first()
    if not district:
        raise NotFoundException(
            message=f"District with ID {installation_in.district_id} does not exist",
            context={"district_id": installation_in.district_id}
        )

    substation = db.query(GridSubstation).filter(GridSubstation.id == installation_in.grid_substation_id).first()
    if not substation:
        raise NotFoundException(
            message=f"Grid substation with ID {installation_in.grid_substation_id} does not exist",
            context={"grid_substation_id": installation_in.grid_substation_id}
        )

    existing_meter = db.query(SolarInstallation).filter(SolarInstallation.meter_id == installation_in.meter_id).first()
    if existing_meter:
        raise ConflictException(
            message=f"A solar installation with meter ID '{installation_in.meter_id}' already exists",
            context={"meter_id": installation_in.meter_id}
        )

    installation = SolarInstallation(
        name=installation_in.name,
        meter_id=installation_in.meter_id,
        inverter_serial=installation_in.inverter_serial,
        capacity_kw=installation_in.capacity_kw,
        installation_type=installation_in.installation_type,
        status=installation_in.status,
        district_id=installation_in.district_id,
        grid_substation_id=installation_in.grid_substation_id,
        commissioned_date=installation_in.commissioned_date
    )
    db.add(installation)
    db.commit()
    db.refresh(installation)

    response.headers["Location"] = f"/api/v1/solar-installations/{installation.id}"
    return installation
