import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
from app.main import app
from app.models.province import Province
from app.models.district import District
from app.models.grid_substation import GridSubstation
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.models.user import User
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///./test_slsea.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        # Seed test provinces
        wp = Province(name="Western Province", code="WP")
        cp = Province(name="Central Province", code="CP")
        db.add_all([wp, cp])
        db.commit()

        # Seed test districts
        colombo = District(name="Colombo", code="COL", province_id=wp.id)
        gampaha = District(name="Gampaha", code="GAM", province_id=wp.id)
        kandy = District(name="Kandy", code="KAN", province_id=cp.id)
        db.add_all([colombo, gampaha, kandy])
        db.commit()

        # Seed test substations
        sub_col = GridSubstation(name="Kolonnawa Substation", code="GS-COL-01", district_id=colombo.id, capacity_mva=90.0, voltage_level_kv=132.0)
        sub_kan = GridSubstation(name="Kiribathkumbura Substation", code="GS-KAN-01", district_id=kandy.id, capacity_mva=63.0, voltage_level_kv=132.0)
        db.add_all([sub_col, sub_kan])
        db.commit()

        # Seed test installations (Strict Rule 1: meter_id on installation, no Device entity)
        inst_1 = SolarInstallation(
            name="Colombo Rooftop Array 1",
            meter_id="MTR-COL-001",
            inverter_serial="INV-001",
            capacity_kw=100.0,
            installation_type="rooftop",
            status="active",
            district_id=colombo.id,
            grid_substation_id=sub_col.id
        )
        inst_2 = SolarInstallation(
            name="Colombo Rooftop Array 2",
            meter_id="MTR-COL-002",
            inverter_serial="INV-002",
            capacity_kw=50.0,
            installation_type="rooftop",
            status="active",
            district_id=colombo.id,
            grid_substation_id=sub_col.id
        )
        inst_kandy = SolarInstallation(
            name="Kandy Solar Farm",
            meter_id="MTR-KAN-001",
            inverter_serial="INV-KAN-01",
            capacity_kw=200.0,
            installation_type="ground-mounted",
            status="active",
            district_id=kandy.id,
            grid_substation_id=sub_kan.id
        )
        db.add_all([inst_1, inst_2, inst_kandy])
        db.commit()

        # Seed test users
        admin_user = User(
            username="admin_test",
            hashed_password=hash_password("adminpass"),
            role="admin",
            jurisdiction_type="national",
            jurisdiction_id=None,
            scopes="admin analyst-read-national analyst-read-province analyst-read-district installation-write"
        )
        colombo_analyst = User(
            username="colombo_analyst_test",
            hashed_password=hash_password("userpass"),
            role="analyst",
            jurisdiction_type="district",
            jurisdiction_id=colombo.id,
            scopes="analyst-read-district"
        )
        kandy_analyst = User(
            username="kandy_analyst_test",
            hashed_password=hash_password("userpass"),
            role="analyst",
            jurisdiction_type="district",
            jurisdiction_id=kandy.id,
            scopes="analyst-read-district"
        )
        national_analyst = User(
            username="national_analyst_test",
            hashed_password=hash_password("userpass"),
            role="analyst",
            jurisdiction_type="national",
            jurisdiction_id=None,
            scopes="analyst-read-national"
        )
        db.add_all([admin_user, colombo_analyst, kandy_analyst, national_analyst])
        db.commit()

        # Seed some initial append-only readings for inst_1 (Strict Rule 2)
        base_time = datetime.now(timezone.utc) - timedelta(hours=2)
        readings = [
            GenerationReading(
                installation_id=inst_1.id,
                timestamp=base_time + timedelta(minutes=15 * i),
                power_kw=45.0 + i * 2.0,
                energy_kwh=100.0 + i * 11.5,
                voltage=230.0 + (i % 3)
            )
            for i in range(8)
        ]
        db.add_all(readings)
        db.commit()

    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    try:
        if os.path.exists("./test_slsea.db"):
            os.remove("./test_slsea.db")
    except Exception:
        pass


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    token = create_access_token(
        subject="admin_test",
        scopes=["admin", "analyst-read-national", "analyst-read-district", "installation-write"],
        role="admin",
        jurisdiction_type="national",
        jurisdiction_id=None
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def national_analyst_headers():
    token = create_access_token(
        subject="national_analyst_test",
        scopes=["analyst-read-national"],
        role="analyst",
        jurisdiction_type="national",
        jurisdiction_id=None
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def colombo_analyst_headers():
    token = create_access_token(
        subject="colombo_analyst_test",
        scopes=["analyst-read-district"],
        role="analyst",
        jurisdiction_type="district",
        jurisdiction_id=1  # Colombo
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def kandy_analyst_headers():
    token = create_access_token(
        subject="kandy_analyst_test",
        scopes=["analyst-read-district"],
        role="analyst",
        jurisdiction_type="district",
        jurisdiction_id=3  # Kandy
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def device_1_headers():
    token = create_access_token(
        subject="device:MTR-COL-001",
        scopes=["installation-write"],
        role="device",
        jurisdiction_type="installation",
        jurisdiction_id=1  # Installation 1
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def device_2_headers():
    token = create_access_token(
        subject="device:MTR-COL-002",
        scopes=["installation-write"],
        role="device",
        jurisdiction_type="installation",
        jurisdiction_id=2  # Installation 2
    )
    return {"Authorization": f"Bearer {token}"}
