from datetime import datetime, timezone
from fastapi import status


def test_device_cannot_write_to_foreign_installation(client, device_1_headers):
    """Write Clients (Devices): Devices authenticate exclusively as their own installation to append their own generation readings."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "power_kw": 50.0,
        "energy_kwh": 300.0,
        "voltage": 230.0
    }
    # Device 1 token trying to write to installation 2
    response = client.post("/api/v1/solar-installations/2/readings", json=payload, headers=device_1_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()
    assert error["code"] == "FORBIDDEN"
    assert "context" in error
    assert error["context"]["client_installation_id"] == 1
    assert error["context"]["target_installation_id"] == 2


def test_cross_jurisdiction_leakage_prevented_for_district_analyst(client, colombo_analyst_headers):
    """Read Clients (SLSEA Users): SLSEA users authenticate with read permissions restricted strictly to their assigned jurisdiction."""
    # Colombo analyst trying to access Kandy installation (ID: 3)
    response = client.get("/api/v1/solar-installations/3", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()
    assert error["code"] == "FORBIDDEN"
    assert "jurisdiction" in error["message"].lower() or "denied" in error["message"].lower()


def test_cross_jurisdiction_readings_leakage_prevented(client, colombo_analyst_headers):
    """District analyst cannot read readings sub-collection of another district."""
    response = client.get("/api/v1/solar-installations/3/readings", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()
    assert error["code"] == "FORBIDDEN"


def test_cross_jurisdiction_district_summary_leakage_prevented(client, colombo_analyst_headers):
    """District analyst cannot read district summary of another district."""
    # Kandy district ID is 3
    response = client.get("/api/v1/district-generation-summaries/3", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()
    assert error["code"] == "FORBIDDEN"


def test_national_analyst_can_access_any_jurisdiction(client, national_analyst_headers):
    """National analyst scope allows reading installations across all districts."""
    res_colombo = client.get("/api/v1/solar-installations/1", headers=national_analyst_headers)
    assert res_colombo.status_code == status.HTTP_200_OK

    res_kandy = client.get("/api/v1/solar-installations/3", headers=national_analyst_headers)
    assert res_kandy.status_code == status.HTTP_200_OK


def test_missing_authentication_returns_401_with_error_schema(client):
    """Unauthenticated requests are rejected with 401 and standard error schema."""
    response = client.get("/api/v1/solar-installations/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert error["code"] == "UNAUTHORIZED"
    assert "message" in error
    assert "context" in error
