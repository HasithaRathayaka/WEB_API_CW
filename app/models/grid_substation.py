from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class GridSubstation(Base):
    __tablename__ = "grid_substations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    capacity_mva = Column(Float, nullable=True)
    voltage_level_kv = Column(Float, nullable=True)

    district = relationship("District", back_populates="grid_substations")
    solar_installations = relationship("SolarInstallation", back_populates="grid_substation")
