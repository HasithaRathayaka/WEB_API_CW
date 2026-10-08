from fastapi import status


def test_district_generation_summary_stretch_goal(client, colombo_analyst_headers):
    """
    Stretch Goal: Implement a district generation summary resource computing total power
    and energy across all installations within a district.
    """
    # Colombo district ID: 1
    response = client.get("/api/v1/district-generation-summaries/1", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["district_id"] == 1
    assert data["district_name"] == "Colombo"
    assert data["total_installations_count"] >= 2
    assert data["active_installations_count"] >= 2
    assert data["total_installed_capacity_kw"] >= 150.0
    assert data["current_aggregate_power_kw"] >= 0.0
    assert data["total_cumulative_energy_kwh"] >= 0.0
    assert "average_voltage" in data
    assert "timestamp" in data


def test_district_generation_summary_alias(client, colombo_analyst_headers):
    """Test alias endpoint /districts/{id}/generation-summaries."""
    response = client.get("/api/v1/districts/1/generation-summaries", headers=colombo_analyst_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["district_id"] == 1


def test_district_summary_etag_and_304(client, colombo_analyst_headers):
    """District generation summary supports ETag and conditional GET."""
    res1 = client.get("/api/v1/district-generation-summaries/1", headers=colombo_analyst_headers)
    assert res1.status_code == status.HTTP_200_OK
    etag = res1.headers.get("ETag")
    assert etag is not None

    headers = {**colombo_analyst_headers, "If-None-Match": etag}
    res2 = client.get("/api/v1/district-generation-summaries/1", headers=headers)
    assert res2.status_code == status.HTTP_304_NOT_MODIFIED
    assert res2.text == ""
