# test_assignments.py
from datetime import datetime
from backend.database import SessionLocal, DatabaseHelper
from backend.models import Technician, Job, Priority, JobStatus

def main():
    session = SessionLocal()
    db = DatabaseHelper(session)

    # -------------------------------
    # 1. Create dummy technicians
    # -------------------------------
    tech1 = Technician(
        name="Alice",
        phone="111-111-1111",
        skills=["HVAC", "Electrical"],
        current_latitude=40.0,
        current_longitude=-75.0,
        active=True
    )
    tech2 = Technician(
        name="Bob",
        phone="222-222-2222",
        skills=["HVAC"],
        current_latitude=40.1,
        current_longitude=-75.1,
        active=True
    )
    
    session.add_all([tech1, tech2])
    session.commit()
    
    # -------------------------------
    # 2. Create a dummy job
    # -------------------------------
    job = Job(
        customer_id=1,
        title="Fix AC",
        required_skills=["HVAC"],
        priority=Priority.URGENT,
        status=JobStatus.PENDING,
        latitude=40.05,
        longitude=-75.05,
        estimated_hours=2,
        submitted_at=datetime.utcnow()
    )
    
    session.add(job)
    session.commit()
    
    # -------------------------------
    # 3. Auto-assign job using Step 2.2
    # -------------------------------
    assignment = db.auto_assign_job(job.id)
    
    if assignment:
        print(f"Assigned Job {job.id} to Technician {assignment.tech_id}")
        print(f"Score: {assignment.match_score}")
    else:
        print("No assignment could be made.")

if __name__ == "__main__":
    main()
