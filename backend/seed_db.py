# seed_db.py
from models import get_engine, get_session, init_db, Customer, Technician, Job, Priority, JobStatus
from datetime import datetime, timedelta

# 1️⃣ Connect to DB and create tables
engine = get_engine()
init_db(engine)
session = get_session(engine)

# 2️⃣ Seed Customers
customers = [
    Customer(name="Alice Johnson", phone="555-111-2222", email="alice@example.com", address="123 Main St", latitude=45.52, longitude=-122.67),
    Customer(name="Bob Smith", phone="555-333-4444", email="bob@example.com", address="456 Oak Ave", latitude=45.53, longitude=-122.68)
]

# 3️⃣ Seed Technicians
technicians = [
    Technician(name="Tech Mike", phone="555-555-5555", skills=["hvac", "residential"], certifications=["EPA_608"], equipment=["gauges", "recovery_machine"]),
    Technician(name="Tech Sarah", phone="555-666-7777", skills=["hvac", "commercial"], certifications=["NATE"], equipment=["gauges"])
]

# 4️⃣ Seed Jobs
jobs = [
    Job(
        customer=customers[0],
        title="AC Not Cooling",
        description="Customer reports AC unit not cooling upstairs rooms.",
        required_skills=["hvac", "residential"],
        priority=Priority.CRITICAL,
        status=JobStatus.PENDING,
        latitude=45.52,
        longitude=-122.67,
        estimated_hours=2.5,
        submitted_at=datetime.utcnow()
    ),
    Job(
        customer=customers[1],
        title="Heater Malfunction",
        description="Heater stops working intermittently.",
        required_skills=["hvac", "commercial"],
        priority=Priority.URGENT,
        status=JobStatus.PENDING,
        latitude=45.53,
        longitude=-122.68,
        estimated_hours=3.0,
        submitted_at=datetime.utcnow() - timedelta(days=1)
    )
]

# 5️⃣ Add everything to session and commit
session.add_all(customers + technicians + jobs)
session.commit()

print("✅ Seeded database with Customers, Technicians, and Jobs")
