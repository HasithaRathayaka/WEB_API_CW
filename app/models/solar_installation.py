from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SolarInstallation(Base):
    __tablename__ = "solar_installations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    
    # Strict Rule 1: meter or inverter identifier must be built as an attribute of SolarInstallation;
    # do not create a separate Device entity.
    meter_id = Column(String(100), unique=True, nullable=False, index=True)
    inverter_serial = Column(String(100), nullable=True)

    capacity_kw = Column(Float, nullable=False)
    installation_type = Column(String(50), default="rooftop", nullable=False)  # rooftop, ground-mounted, floating
    status = Column(String(50), default="active", nullable=False)  # active, maintenance, decommissioned

    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    grid_substation_id = Column(Integer, ForeignKey("grid_substations.id"), nullable=False, index=True)
    
    commissioned_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Note: Strict Rule 2 forbids last-value fields on this installation entity!
    # All readings are retrieved dynamically from the append-only GenerationReading time series.

    district = relationship("District", back_populates="solar_installations")
    grid_substation = relationship("GridSubstation", back_populates="solar_installations")
    readings = relationship("GenerationReading", back_populates="installation", cascade="all, delete-orphan", order_by="GenerationReading.timestamp.desc()")
