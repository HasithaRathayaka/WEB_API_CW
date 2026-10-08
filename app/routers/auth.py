from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.solar_installation import SolarInstallation
from app.schemas.token import Token, UserLoginRequest, DeviceTokenRequest
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedException, NotFoundException

router = APIRouter(prefix="/tokens", tags=["Tokens & Authentication"])


@router.post(
    "",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Issue JWT access token for SLSEA users"
)
def login_user(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate an SLSEA user (analyst or administrator) and issue a scoped JWT token.
    Token contains user scopes, jurisdiction type, and jurisdiction ID to prevent
    cross-jurisdiction leakage.
    """
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise UnauthorizedException(
            message="Invalid username or password",
            context={"username": login_data.username}
        )

    if not user.is_active:
        raise UnauthorizedException(
            message="User account is deactivated",
            context={"username": login_data.username}
        )

    user_scopes = [s.strip() for s in user.scopes.split(" ") if s.strip()]

    token = create_access_token(
        subject=user.username,
        scopes=user_scopes,
        role=user.role,
        jurisdiction_type=user.jurisdiction_type,
        jurisdiction_id=user.jurisdiction_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scopes=user_scopes,
        role=user.role,
        jurisdiction_type=user.jurisdiction_type,
        jurisdiction_id=user.jurisdiction_id
    )


@router.post(
    "/devices",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Issue JWT access token for solar installation devices"
)
def authenticate_device(device_data: DeviceTokenRequest, db: Session = Depends(get_db)):
    """
    Authenticate a solar device/meter and issue an installation-write scoped JWT.
    Enforces strict binding between the device's meter_id and target installation ID.
    """
    installation = db.query(SolarInstallation).filter(
        SolarInstallation.id == device_data.installation_id,
        SolarInstallation.meter_id == device_data.meter_id
    ).first()

    if not installation:
        raise UnauthorizedException(
            message="Authentication failed: Installation ID and meter ID do not match registered records",
            context={
                "meter_id": device_data.meter_id,
                "installation_id": device_data.installation_id
            }
        )

    scopes = ["installation-write"]
    token = create_access_token(
        subject=f"device:{device_data.meter_id}",
        scopes=scopes,
        role="device",
        jurisdiction_type="installation",
        jurisdiction_id=installation.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scopes=scopes,
        role="device",
        jurisdiction_type="installation",
        jurisdiction_id=installation.id
    )
