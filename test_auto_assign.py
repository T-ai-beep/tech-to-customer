from backend.database import DatabaseHelper, get_engine, get_session
from backend.models import Technician, Job, Priority, JobStatus
from datetime import datetime

def main():
    # create engine & session
    engine = get_engine()
    session = get_session()
    db = DatabaseHelper(session)

    # Create technicians
    tech1 = db.create_technician(
        name="Bob",
        phone="111111",
        skills=["HVAC"],
        shift_start=8,
        shift_end=17,
        current_lat=39.9,
        current_lon=-75.1
    )

    tech2 = db.create_technician(
        name="Alice",
        phone="222222",
        skills=["Plumbing"],
        shift_start=9,
        shift_end=18,
        current_lat=40.1,
        current_lon=-75.0
    )

    # Create a customer first
    customer = db.create_customer(
        name="Test Customer",
        phone="555-0000",
        address="123 Main St",
        lat=39.95,
        lon=-75.05
    )

    # Create a job
    job = db.create_job(
        customer_id=int(customer.id),  # type: ignore
        title="Fix AC",
        description="AC not cooling",
        required_skills=["HVAC"],
        priority=Priority.ROUTINE,
        lat=39.95,
        lon=-75.05,
        estimated_hours=2
    )

    # Auto-assign
    assignment = db.auto_assign_job(int(job.id))  # type: ignore
    if assignment:
        print(f"✅ Job assigned to {assignment.technician.name}")
    else:
        print("❌ Could not assign job")

if __name__ == "__main__":
    main()
