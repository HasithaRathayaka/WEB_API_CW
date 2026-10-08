# SLSEA Real-Time Solar Generation Data API

Production-ready, highly compliant RESTful API engineered for the **Sri Lanka Sustainable Energy Authority (SLSEA)** to monitor and analyze real-time grid-tied solar photovoltaic generation nationwide.

Built with **Python 3**, **FastAPI**, **PostgreSQL** (with SQLite fallback for local developer agility), and **SQLAlchemy 2.0**.

---

## 📋 Architectural Conformance & Specification Compliance

| Requirement | Implementation Detail | Spec Conformance |
| :--- | :--- | :--- |
| **Tech Stack** | Python 3, FastAPI, PostgreSQL/SQLite, SQLAlchemy 2.0, Pydantic v2 | Fully Compliant |
| **Core Entities** | Strict models for `Province`, `District`, `GridSubstation`, `SolarInstallation`, `GenerationReading`, `User` | Fully Compliant |
| **Strict Rule 1** | Meter/inverter identifier is strictly an attribute of `SolarInstallation` (`meter_id`). **No separate `Device` entity.** | Fully Compliant |
| **Strict Rule 2** | `GenerationReading` is strictly an append-only time series. **No last-value fields on `SolarInstallation`.** | Fully Compliant |
| **Richardson Maturity Model** | Level 2: Proper HTTP verbs (GET, POST), standard status codes (200, 201, 304, 401, 403, 404, 422), and resource URIs. | Level 2 Compliant |
| **URI Naming Standards** | Strictly lowercase, hyphenated, pluralised nouns (`/solar-installations`, `/district-generation-summaries`). **Zero verbs.** | Fully Compliant |
| **HTTP Headers** | Enforces `Location` header on `201 Created` responses; supports `ETag` and conditional GETs returning `304 Not Modified`. | Fully Compliant |
| **Unified Error Schema** | Uniform JSON schema across all 4xx/5xx responses: `{"code": ..., "message": ..., "context": ...}`. | Fully Compliant |
| **Write Path** | Device ingestion endpoint `POST /solar-installations/{id}/readings` returning `201 Created` with `Location` header. | Fully Compliant |
| **Operational Read Path** | Composite installation resource `GET /solar-installations/{id}` and derived `GET /solar-installations/{id}/last-known-reading`. | Fully Compliant |
| **Analytical Read Path** | Scoped readings sub-collection `GET /solar-installations/{id}/readings` with pagination (`count`, `next`/`prev` links), timestamp sorting, and time window filters. | Fully Compliant |
| **Stretch Goal** | District generation summary `GET /district-generation-summaries/{district_id}` aggregating total power and cumulative energy across all installations. | Fully Compliant |
| **Security & Auth** | JWT Bearer authentication enforcing scopes (`installation-write`, `analyst-read-district`, `analyst-read-province`, `analyst-read-national`) preventing cross-jurisdiction leakage. | Fully Compliant |
| **Seed Dataset** | High-performance bulk seeder generating **9 provinces**, **25 districts**, **27 substations**, **200 installations**, and **134,400 readings** (1 full week at 15-min intervals). | Fully Compliant |

---

## 🗄️ Core Data Models

```
Province (1) ───────────< (Many) District (1) ───────────< (Many) GridSubstation (1)
                                   │                                    │
                                   │ (1)                                │ (1)
                                   ▼                                    ▼
                          SolarInstallation (meter_id, capacity_kw, status)
                                   │ (1)
                                   ▼
                       GenerationReading [Append-Only Time Series]
                          - timestamp (15-min interval)
                          - power_kw (instantaneous kW)
                          - energy_kwh (cumulative kWh)
                          - voltage (V)
```

> **Strict Rule 1 Note:** The inverter/meter identifier is strictly embedded on [`SolarInstallation.meter_id`](file:///d:/Study%20Material/NIBM%20Lecture%20Notes/Degree/web%20API/WEB_API_CW/app/models/solar_installation.py). No separate `Device` entity exists.
>
> **Strict Rule 2 Note:** [`SolarInstallation`](file:///d:/Study%20Material/NIBM%20Lecture%20Notes/Degree/web%20API/WEB_API_CW/app/models/solar_installation.py) contains zero last-value fields. All current metrics are derived dynamically from the [`GenerationReading`](file:///d:/Study%20Material/NIBM%20Lecture%20Notes/Degree/web%20API/WEB_API_CW/app/models/generation_reading.py) time series.

---

## 🔐 Security, Scopes & Jurisdiction Isolation

Authentication is handled via JWT Bearer tokens issuing specific cryptographic scopes:

1. **Write Clients (Solar Devices):**
   - Scope: `installation-write`
   - Bound strictly to their `installation_id`.
   - A device token for Installation 1 attempting to post readings to Installation 2 is immediately rejected with `403 Forbidden`.
2. **Read Clients (SLSEA Analysts & Officials):**
   - **National Analyst:** `analyst-read-national` (Full visibility across all Sri Lankan provinces and districts).
   - **Province Analyst:** `analyst-read-province` (Restricted strictly to installations in their assigned province).
   - **District Analyst:** `analyst-read-district` (Restricted strictly to installations in their assigned district).
   - Any cross-jurisdiction attempt returns `403 Forbidden` with detailed error context.

---

## 🚀 Quickstart Guide

### 1. Environment Setup

Ensure Python 3.10+ is installed:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configuration (`.env`)

Copy `.env.example` to `.env`:
```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/slsea_solar_db
# For zero-setup local SQLite testing:
# DATABASE_URL=sqlite:///./slsea_solar.db
SECRET_KEY=slsea_solar_super_secret_jwt_key_change_in_production_2026!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
API_V1_PREFIX=/api/v1
```

### 3. Run the Database Seed Script

Seeds 9 provinces, 25 districts, 27 substations, 200 solar installations, and 134,400 generation readings (1 full week at 15-minute intervals):
```powershell
python scripts/seed.py --days 7 --installations 200
```

### 4. Start the API Server

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc)

### 5. Run the Automated Test Suite

```powershell
python -m pytest -v
```

All 29 tests execute across authentication, operational composite read, derived last-known-reading, time series ingestion, pagination, sorting, time window filtering, ETag 304 conditional caching, and cross-jurisdiction leakage prevention.

---

## 📡 API Reference & Key Endpoints

All resource URIs follow strict lowercase, hyphenated, pluralized nouns with zero verbs:

### 1. Authentication & Tokens
- `POST /api/v1/tokens`: Authenticate SLSEA user (Returns JWT with scopes & jurisdiction).
  - Pre-seeded users:
    - Admin: `admin` / `adminpassword123`
    - National Analyst: `slsea_national_analyst` / `analystpassword123`
    - Western Province Analyst: `western_province_analyst` / `provincepassword123`
    - Colombo District Analyst: `colombo_district_analyst` / `districtpassword123`
    - Kandy District Analyst: `kandy_district_analyst` / `districtpassword123`
- `POST /api/v1/tokens/devices`: Authenticate solar meter/inverter device.
  - Body: `{"meter_id": "MTR-LK-COL-0001", "installation_id": 1}`

### 2. Solar Installations (Operational Read Path)
- `GET /api/v1/solar-installations`: List installations (scoped by caller's jurisdiction). Supports `ETag` + `304 Not Modified`.
- `GET /api/v1/solar-installations/{id}`: Composite operational resource combining installation details, district, province, grid substation, and dynamically derived operational metrics. Supports `ETag`.
- `GET /api/v1/solar-installations/{id}/last-known-reading`: Derived last-known-reading resource per installation (dynamically computed from append-only series). Supports `ETag`.
- `POST /api/v1/solar-installations`: Register installation. Returns `201 Created` with `Location: /api/v1/solar-installations/{id}`.

### 3. Generation Readings (Write Ingestion & Analytical Read Path)
- `POST /api/v1/solar-installations/{id}/readings`: Device ingestion endpoint. Returns `201 Created` with `Location: /api/v1/solar-installations/{id}/readings/{reading_id}`.
- `GET /api/v1/solar-installations/{id}/readings`: Analytical sub-collection featuring:
  - `page`: Page index (default: `1`)
  - `page_size`: Page limit (default: `50`)
  - `sort`: Sort direction by timestamp (`desc` or `asc`)
  - `start_time` & `end_time`: ISO 8601 time window filters
  - Hypermedia envelope with `count`, `total_count`, `next`, `prev`, and `results`.
  - Conditional GET via `ETag` / `If-None-Match`.

### 4. District Generation Summaries (Stretch Goal)
- `GET /api/v1/district-generation-summaries/{district_id}`: Computes aggregate installed capacity, active installation count, total current instantaneous power (kW), and cumulative energy (kWh).
- `GET /api/v1/districts/{district_id}/generation-summaries`: Canonical nested REST alias.

### 5. Geographic & Administrative Hierarchy
- `GET /api/v1/provinces`: List all 9 provinces.
- `GET /api/v1/districts`: List districts with optional `?province_id=` filter.
- `GET /api/v1/grid-substations`: List grid substations with optional `?district_id=` filter.

---

## 🛡️ Unified Error Schema

All exceptions and validation errors uniformly return:
```json
{
  "code": "FORBIDDEN",
  "message": "Access denied: Solar installation belongs outside your assigned district jurisdiction",
  "context": {
    "user_district_id": 1,
    "installation_district_id": 4
  }
}
```
Standard error codes: `RESOURCE_NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`, `RESOURCE_CONFLICT`, `VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`.
