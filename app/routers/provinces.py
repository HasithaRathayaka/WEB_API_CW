from typing import List
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.province import Province
from app.schemas.province import ProvinceCreate, ProvinceResponse
from app.core.dependencies import get_current_client, require_any_scope, AuthenticatedEntity
from app.core.exceptions import NotFoundException, ConflictException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/provinces", tags=["Provinces"])


@router.get(
    "",
    response_model=List[ProvinceResponse],
    summary="List all provinces"
)
def list_provinces(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """List all Sri Lankan provinces. Supports ETag conditional caching."""
    provinces = db.query(Province).order_by(Province.name.asc()).all()
    data = [ProvinceResponse.model_validate(p).model_dump() for p in provinces]
    
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return provinces


@router.get(
    "/{province_id}",
    response_model=ProvinceResponse,
    summary="Retrieve a province by ID"
)
def get_province(
    province_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "admin"]))
):
    """Retrieve details of a single province with ETag support."""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise NotFoundException(
            message=f"Province with ID {province_id} does not exist",
            context={"province_id": province_id}
        )

    data = ProvinceResponse.model_validate(province).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return province


@router.post(
    "",
    response_model=ProvinceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new province"
)
def create_province(
    province_in: ProvinceCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """Create a new province. Enforces Location header on 201 Created."""
    existing = db.query(Province).filter(
        (Province.name == province_in.name) | (Province.code == province_in.code)
    ).first()
    if existing:
        raise ConflictException(
            message="Province with this name or code already exists",
            context={"name": province_in.name, "code": province_in.code}
        )

    province = Province(name=province_in.name, code=province_in.code)
    db.add(province)
    db.commit()
    db.refresh(province)

    response.headers["Location"] = f"/api/v1/provinces/{province.id}"
    return province
