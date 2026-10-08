from app.database import SessionLocal
from app.models.province import Province
from app.models.district import District
from app.models.grid_substation import GridSubstation
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.models.user import User


def test_seed_database_counts():
    """Verify that seeded database strictly fulfills all minimum count requirements."""
    db = SessionLocal()
    try:
        province_count = db.query(Province).count()
        district_count = db.query(District).count()
        substation_count = db.query(GridSubstation).count()
        installation_count = db.query(SolarInstallation).count()
        reading_count = db.query(GenerationReading).count()
        user_count = db.query(User).count()

        assert province_count == 9, f"Expected 9 provinces, got {province_count}"
        assert district_count == 25, f"Expected 25 districts, got {district_count}"
        assert substation_count >= 20, f"Expected >= 20 substations, got {substation_count}"
        assert installation_count >= 200, f"Expected >= 200 installations, got {installation_count}"
        assert reading_count >= (200 * 96 * 7), f"Expected >= 134400 readings, got {reading_count}"
        assert user_count >= 5, f"Expected >= 5 users, got {user_count}"
    finally:
        db.close()
