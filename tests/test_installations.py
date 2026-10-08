from fastapi import status
from app.models.solar_installation import SolarInstallation
import app.models


def test_strict_rule_1_meter_id_attribute_and_no_device_entity():
    """Strict Rule 1: The meter or inverter identifier must be built as an attribute of SolarInstallation; do not create a separate Device entity."""
    # Verify attribute on model
    assert hasattr(SolarInstallation, "meter_id"), "SolarInstallation must contain meter_id attribute"
    
    # Verify no Device model/entity exists in app.models
    assert not hasattr(app.models, "Device"), "No Device entity should exist"
    assert "device" not in [table.name for table in SolarInstallation.metadata.tables.values()], "No device table should exist"


def test_strict_rule_2_no_last_value_fields_on_installation():
    """Strict Rule 2: Do not use last-value fields on the installation for generation readings."""
    forbidden_attributes = [
        "last_power", "last_power_kw", "last_energy", "last_energy_kwh",
        "last_voltage", "last_reading", "last_reading_id", "current_power", "latest_power"
    ]
    for attr in forbidden_attributes:
        assert not hasattr(SolarInstallation, attr), f"SolarInstallation must not store last-value field '{attr}'"


def test_get_solar_installation_composite(client, national_analyst_headers):
    """Read Path (Operational): Build a composite resource for an installation."""
    response = client.get("/api/v1/solar-installations/1", headers=national_analyst_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["meter_id"] == "MTR-COL-001"
    assert "district" in data
    assert data["district"]["name"] == "Colombo"
    assert "grid_substation" in data
    assert "last_known_reading" in data
    assert data["last_known_reading"] is not None
    assert "power_kw" in data["last_known_reading"]


def test_get_derived_last_known_reading(client, national_analyst_headers):
    """Read Path (Operational): Derived 'last-known-reading' resource per installation."""
    response = client.get("/api/v1/solar-installations/1/last-known-reading", headers=national_analyst_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["installation_id"] == 1
    assert "power_kw" in data
    assert "energy_kwh" in data
    assert "voltage" in data
    assert "timestamp" in data


def test_etag_and_conditional_get_304(client, national_analyst_headers):
    """Enforce ETag headers and conditional GETs returning 304 Not Modified."""
    # First GET to obtain ETag
    res1 = client.get("/api/v1/solar-installations/1", headers=national_analyst_headers)
    assert res1.status_code == status.HTTP_200_OK
    etag = res1.headers.get("ETag")
    assert etag is not None

    # Second GET with If-None-Match header matching the ETag
    headers = {**national_analyst_headers, "If-None-Match": etag}
    res2 = client.get("/api/v1/solar-installations/1", headers=headers)
    assert res2.status_code == status.HTTP_304_NOT_MODIFIED
    assert res2.text == ""


def test_create_installation_enforces_location_header(client, admin_headers):
    """Enforce Location headers on 201 Created responses."""
    payload = {
        "name": "New Colombo Commercial Solar",
        "meter_id": "MTR-COL-NEW-999",
        "inverter_serial": "INV-NEW-999",
        "capacity_kw": 75.0,
        "installation_type": "rooftop",
        "status": "active",
        "district_id": 1,
        "grid_substation_id": 1
    }
    response = client.post("/api/v1/solar-installations", json=payload, headers=admin_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "Location" in response.headers
    assert response.headers["Location"] == f"/api/v1/solar-installations/{data['id']}"
