from fastapi import status


def test_404_error_schema_conformance(client, national_analyst_headers):
    """Verify 404 Not Found returns consistent JSON error schema: code, message, context."""
    response = client.get("/api/v1/solar-installations/99999", headers=national_analyst_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()
    assert "code" in error
    assert "message" in error
    assert "context" in error
    assert error["code"] == "RESOURCE_NOT_FOUND"


def test_401_error_schema_conformance(client):
    """Verify 401 Unauthorized returns consistent JSON error schema: code, message, context."""
    response = client.get("/api/v1/provinces")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert "code" in error
    assert "message" in error
    assert "context" in error
    assert error["code"] == "UNAUTHORIZED"


def test_422_validation_error_schema_conformance(client, admin_headers):
    """Verify 422 Unprocessable Entity returns consistent JSON error schema: code, message, context."""
    # Missing required fields like name, meter_id, capacity_kw
    response = client.post("/api/v1/solar-installations", json={"invalid_field": "test"}, headers=admin_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()
    assert error["code"] == "VALIDATION_ERROR"
    assert "message" in error
    assert "context" in error
    assert "validation_errors" in error["context"]


def test_403_forbidden_error_schema_conformance(client, colombo_analyst_headers):
    """Verify 403 Forbidden returns consistent JSON error schema: code, message, context."""
    response = client.get("/api/v1/solar-installations/3", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error = response.json()
    assert error["code"] == "FORBIDDEN"
    assert "message" in error
    assert "context" in error
