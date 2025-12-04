# backend/test_assignment_engine.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Technician, TechSkillLevel, Job, Priority
from backend.assignment_engine import AssignmentEngine

# ----------------- SETUP IN-MEMORY DB -----------------
engine = create_engine("sqlite:///:memory:", echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base.metadata.create_all(bind=engine)

# ----------------- CREATE DUMMY TECHNICIANS -----------------
tech1 = Technician(
    name="Alice",
    phone="555-1111",
    current_lat=37.7749,
    current_lon=-122.4194,
    hourly_rate=100.0,
    hourly_cost=40.0
)
tech1.skill_levels = [
    TechSkillLevel(skill_name="HVAC", proficiency_level=5),
    TechSkillLevel(skill_name="Plumbing", proficiency_level=3)
]

tech2 = Technician(
    name="Bob",
    phone="555-2222",
    current_lat=37.8044,
    current_lon=-122.2711,
    hourly_rate=90.0,
    hourly_cost=35.0
)
tech2.skill_levels = [
    TechSkillLevel(skill_name="HVAC", proficiency_level=2),
    TechSkillLevel(skill_name="Electrical", proficiency_level=5)
]

session.add_all([tech1, tech2])
session.commit()

# ----------------- CREATE DUMMY JOB -----------------
job1 = Job(
    title="Fix AC Unit",
    customer_id=1,
    required_skills=["HVAC"],
    priority=Priority.CRITICAL,
    lat=37.7790,
    lon=-122.4183,
    estimated_hours=2
)
session.add(job1)
session.commit()

# ----------------- RUN ASSIGNMENT ENGINE -----------------
engine_obj = AssignmentEngine(session)
result = engine_obj.find_best_technician(job1.id)

if result:
    tech, score, breakdown = result
    print(f"Best Tech: {tech.name}")
    print(f"Score: {score:.2f}")
    print("Breakdown:", {k: f"{v:.2f}" if isinstance(v, float) else v 
                        for k, v in breakdown.items()})
else:
    print("No suitable technician found.")