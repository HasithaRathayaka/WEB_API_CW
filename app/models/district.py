from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    province_id = Column(Integer, ForeignKey("provinces.id"), nullable=False, index=True)

    province = relationship("Province", back_populates="districts")
    grid_substations = relationship("GridSubstation", back_populates="district", cascade="all, delete-orphan")
    solar_installations = relationship("SolarInstallation", back_populates="district")
