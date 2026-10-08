from typing import Optional
from datetime import datetime
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.database import get_db
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.schemas.generation_reading import (
    GenerationReadingCreate,
    GenerationReadingResponse,
    PaginatedReadingsResponse
)
from app.core.dependencies import (
    get_current_client,
    require_any_scope,
    verify_installation_write_access,
    verify_jurisdiction_read_access,
    AuthenticatedEntity
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/solar-installations/{installation_id}/readings", tags=["Generation Readings"])


@router.post(
    "",
    response_model=GenerationReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new generation reading (Write Path)"
)
def create_generation_reading(
    installation_id: int,
    reading_in: GenerationReadingCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["installation-write", "admin"]))
):
    """
    Write Path: Ingestion endpoint for solar devices to POST new readings.
    Enforces strict binding: devices authenticate exclusively as their own installation.
    Returns 201 Created and sets the Location header.
    Strict Rule 2: Appends directly to the time-series without updating last-value on installation.
    """
    installation = db.query(SolarInstallation).filter(SolarInstallation.id == installation_id).first()
    if not installation:
        raise NotFoundException(
            message=f"Solar installation with ID {installation_id} does not exist",
            context={"installation_id": installation_id}
        )

    # Security: Verify that the device owns this installation
    verify_installation_write_access(installation_id, client)

    reading = GenerationReading(
        installation_id=installation_id,
        timestamp=reading_in.timestamp,
        power_kw=reading_in.power_kw,
        energy_kwh=reading_in.energy_kwh,
        voltage=reading_in.voltage
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    location_url = f"/api/v1/solar-installations/{installation_id}/readings/{reading.id}"
    response.headers["Location"] = location_url

    return reading


@router.get(
    "",
    response_model=PaginatedReadingsResponse,
    summary="Scoped analytical readings sub-collection (Read Path)"
)
def list_generation_readings(
    installation_id: int,
    request: Request,
    response: Response,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    sort: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by timestamp (asc or desc)"),
    start_time: Optional[datetime] = Query(None, description="Start timestamp filter (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End timestamp filter (ISO 8601)"),
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "installation-write", "admin"]))
):
    """
    Read Path (Analytical): Scoped readings sub-collection featuring:
    - Pagination with count, total_count, and next/prev hypermedia links
    - Sorting by timestamp (asc or desc)
    - Filtering by time window (start_time, end_time)
    - Jurisdiction boundary protection preventing cross-jurisdiction leakage
    - ETag caching and 304 Not Modified support
    """
    installation = db.query(SolarInstallation).filter(SolarInstallation.id == installation_id).first()
    if not installation:
        raise NotFoundException(
            message=f"Solar installation with ID {installation_id} does not exist",
            context={"installation_id": installation_id}
        )

    # Security: Verify client's jurisdiction permission to read this installation
    verify_jurisdiction_read_access(installation, client, db)

    query = db.query(GenerationReading).filter(GenerationReading.installation_id == installation_id)

    if start_time:
        query = query.filter(GenerationReading.timestamp >= start_time)
    if end_time:
        query = query.filter(GenerationReading.timestamp <= end_time)

    total_count = query.count()

    order_clause = desc(GenerationReading.timestamp) if sort.lower() == "desc" else asc(GenerationReading.timestamp)
    offset = (page - 1) * page_size
    readings = query.order_by(order_clause).offset(offset).limit(page_size).all()

    # Construct next / prev links
    base_url = f"/api/v1/solar-installations/{installation_id}/readings"
    
    def build_page_link(p: int) -> str:
        params = {"page": p, "page_size": page_size, "sort": sort}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        return f"{base_url}?{urlencode(params)}"

    next_link = build_page_link(page + 1) if (offset + page_size) < total_count else None
    prev_link = build_page_link(page - 1) if page > 1 else None

    results = [GenerationReadingResponse.model_validate(r) for r in readings]

    paginated_data = PaginatedReadingsResponse(
        count=len(results),
        total_count=total_count,
        page=page,
        page_size=page_size,
        next=next_link,
        prev=prev_link,
        results=results
    )

    etag = generate_etag(paginated_data.model_dump())
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return paginated_data


@router.get(
    "/{reading_id}",
    response_model=GenerationReadingResponse,
    summary="Retrieve an individual generation reading"
)
def get_generation_reading(
    installation_id: int,
    reading_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["analyst-read-national", "analyst-read-province", "analyst-read-district", "installation-write", "admin"]))
):
    """Retrieve an individual reading with jurisdiction check and ETag support."""
    installation = db.query(SolarInstallation).filter(SolarInstallation.id == installation_id).first()
    if not installation:
        raise NotFoundException(
            message=f"Solar installation with ID {installation_id} does not exist",
            context={"installation_id": installation_id}
        )

    verify_jurisdiction_read_access(installation, client, db)

    reading = db.query(GenerationReading).filter(
        GenerationReading.id == reading_id,
        GenerationReading.installation_id == installation_id
    ).first()

    if not reading:
        raise NotFoundException(
            message=f"Generation reading with ID {reading_id} does not exist for installation {installation_id}",
            context={"installation_id": installation_id, "reading_id": reading_id}
        )

    data = GenerationReadingResponse.model_validate(reading).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return reading
