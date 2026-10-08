# SLSEA Real-Time Solar Generation Data API - Project Specification

## Architecture & Data Model
*   **Tech Stack:** Python 3, FastAPI, PostgreSQL, and SQLAlchemy.
*   **Core Entities:** Generate data models strictly for `Province`, `District`, `GridSubstation`, `SolarInstallation`, `GenerationReading`, and `User`[cite: 4].
*   **Strict Rule 1:** The meter or inverter identifier must be built as an attribute of `SolarInstallation` (e.g., `meter_id`); do not create a separate `Device` entity[cite: 4].
*   **Strict Rule 2:** `GenerationReading` must be an append-only time series containing the owning installation, timestamp, instantaneous power (kW), cumulative energy (kWh), and voltage[cite: 4]. Do not use last-value fields on the installation for this[cite: 4].
*   **Seed Script:** Write a robust database seed script generating 9 provinces, 25 districts, >=20 substations, >=200 installations, and >=1 week of 15-minute interval readings per installation[cite: 5].

## REST API Design Rules
*   **Maturity:** Target Richardson Maturity Model Level 2[cite: 3].
*   **Naming Standards:** Use lowercase, hyphenated, pluralised nouns for all URIs (e.g., `/solar-installations`)[cite: 11]. Avoid verbs completely[cite: 11].
*   **HTTP & Headers:** Enforce `Location` headers on `201 Created` responses[cite: 11]. Support `ETag` headers and conditional GETs returning `304 Not Modified` for retrievable resources[cite: 6, 12].
*   **Error Handling:** Implement one consistent JSON error schema containing a code, message, and detailed context across the entire API[cite: 6].

## Core & Advanced Endpoints
*   **Write Path:** Create an ingestion endpoint for devices to POST new readings, returning a 201 status code[cite: 5].
*   **Read Path (Operational):** Build a composite resource for an installation and a derived "last-known-reading" resource per installation[cite: 5].
*   **Read Path (Analytical):** Construct a scoped readings sub-collection (`/solar-installations/{id}/readings`) featuring pagination (count, next/prev links), sorting by timestamp, and filtering by jurisdiction and time window[cite: 5, 12].
*   **Stretch Goal:** Implement a district generation summary resource computing total power and energy across all installations within a district[cite: 6].

## Security & Authentication
*   **Write Clients (Devices):** Devices authenticate exclusively as their own installation to append their own generation readings[cite: 4].
*   **Read Clients (SLSEA Users):** SLSEA users authenticate with read permissions restricted strictly to their assigned jurisdiction[cite: 4].
*   **Implementation:** Use JWT bearer authentication enforcing distinct scopes like `installation-write` and `analyst-read-district` to prevent cross-jurisdiction leakage[cite: 14].