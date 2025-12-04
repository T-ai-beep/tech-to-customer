# test_financial_calc.py
from backend.database import get_session
from backend.models import Job, Technician, JobPart, Assignment, JobStatus
from backend.financial_calculator import FinancialCalculator
from datetime import datetime

session = get_session()

# --- Create technician ---
tech = Technician(
    name="Tech A",
    hourly_rate=120.0,
    hourly_cost=40.0,
    active=True
)
session.add(tech)
session.commit()

# --- Create job ---
job = Job(
    title="HVAC Repair",
    customer_id=1,
    assigned_to=tech.id,
    status=JobStatus.COMPLETED,
    estimated_hours=2.0,
    actual_hours=3.0
)
session.add(job)
session.commit()

# --- Add assignment (for fuel cost) ---
assign = Assignment(
    job_id=job.id,
    technician_id=tech.id,
    distance_miles=15.0
)
session.add(assign)
session.commit()

# --- Add parts ---
p1 = JobPart(
    job_id=job.id,
    part_name="Compressor",
    unit_cost=150,
    unit_price=300,
    quantity_used=1
p2 = JobPart(
    job_id=job.id,
    part_name="Capacitor",
    unit_cost=10,
    unit_price=30,
    quantity_used=2
)
session.add_all([p1, p2])
session.commit()

# ---- RUN FINANCIAL CALCULATOR ----
calc = FinancialCalculator(session)
res = calc.calculate_job_financials(job.id)

print("=== FINANCIAL RESULTS ===")
print("Revenue:", res.total_revenue)
print("Cost:", res.total_cost)
print("Profit:", res.gross_profit)
print("Margin %:", res.gross_margin_pct)
