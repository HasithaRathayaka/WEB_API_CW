from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.database import Base


class GenerationReading(Base):
    __tablename__ = "generation_readings"

    # Strict Rule 2: GenerationReading must be an append-only time series containing
    # the owning installation, timestamp, instantaneous power (kW), cumulative energy (kWh), and voltage.
    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("solar_installations.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    power_kw = Column(Float, nullable=False)        # Instantaneous power (kW)
    energy_kwh = Column(Float, nullable=False)      # Cumulative energy (kWh)
    voltage = Column(Float, nullable=False)         # Voltage (V)

    installation = relationship("SolarInstallation", back_populates="readings")

    __table_args__ = (
        Index("idx_reading_inst_time", "installation_id", "timestamp"),
    )
