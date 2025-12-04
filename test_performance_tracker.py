from datetime import datetime
from backend.models import Technician, TechPerformanceMetric, get_session
from init_db import init_db

# Initialize DB (creates tables if not exist)
init_db()

# Start session
session = get_session()

# 1️⃣ Create a test technician
tech = Technician(
    name="Test Tech",
    phone="555-1234",
    skills='["HVAC"]',
    certifications='[]',
    equipment='[]',
    shift_start=8,
    shift_end=17,
    on_call=False,
    current_lat=None,
    current_lon=None,
    active=True
)
session.add(tech)
session.commit()  # must commit to generate tech.id

# 2️⃣ Create a performance metric record for that tech
metric = TechPerformanceMetric(
    tech_id=tech.id,
    date=datetime.utcnow(),
    shift_hours=8,
    billable_hours=7,
    drive_time_hours=0.5,
    idle_time_hours=0.5,
    jobs_completed=3,
    jobs_cancelled=0,
    callbacks=0,
    revenue_generated=450,
    avg_job_value=150,
    utilization_rate=0.875,  # 7/8 hours
    first_time_fix_rate=1.0  # 100%
)
session.add(metric)
session.commit()

# 3️⃣ Query to verify
saved_metric = session.query(TechPerformanceMetric).first()
if saved_metric:
    print("Saved metric:", saved_metric.id, saved_metric.tech_id, saved_metric.revenue_generated)
else:
    print("No metric found")

session.close()
