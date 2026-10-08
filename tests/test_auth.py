from fastapi import status


def test_user_login_success(client):
    response = client.post(
        "/api/v1/tokens",
        json={"username": "colombo_analyst_test", "password": "userpass"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "analyst-read-district" in data["scopes"]
    assert data["jurisdiction_type"] == "district"
    assert data["jurisdiction_id"] == 1


def test_user_login_invalid_password(client):
    response = client.post(
        "/api/v1/tokens",
        json={"username": "colombo_analyst_test", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert error["code"] == "UNAUTHORIZED"
    assert "message" in error
    assert "context" in error


def test_device_authentication_success(client):
    response = client.post(
        "/api/v1/tokens/devices",
        json={"meter_id": "MTR-COL-001", "installation_id": 1}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "installation-write" in data["scopes"]
    assert data["jurisdiction_type"] == "installation"
    assert data["jurisdiction_id"] == 1


def test_device_authentication_mismatch_fails(client):
    # meter MTR-COL-001 does not match installation 2
    response = client.post(
        "/api/v1/tokens/devices",
        json={"meter_id": "MTR-COL-001", "installation_id": 2}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert error["code"] == "UNAUTHORIZED"
    assert "context" in error
