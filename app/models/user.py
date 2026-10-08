from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="analyst")  # admin, analyst, device
    
    # Jurisdiction scoping for RBAC / security
    # Types: "national", "province", "district", "installation"
    jurisdiction_type = Column(String(50), nullable=False, default="national")
    jurisdiction_id = Column(Integer, nullable=True)  # district_id, province_id, or installation_id
    
    # Space-delimited scopes, e.g. "installation-write", "analyst-read-district", "analyst-read-national"
    scopes = Column(String(255), nullable=False, default="analyst-read-national")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
