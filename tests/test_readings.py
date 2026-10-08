from datetime import datetime, timezone, timedelta
from fastapi import status


def test_write_path_ingestion_201_and_location_header(client, device_1_headers):
    """Write Path: Create an ingestion endpoint for devices to POST new readings, returning a 201 status code and Location header."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "timestamp": now_iso,
        "power_kw": 88.5,
        "energy_kwh": 1250.0,
        "voltage": 231.4
    }
    response = client.post("/api/v1/solar-installations/1/readings", json=payload, headers=device_1_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["installation_id"] == 1
    assert data["power_kw"] == 88.5
    assert "Location" in response.headers
    assert response.headers["Location"] == f"/api/v1/solar-installations/1/readings/{data['id']}"


def test_analytical_read_path_pagination_and_links(client, national_analyst_headers):
    """Read Path (Analytical): Scoped readings sub-collection featuring pagination (count, next/prev links)."""
    response = client.get(
        "/api/v1/solar-installations/1/readings?page=1&page_size=3",
        headers=national_analyst_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 3
    assert data["total_count"] >= 8
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert data["next"] is not None
    assert "page=2" in data["next"]
    assert data["prev"] is None
    assert len(data["results"]) == 3


def test_analytical_read_path_sorting(client, national_analyst_headers):
    """Read Path (Analytical): sorting by timestamp."""
    # Descending sort
    res_desc = client.get("/api/v1/solar-installations/1/readings?sort=desc", headers=national_analyst_headers)
    assert res_desc.status_code == status.HTTP_200_OK
    readings_desc = res_desc.json()["results"]
    assert len(readings_desc) >= 2
    assert readings_desc[0]["timestamp"] >= readings_desc[1]["timestamp"]

    # Ascending sort
    res_asc = client.get("/api/v1/solar-installations/1/readings?sort=asc", headers=national_analyst_headers)
    assert res_asc.status_code == status.HTTP_200_OK
    readings_asc = res_asc.json()["results"]
    assert len(readings_asc) >= 2
    assert readings_asc[0]["timestamp"] <= readings_asc[1]["timestamp"]


def test_analytical_read_path_time_window_filtering(client, national_analyst_headers):
    """Read Path (Analytical): filtering by time window."""
    now = datetime.now(timezone.utc)
    t_start = (now - timedelta(hours=1, minutes=30)).isoformat()
    t_end = now.isoformat()

    response = client.get(
        "/api/v1/solar-installations/1/readings",
        params={"start_time": t_start, "end_time": t_end},
        headers=national_analyst_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    for item in data["results"]:
        # Verify item timestamp is within range
        item_time = datetime.fromisoformat(item["timestamp"])
        if item_time.tzinfo is None:
            item_time = item_time.replace(tzinfo=timezone.utc)
        start_dt = datetime.fromisoformat(t_start)
        end_dt = datetime.fromisoformat(t_end)
        assert item_time >= start_dt
        assert item_time <= end_dt


def test_analytical_readings_etag_and_304(client, national_analyst_headers):
    """ETag and conditional GET on analytical readings collection."""
    res1 = client.get("/api/v1/solar-installations/1/readings", headers=national_analyst_headers)
    assert res1.status_code == status.HTTP_200_OK
    etag = res1.headers.get("ETag")
    assert etag is not None

    headers = {**national_analyst_headers, "If-None-Match": etag}
    res2 = client.get("/api/v1/solar-installations/1/readings", headers=headers)
    assert res2.status_code == status.HTTP_304_NOT_MODIFIED
    assert res2.text == ""
