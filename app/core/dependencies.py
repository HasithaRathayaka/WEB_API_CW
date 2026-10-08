from typing import List, Optional
from fastapi import Depends, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException
from app.core.security import decode_access_token
from app.models.solar_installation import SolarInstallation
from app.models.district import District

security_bearer = HTTPBearer(auto_error=False)


class AuthenticatedEntity:
    """Represents an authenticated user or device client extracted from JWT claims."""
    def __init__(
        self,
        identifier: str,
        scopes: List[str],
        role: str,
        jurisdiction_type: str,
        jurisdiction_id: Optional[int] = None
    ):
        self.identifier = identifier
        self.scopes = scopes
        self.role = role
        self.jurisdiction_type = jurisdiction_type
        self.jurisdiction_id = jurisdiction_id

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes


def get_current_client(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> AuthenticatedEntity:
    """
    Validate JWT Bearer token and extract the authenticated entity.
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(
            message="Missing authentication credentials in Authorization header",
            context={"scheme": "Bearer"}
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException(
            message="Authentication token has expired",
            context={"error": "token_expired"}
        )
    except jwt.InvalidTokenError as e:
        raise UnauthorizedException(
            message="Invalid authentication token",
            context={"error": str(e)}
        )

    identifier: str = payload.get("sub")
    scopes: List[str] = payload.get("scopes", [])
    role: str = payload.get("role", "analyst")
    jurisdiction_type: str = payload.get("jurisdiction_type", "national")
    jurisdiction_id: Optional[int] = payload.get("jurisdiction_id")

    if not identifier:
        raise UnauthorizedException(
            message="Token payload is missing subject identifier",
            context={"payload": payload}
        )

    return AuthenticatedEntity(
        identifier=identifier,
        scopes=scopes,
        role=role,
        jurisdiction_type=jurisdiction_type,
        jurisdiction_id=jurisdiction_id
    )


def require_any_scope(allowed_scopes: List[str]):
    """
    Dependency factory ensuring the client has at least one of the required scopes.
    """
    def scope_checker(
        current_client: AuthenticatedEntity = Depends(get_current_client)
    ) -> AuthenticatedEntity:
        # Admin bypass
        if current_client.role == "admin":
            return current_client
            
        for scope in allowed_scopes:
            if current_client.has_scope(scope):
                return current_client

        raise ForbiddenException(
            message="Insufficient permissions for this resource",
            context={
                "required_scopes": allowed_scopes,
                "current_scopes": current_client.scopes
            }
        )
    return scope_checker


def require_installation_write(
    current_client: AuthenticatedEntity = Depends(require_any_scope(["installation-write"]))
) -> AuthenticatedEntity:
    """Dependency specifically requiring installation-write scope."""
    return current_client


def require_analyst_read(
    current_client: AuthenticatedEntity = Depends(
        require_any_scope([
            "analyst-read-national",
            "analyst-read-province",
            "analyst-read-district"
        ])
    )
) -> AuthenticatedEntity:
    """Dependency requiring one of the read analyst scopes."""
    return current_client


def verify_installation_write_access(
    installation_id: int,
    client: AuthenticatedEntity
) -> None:
    """
    Write Clients (Devices): Devices authenticate exclusively as their own
    installation to append their own generation readings.
    """
    if client.role == "admin":
        return

    if client.jurisdiction_type == "installation":
        if client.jurisdiction_id != installation_id:
            raise ForbiddenException(
                message="Device is forbidden from appending readings to a foreign installation",
                context={
                    "client_installation_id": client.jurisdiction_id,
                    "target_installation_id": installation_id
                }
            )


def verify_jurisdiction_read_access(
    installation: SolarInstallation,
    client: AuthenticatedEntity,
    db: Session
) -> None:
    """
    Read Clients (SLSEA Users): Users authenticate with read permissions restricted
    strictly to their assigned jurisdiction (district, province, or national).
    Prevents cross-jurisdiction leakage.
    """
    if client.role == "admin":
        return

    # If device is reading its own installation
    if client.jurisdiction_type == "installation":
        if client.jurisdiction_id == installation.id:
            return
        raise ForbiddenException(
            message="Device is forbidden from reading foreign installation data",
            context={"target_installation_id": installation.id}
        )

    # National scope has read access across all jurisdictions
    if client.has_scope("analyst-read-national") or client.jurisdiction_type == "national":
        return

    # Province-level jurisdiction check
    if client.has_scope("analyst-read-province") or client.jurisdiction_type == "province":
        district = db.query(District).filter(District.id == installation.district_id).first()
        if not district or district.province_id != client.jurisdiction_id:
            raise ForbiddenException(
                message="Access denied: Solar installation belongs outside your assigned province jurisdiction",
                context={
                    "user_province_id": client.jurisdiction_id,
                    "installation_district_id": installation.district_id
                }
            )
        return

    # District-level jurisdiction check
    if client.has_scope("analyst-read-district") or client.jurisdiction_type == "district":
        if installation.district_id != client.jurisdiction_id:
            raise ForbiddenException(
                message="Access denied: Solar installation belongs outside your assigned district jurisdiction",
                context={
                    "user_district_id": client.jurisdiction_id,
                    "installation_district_id": installation.district_id
                }
            )
        return

    raise ForbiddenException(
        message="User lacks valid jurisdiction read permissions",
        context={"jurisdiction_type": client.jurisdiction_type}
    )


def verify_district_read_access(
    district_id: int,
    client: AuthenticatedEntity,
    db: Session
) -> None:
    """
    Verifies that the client has permission to read data for a specific district.
    """
    if client.role == "admin":
        return

    if client.has_scope("analyst-read-national") or client.jurisdiction_type == "national":
        return

    if client.has_scope("analyst-read-district") or client.jurisdiction_type == "district":
        if client.jurisdiction_id != district_id:
            raise ForbiddenException(
                message="Access denied: Requested district is outside your assigned district jurisdiction",
                context={
                    "assigned_district_id": client.jurisdiction_id,
                    "requested_district_id": district_id
                }
            )
        return

    if client.has_scope("analyst-read-province") or client.jurisdiction_type == "province":
        district = db.query(District).filter(District.id == district_id).first()
        if not district:
            raise NotFoundException(
                message="District not found",
                context={"district_id": district_id}
            )
        if district.province_id != client.jurisdiction_id:
            raise ForbiddenException(
                message="Access denied: Requested district is outside your assigned province jurisdiction",
                context={
                    "assigned_province_id": client.jurisdiction_id,
                    "district_province_id": district.province_id
                }
            )
        return

    raise ForbiddenException(
        message="User lacks jurisdiction access for this district",
        context={"jurisdiction_type": client.jurisdiction_type}
    )
