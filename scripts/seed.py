import argparse
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import insert

from app.database import engine, SessionLocal, Base
from app.models.province import Province
from app.models.district import District
from app.models.grid_substation import GridSubstation
from app.models.solar_installation import SolarInstallation
from app.models.generation_reading import GenerationReading
from app.models.user import User
from app.core.security import hash_password

# ==============================================================================
# Master Data for Sri Lanka Provinces & 25 Districts
# ==============================================================================

PROVINCES_DATA = [
    {"name": "Western Province", "code": "WP"},
    {"name": "Central Province", "code": "CP"},
    {"name": "Southern Province", "code": "SP"},
    {"name": "Northern Province", "code": "NP"},
    {"name": "Eastern Province", "code": "EP"},
    {"name": "North Western Province", "code": "NWP"},
    {"name": "North Central Province", "code": "NCP"},
    {"name": "Uva Province", "code": "UP"},
    {"name": "Sabaragamuwa Province", "code": "SGP"},
]

DISTRICTS_DATA = [
    # Western Province
    {"name": "Colombo", "code": "COL", "province_code": "WP"},
    {"name": "Gampaha", "code": "GAM", "province_code": "WP"},
    {"name": "Kalutara", "code": "KAL", "province_code": "WP"},
    # Central Province
    {"name": "Kandy", "code": "KAN", "province_code": "CP"},
    {"name": "Matale", "code": "MTL", "province_code": "CP"},
    {"name": "Nuwara Eliya", "code": "NUE", "province_code": "CP"},
    # Southern Province
    {"name": "Galle", "code": "GAL", "province_code": "SP"},
    {"name": "Matara", "code": "MAT", "province_code": "SP"},
    {"name": "Hambantota", "code": "HAM", "province_code": "SP"},
    # Northern Province
    {"name": "Jaffna", "code": "JAF", "province_code": "NP"},
    {"name": "Kilinochchi", "code": "KIL", "province_code": "NP"},
    {"name": "Mannar", "code": "MAN", "province_code": "NP"},
    {"name": "Vavuniya", "code": "VAV", "province_code": "NP"},
    {"name": "Mullaitivu", "code": "MUL", "province_code": "NP"},
    # Eastern Province
    {"name": "Batticaloa", "code": "BAT", "province_code": "EP"},
    {"name": "Ampara", "code": "AMP", "province_code": "EP"},
    {"name": "Trincomalee", "code": "TRI", "province_code": "EP"},
    # North Western Province
    {"name": "Kurunegala", "code": "KUR", "province_code": "NWP"},
    {"name": "Puttalam", "code": "PUT", "province_code": "NWP"},
    # North Central Province
    {"name": "Anuradhapura", "code": "ANU", "province_code": "NCP"},
    {"name": "Polonnaruwa", "code": "POL", "province_code": "NCP"},
    # Uva Province
    {"name": "Badulla", "code": "BAD", "province_code": "UP"},
    {"name": "Monaragala", "code": "MON", "province_code": "UP"},
    # Sabaragamuwa Province
    {"name": "Ratnapura", "code": "RAT", "province_code": "SGP"},
    {"name": "Kegalle", "code": "KEG", "province_code": "SGP"},
]

SUBSTATIONS_DATA = [
    # Western
    {"name": "Kolonnawa Grid Substation", "code": "GS-COL-01", "district_code": "COL", "capacity_mva": 90.0, "voltage_level_kv": 132.0},
    {"name": "Pannipitiya Grid Substation", "code": "GS-COL-02", "district_code": "COL", "capacity_mva": 120.0, "voltage_level_kv": 220.0},
    {"name": "Kotugoda Grid Substation", "code": "GS-GAM-01", "district_code": "GAM", "capacity_mva": 120.0, "voltage_level_kv": 220.0},
    {"name": "Veyangoda Grid Substation", "code": "GS-GAM-02", "district_code": "GAM", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Horana Grid Substation", "code": "GS-KAL-01", "district_code": "KAL", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    # Central
    {"name": "Kiribathkumbura Grid Substation", "code": "GS-KAN-01", "district_code": "KAN", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Ukuwela Grid Substation", "code": "GS-MTL-01", "district_code": "MTL", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Polpitiya Grid Substation", "code": "GS-NUE-01", "district_code": "NUE", "capacity_mva": 90.0, "voltage_level_kv": 132.0},
    # Southern
    {"name": "Galle Grid Substation", "code": "GS-GAL-01", "district_code": "GAL", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Matara Grid Substation", "code": "GS-MAT-01", "district_code": "MAT", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Hambantota Grid Substation", "code": "GS-HAM-01", "district_code": "HAM", "capacity_mva": 120.0, "voltage_level_kv": 220.0},
    # Northern
    {"name": "Chunnakam Grid Substation", "code": "GS-JAF-01", "district_code": "JAF", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Kilinochchi Grid Substation", "code": "GS-KIL-01", "district_code": "KIL", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Mannar Grid Substation", "code": "GS-MAN-01", "district_code": "MAN", "capacity_mva": 120.0, "voltage_level_kv": 220.0},
    {"name": "Vavuniya Grid Substation", "code": "GS-VAV-01", "district_code": "VAV", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Mullaitivu Grid Substation", "code": "GS-MUL-01", "district_code": "MUL", "capacity_mva": 31.5, "voltage_level_kv": 132.0},
    # Eastern
    {"name": "Valachchenai Grid Substation", "code": "GS-BAT-01", "district_code": "BAT", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Ampara Grid Substation", "code": "GS-AMP-01", "district_code": "AMP", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Trincomalee Grid Substation", "code": "GS-TRI-01", "district_code": "TRI", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    # North Western
    {"name": "Kurunegala Grid Substation", "code": "GS-KUR-01", "district_code": "KUR", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Madampe Grid Substation", "code": "GS-PUT-01", "district_code": "PUT", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    # North Central
    {"name": "Anuradhapura Grid Substation", "code": "GS-ANU-01", "district_code": "ANU", "capacity_mva": 120.0, "voltage_level_kv": 220.0},
    {"name": "Habarana Grid Substation", "code": "GS-POL-01", "district_code": "POL", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    # Uva
    {"name": "Badulla Grid Substation", "code": "GS-BAD-01", "district_code": "BAD", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Monaragala Grid Substation", "code": "GS-MON-01", "district_code": "MON", "capacity_mva": 31.5, "voltage_level_kv": 132.0},
    # Sabaragamuwa
    {"name": "Ratnapura Grid Substation", "code": "GS-RAT-01", "district_code": "RAT", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
    {"name": "Kegalle Grid Substation", "code": "GS-KEG-01", "district_code": "KEG", "capacity_mva": 63.0, "voltage_level_kv": 132.0},
]


def seed_database(days_of_readings: int = 7, target_installations: int = 200):
    """
    Robust database seeder strictly conforming to specification:
    - 9 provinces
    - 25 districts
    - >= 20 substations (seeded: 27)
    - >= 200 installations (seeded: target_installations)
    - >= 1 week of 15-minute interval readings per installation (seeded: 7 days * 96 readings/day = 672 readings per installation)
    - Users for testing scopes and jurisdiction RBAC
    """
    start_time = time.time()
    print("=" * 70)
    print("SLSEA Solar Data API - Starting Database Seeding")
    print(f"Target: 9 Provinces, 25 Districts, >=20 Substations, {target_installations} Installations")
    print(f"Readings: {days_of_readings} days at 15-minute intervals ({days_of_readings * 96} readings/installation)")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Provinces
        print("\n[1/6] Seeding Provinces...")
        province_map = {}
        for prov_data in PROVINCES_DATA:
            prov = db.query(Province).filter(Province.code == prov_data["code"]).first()
            if not prov:
                prov = Province(name=prov_data["name"], code=prov_data["code"])
                db.add(prov)
                db.flush()
            province_map[prov_data["code"]] = prov
        db.commit()
        print(f"[OK] Provinces count: {len(province_map)} (Target: 9)")

        # 2. Seed Districts
        print("\n[2/6] Seeding Districts...")
        district_map = {}
        for dist_data in DISTRICTS_DATA:
            dist = db.query(District).filter(District.code == dist_data["code"]).first()
            if not dist:
                prov = province_map[dist_data["province_code"]]
                dist = District(name=dist_data["name"], code=dist_data["code"], province_id=prov.id)
                db.add(dist)
                db.flush()
            district_map[dist_data["code"]] = dist
        db.commit()
        print(f"[OK] Districts count: {len(district_map)} (Target: 25)")

        # 3. Seed Grid Substations
        print("\n[3/6] Seeding Grid Substations...")
        substation_map = {}
        for sub_data in SUBSTATIONS_DATA:
            sub = db.query(GridSubstation).filter(GridSubstation.code == sub_data["code"]).first()
            if not sub:
                dist = district_map[sub_data["district_code"]]
                sub = GridSubstation(
                    name=sub_data["name"],
                    code=sub_data["code"],
                    district_id=dist.id,
                    capacity_mva=sub_data["capacity_mva"],
                    voltage_level_kv=sub_data["voltage_level_kv"]
                )
                db.add(sub)
                db.flush()
            substation_map[sub_data["code"]] = sub
        db.commit()
        print(f"[OK] Grid Substations count: {len(substation_map)} (Target: >= 20)")

        # 4. Seed Users (RBAC & Jurisdiction Scopes)
        print("\n[4/6] Seeding SLSEA Users & Security Roles...")
        colombo_district = district_map["COL"]
        kandy_district = district_map["KAN"]
        western_province = province_map["WP"]

        users_to_seed = [
            {
                "username": "admin",
                "password": "adminpassword123",
                "role": "admin",
                "jurisdiction_type": "national",
                "jurisdiction_id": None,
                "scopes": "admin analyst-read-national analyst-read-province analyst-read-district installation-write"
            },
            {
                "username": "slsea_national_analyst",
                "password": "analystpassword123",
                "role": "analyst",
                "jurisdiction_type": "national",
                "jurisdiction_id": None,
                "scopes": "analyst-read-national"
            },
            {
                "username": "western_province_analyst",
                "password": "provincepassword123",
                "role": "analyst",
                "jurisdiction_type": "province",
                "jurisdiction_id": western_province.id,
                "scopes": "analyst-read-province"
            },
            {
                "username": "colombo_district_analyst",
                "password": "districtpassword123",
                "role": "analyst",
                "jurisdiction_type": "district",
                "jurisdiction_id": colombo_district.id,
                "scopes": "analyst-read-district"
            },
            {
                "username": "kandy_district_analyst",
                "password": "districtpassword123",
                "role": "analyst",
                "jurisdiction_type": "district",
                "jurisdiction_id": kandy_district.id,
                "scopes": "analyst-read-district"
            }
        ]

        for u_info in users_to_seed:
            existing_user = db.query(User).filter(User.username == u_info["username"]).first()
            if not existing_user:
                new_user = User(
                    username=u_info["username"],
                    hashed_password=hash_password(u_info["password"]),
                    role=u_info["role"],
                    jurisdiction_type=u_info["jurisdiction_type"],
                    jurisdiction_id=u_info["jurisdiction_id"],
                    scopes=u_info["scopes"],
                    is_active=True
                )
                db.add(new_user)
        db.commit()
        print("[OK] Seeded Admin, National, Province, and District Analyst accounts.")

        # 5. Seed >= 200 Solar Installations
        print(f"\n[5/6] Seeding {target_installations} Solar Installations...")
        existing_installations = db.query(SolarInstallation).all()
        installations_list = list(existing_installations)
        districts_list = list(district_map.values())
        substations_list = list(substation_map.values())

        types = ["rooftop", "ground-mounted", "floating"]
        random.seed(42)  # Deterministic seed

        needed = target_installations - len(existing_installations)
        if needed > 0:
            for idx in range(len(existing_installations) + 1, target_installations + 1):
                district = districts_list[idx % len(districts_list)]
                # Find substations in this district, or any substation if none
                dist_substations = [s for s in substations_list if s.district_id == district.id]
                substation = dist_substations[0] if dist_substations else substations_list[idx % len(substations_list)]

                meter_id = f"MTR-LK-{district.code}-{idx:04d}"
                capacity = round(random.choice([10.0, 20.0, 50.0, 100.0, 150.0, 250.0, 500.0]) + random.uniform(0.5, 4.5), 2)
                inst_type = random.choice(types)
                status_choice = "active" if idx % 20 != 0 else "maintenance"

                inst = SolarInstallation(
                    name=f"Solar Facility {district.name} #{idx:03d}",
                    meter_id=meter_id,  # Strict Rule 1
                    inverter_serial=f"INV-SN-{random.randint(100000, 999999)}",
                    capacity_kw=capacity,
                    installation_type=inst_type,
                    status=status_choice,
                    district_id=district.id,
                    grid_substation_id=substation.id,
                    commissioned_date=(datetime.now().date() - timedelta(days=random.randint(100, 1000)))
                )
                db.add(inst)
                installations_list.append(inst)

            db.commit()
            # Refresh list
            installations_list = db.query(SolarInstallation).all()

        print(f"[OK] Total Solar Installations: {len(installations_list)} (Target: >= 200)")

        # 6. Seed >= 1 Week of 15-Minute Interval Readings
        # 15-minute intervals: 4 readings/hour * 24 hours/day * days_of_readings
        print(f"\n[6/6] Seeding {days_of_readings} Days of 15-Minute Generation Readings...")
        intervals_per_day = 96
        total_intervals = intervals_per_day * days_of_readings
        
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start_date = now - timedelta(days=days_of_readings)

        # Check existing readings count
        existing_readings_count = db.query(GenerationReading).count()
        expected_min_readings = len(installations_list) * total_intervals

        if existing_readings_count < expected_min_readings:
            print(f"Generating ~{expected_min_readings} readings in bulk chunks for optimal performance...")
            
            bulk_records = []
            chunk_size = 5000
            total_inserted = 0

            # Delete any partial readings to ensure consistent time series
            if existing_readings_count > 0:
                print("Clearing prior partial readings...")
                db.query(GenerationReading).delete()
                db.commit()

            for inst in installations_list:
                cumulative_energy = round(random.uniform(500.0, 5000.0), 2)
                
                for step in range(total_intervals):
                    reading_time = start_date + timedelta(minutes=15 * step)
                    hour_float = reading_time.hour + (reading_time.minute / 60.0)

                    # Solar curve: 0 power between 18:30 and 05:30; bell curve during daylight
                    if 6.0 <= hour_float <= 18.0:
                        # Sun angle curve peaking at 12:00
                        solar_angle = math.sin((hour_float - 6.0) / 12.0 * math.pi)
                        irradiance_factor = max(0.0, solar_angle)
                        # Add slight weather variability
                        variation = random.uniform(0.85, 1.05)
                        power_kw = round(inst.capacity_kw * irradiance_factor * variation, 3)
                    else:
                        power_kw = 0.0

                    # 15 minutes = 0.25 hour
                    delta_energy = power_kw * 0.25
                    cumulative_energy = round(cumulative_energy + delta_energy, 3)

                    # Voltage varies around nominal 230V
                    voltage = round(random.uniform(227.0, 233.5), 1)

                    bulk_records.append({
                        "installation_id": inst.id,
                        "timestamp": reading_time,
                        "power_kw": power_kw,
                        "energy_kwh": cumulative_energy,
                        "voltage": voltage
                    })

                    if len(bulk_records) >= chunk_size:
                        db.execute(insert(GenerationReading), bulk_records)
                        db.commit()
                        total_inserted += len(bulk_records)
                        bulk_records = []
                        if total_inserted % 20000 == 0:
                            print(f"  ... inserted {total_inserted} readings ({total_inserted / expected_min_readings * 100:.1f}%)")

            if bulk_records:
                db.execute(insert(GenerationReading), bulk_records)
                db.commit()
                total_inserted += len(bulk_records)

            print(f"[OK] Successfully generated and inserted {total_inserted} generation readings.")
        else:
            print(f"[OK] Existing readings count {existing_readings_count} meets or exceeds requirements ({expected_min_readings}).")

        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"SEEDING COMPLETED SUCCESSFULLY in {elapsed:.2f} seconds!")
        print("Summary:")
        print(f"- Provinces: {db.query(Province).count()}")
        print(f"- Districts: {db.query(District).count()}")
        print(f"- Grid Substations: {db.query(GridSubstation).count()}")
        print(f"- Solar Installations: {db.query(SolarInstallation).count()}")
        print(f"- Generation Readings: {db.query(GenerationReading).count()}")
        print(f"- Users: {db.query(User).count()}")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database for SLSEA Solar Generation Data API")
    parser.add_argument("--days", type=int, default=7, help="Number of days of 15-minute readings to generate (default: 7)")
    parser.add_argument("--installations", type=int, default=200, help="Number of solar installations to generate (default: 200)")
    args = parser.parse_args()

    seed_database(days_of_readings=args.days, target_installations=args.installations)
