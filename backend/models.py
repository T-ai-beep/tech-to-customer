# backend/models.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, JSON, ForeignKey, Text, Enum as SQLEnum,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
from dotenv import load_dotenv

Base = declarative_base()
load_dotenv()

# ===================== ENUMS =====================
class Priority(enum.Enum):
    ROUTINE = "Routine"
    URGENT = "Urgent"
    HIGH = "High"
    CRITICAL = "Critical"
    EMERGENCY = "Emergency"

class JobStatus(enum.Enum):
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"  # Optional, if you want to track cancellations

# ===================== DATABASE =====================
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./hvac_dispatch.db")
engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)

def get_engine():
    return engine

def get_session():
    return SessionLocal()

def init_db(engine=engine):
    Base.metadata.create_all(bind=engine)

# ===================== MODELS =====================

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, unique=True)
    address = Column(String, nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    notes = Column(Text)

    jobs = relationship("Job", back_populates="customer")


class Technician(Base):
    __tablename__ = "technicians"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    skills = Column(JSON, default=[])
    certifications = Column(JSON, default=[])
    equipment = Column(JSON, default=[])
    shift_start = Column(Integer, default=8)
    shift_end = Column(Integer, default=17)
    on_call = Column(Boolean, default=False)
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    free_at = Column(DateTime, default=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="technician")
    skill_levels = relationship("TechSkillLevel", back_populates="tech")
    inventory = relationship("TechInventory", back_populates="tech")
    performance_metrics = relationship("TechPerformanceMetric", back_populates="tech")


class TechSkillLevel(Base):
    __tablename__ = "tech_skill_levels"
    id = Column(Integer, primary_key=True)
    tech_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    proficiency_level = Column(Integer, nullable=False)  # 1-5 scale

    tech = relationship("Technician", back_populates="skill_levels")


# ----------------- JOBS -----------------
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    required_skills = Column(JSON, default=[])
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.ROUTINE)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    lat = Column(Float)
    lon = Column(Float)
    address = Column(String)
    estimated_hours = Column(Float, nullable=False)
    equipment_details = Column(JSON, default={})
    submitted_at = Column(DateTime, default=datetime.utcnow)
    sla_met = Column(Boolean)

    customer = relationship("Customer", back_populates="jobs")
    assignments = relationship("Assignment", back_populates="job")
    parts = relationship("JobPart", back_populates="job")
    financial = relationship("JobFinancial", uselist=False, back_populates="job")


# ----------------- TECH INVENTORY -----------------
class TechInventory(Base):
    __tablename__ = "tech_inventory"

    id = Column(Integer, primary_key=True)
    tech_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    part_sku = Column(String, nullable=False)
    quantity = Column(Integer, default=0)

    tech = relationship("Technician", back_populates="inventory")


# ----------------- JOB PARTS -----------------
class JobPart(Base):
    __tablename__ = "job_parts"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    part_sku = Column(String, nullable=False)
    quantity_used = Column(Integer, default=1)
    unit_cost = Column(Float, default=0)
    unit_price = Column(Float, default=0)

    job = relationship("Job", back_populates="parts")


class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    tech_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    distance_miles = Column(Float)
    travel_time_hours = Column(Float)
    match_score = Column(Float)

    job = relationship("Job", back_populates="assignments")
    technician = relationship("Technician", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint('job_id', 'tech_id', name='uix_job_tech'),
    )


# ----------------- JOB FINANCIALS -----------------
class JobFinancial(Base):
    __tablename__ = "job_financials"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)

    labor_rate_per_hour = Column(Float, default=0)
    labor_hours_charged = Column(Float, default=0)
    labor_revenue = Column(Float, default=0)
    parts_revenue = Column(Float, default=0)
    total_revenue = Column(Float, default=0)

    tech_hourly_cost = Column(Float, default=0)
    labor_cost = Column(Float, default=0)
    parts_cost = Column(Float, default=0)
    fuel_cost = Column(Float, default=0)
    overhead_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)

    gross_profit = Column(Float, default=0)
    gross_margin_pct = Column(Float, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="financial")


# ----------------- TECH PERFORMANCE METRICS -----------------
class TechPerformanceMetric(Base):
    __tablename__ = "tech_performance_metric"

    id = Column(Integer, primary_key=True, index=True)
    tech_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)

    shift_hours = Column(Float, default=8)
    billable_hours = Column(Float, default=0)
    drive_time_hours = Column(Float, default=0)
    idle_time_hours = Column(Float, default=0)

    jobs_completed = Column(Integer, default=0)
    jobs_cancelled = Column(Integer, default=0)
    callbacks = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    avg_job_value = Column(Float, default=0)
    utilization_rate = Column(Float, default=0)
    first_time_fix_rate = Column(Float, default=0)

    tech = relationship("Technician", back_populates="performance_metrics")


# ===================== EXPORTS =====================
__all__ = [
    "Customer",
    "Technician",
    "TechSkillLevel",
    "TechInventory",
    "Job",
    "JobPart",
    "Assignment",
    "JobFinancial",
    "TechPerformanceMetric",
    "Priority",
    "JobStatus"
]
