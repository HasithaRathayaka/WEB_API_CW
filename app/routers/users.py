from typing import List
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.dependencies import require_any_scope, AuthenticatedEntity
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, ConflictException
from app.core.etag import generate_etag, verify_etag_and_respond

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List all users"
)
def list_users(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """List all registered users. Admin scope required. Supports ETag conditional caching."""
    users = db.query(User).order_by(User.id.asc()).all()
    data = [UserResponse.model_validate(u).model_dump() for u in users]

    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Retrieve user by ID"
)
def get_user(
    user_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """Retrieve user details. Admin scope required. Supports ETag conditional caching."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(
            message=f"User with ID {user_id} does not exist",
            context={"user_id": user_id}
        )

    data = UserResponse.model_validate(user).model_dump()
    etag = generate_etag(data)
    conditional_resp = verify_etag_and_respond(request, etag, response)
    if conditional_resp:
        return conditional_resp

    return user


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def create_user(
    user_in: UserCreate,
    response: Response,
    db: Session = Depends(get_db),
    client: AuthenticatedEntity = Depends(require_any_scope(["admin"]))
):
    """Register a new SLSEA user or device account. Enforces Location header on 201 Created."""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise ConflictException(
            message=f"User with username '{user_in.username}' already exists",
            context={"username": user_in.username}
        )

    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        jurisdiction_type=user_in.jurisdiction_type,
        jurisdiction_id=user_in.jurisdiction_id,
        scopes=user_in.scopes,
        is_active=user_in.is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response.headers["Location"] = f"/api/v1/users/{user.id}"
    return user
