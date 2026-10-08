from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.grid_substation import GridSubstation
from app.models.district import District
from app.schemas.grid_substation import GridSubstationCreate, GridSubstationResponse
from app.core.dependencies import require_any_scope, AuthenticatedEntity
from app.core.exceptions import NotFoundException, ConflictException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/grid-substations", tags=["Grid Substations"])


@router.get(
    "",
    response_model=List[GridSubstationResponse],
    summary="List grid substations"
)
def list_grid_substations(
    request: Request,
    response: Response,
    district_id: Optional[int] = Query(None, description="Filter by district ID"),
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """List grid substations. Supports ETag conditional GETs."""
    query = db.query(GridSubstation)

    # Scoping by jurisdiction
    if client.role != "admin" and (client.has_scope("analyst-read-district") or client.jurisdiction_type == "district"):
        query = query.filter(GridSubstation.district_id == client.jurisdiction_id)
    elif district_id:
        query = query.filter(GridSubstation.district_id == district_id)

    substations = query.order_by(GridSubstation.name.asc()).all()
    data = [GridSubstationResponse.model_validate(s).model_dump() for s in substations]

    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return substations


@router.get(
    "/{substation_id}",
    response_model=GridSubstationResponse,
    summary="Retrieve grid substation by ID"
)
def get_grid_substation(
    substation_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """Retrieve grid substation details with ETag support."""
    substation = db.query(GridSubstation).filter(GridSubstation.id == substation_id).first()
    if not substation:
        raise NotFoundException(
            message=f"Grid substation with ID {substation_id} does not exist",
            context={"substation_id": substation_id}
        )

    data = GridSubstationResponse.model_validate(substation).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return substation


@router.post(
    "",
    response_model=GridSubstationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new grid substation"
)
def create_grid_substation(
    substation_in: GridSubstationCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """Create a new grid substation. Enforces Location header on 201 Created."""
    district = db.query(District).filter(District.id == substation_in.district_id).first()
    if not district:
        raise NotFoundException(
            message=f"District with ID {substation_in.district_id} does not exist",
            context={"district_id": substation_in.district_id}
        )

    existing = db.query(GridSubstation).filter(GridSubstation.code == substation_in.code).first()
    if existing:
        raise ConflictException(
            message=f"Grid substation with code '{substation_in.code}' already exists",
            context={"code": substation_in.code}
        )

    substation = GridSubstation(
        name=substation_in.name,
        code=substation_in.code,
        district_id=substation_in.district_id,
        capacity_mva=substation_in.capacity_mva,
        voltage_level_kv=substation_in.voltage_level_kv
    )
    db.add(substation)
    db.commit()
    db.refresh(substation)

    response.headers["Location"] = f"/api/v1/grid-substations/{substation.id}"
    return substation
