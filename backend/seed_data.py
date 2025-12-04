# backend/seed_data.py
"""
Seed the HVAC Dispatch System database with realistic test data
"""

from datetime import datetime, timedelta
import random

from backend.models import get_engine, get_session, init_db, Priority, JobStatus
from backend.database import DatabaseHelper

# --- Config ---
NUM_CUSTOMERS = 5
NUM_TECHS = 5
NUM_JOBS = 10
SKILLS_POOL = ["hvac", "residential", "commercial", "electrical", "plumbing"]

# --- Helper Functions ---
def random_location():
    """Return random lat/lon around Austin for testing"""
    return round(random.uniform(30.25, 30.30), 6), round(random.uniform(-97.75, -97.72), 6)

def random_datetime(days_back=30):
    """Return random datetime within past `days_back` days"""
    return datetime.utcnow() - timedelta(days=random.randint(0, days_back), hours=random.randint(0, 23))

# --- Seed Script ---
def seed_database():
    engine = get_engine()
    init_db(engine)
    session = get_session()
    db = DatabaseHelper(session)

    print("🌱 Seeding database...")

    # ---------------- CUSTOMERS ----------------
    customers = []
    for i in range(NUM_CUSTOMERS):
        lat, lon = random_location()
        cust = db.create_customer(
            name=f"Customer {i+1}",
            phone=f"512-555-01{str(i+10)}",
            address=f"{100+i} Main St, Austin TX 7870{i}",
            email=f"customer{i+1}@example.com",
            lat=lat,
            lon=lon
        )
        customers.append(cust)
    print(f"✅ Created {len(customers)} customers")

    # ---------------- TECHNICIANS ----------------
    techs = []
    for i in range(NUM_TECHS):
        lat, lon = random_location()
        
        # Create technician directly with all fields
        from backend.models import Technician as TechModel
        tech = TechModel(
            name=f"Tech {i+1}",
            phone=f"512-555-02{str(i+10)}",
            skills=random.sample(SKILLS_POOL, k=2),
            certifications=[],
            equipment=[],
            current_lat=lat,
            current_lon=lon,
            shift_start=random.choice([8,9,10]),
            shift_end=random.choice([17,18,19]),
            on_call=random.choice([True, False]),
            hourly_rate=random.uniform(80, 120),
            hourly_cost=random.uniform(25, 45),
            active=True
        )
        session.add(tech)
        session.commit()
        session.refresh(tech)
        techs.append(tech)
    print(f"✅ Created {len(techs)} technicians")

    # ---------------- JOBS ----------------
    jobs = []
    for i in range(NUM_JOBS):
        customer = random.choice(customers)
        lat, lon = random_location()
        job = db.create_job(
            customer_id=customer.id,
            title=f"Job {i+1} for {customer.name}",
            description="Routine maintenance or repair required",
            required_skills=random.sample(SKILLS_POOL, k=1),
            priority=random.choice(list(Priority)),
            lat=lat,
            lon=lon,
            estimated_hours=round(random.uniform(1, 5), 2)
        )
        jobs.append(job)
    print(f"✅ Created {len(jobs)} jobs")

    # ---------------- ASSIGNMENTS ----------------
    assignments = []
    for job in jobs:
        print(f"Trying to assign job {job.id} - {job.title}")
        assignment = db.auto_assign_job(job.id)
        if assignment:
            assignments.append(assignment)
            print(f"✅ Assigned Job {job.title} to Tech ID {assignment.tech_id}")
        else:
            print(f"⚠️ Could not assign Job {job.title} - no suitable tech")
    print(f"✅ Created {len(assignments)} assignments")

    session.close()
    print("\n🎉 Database seeding complete!")

if __name__ == "__main__":
    seed_database()