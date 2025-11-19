# models.py
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, JSON, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

# Enums
class Priority(enum.Enum):
    CRITICAL = "critical"
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"

class JobStatus(enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Models
class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(200))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship("Job", back_populates="customer")

class Technician(Base):
    __tablename__ = 'technicians'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(200))
    skills = Column(JSON, nullable=False, default=list)  # ["hvac", "residential"]
    certifications = Column(JSON, default=list)  # ["EPA_608", "NATE"]
    equipment = Column(JSON, default=list)  # ["recovery_machine", "gauges"]
    shift_start = Column(Integer, default=8)  # Hour (0-23)
    shift_end = Column(Integer, default=17)
    on_call = Column(Boolean, default=False)
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    free_at = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="technician")

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Job details
    title = Column(String(200))  # "AC Not Cooling"
    description = Column(Text)
    required_skills = Column(JSON, nullable=False)  # ["hvac", "residential"]
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.ROUTINE)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    
    # Location
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Timing
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_for = Column(DateTime)  # If customer requested specific time
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Estimates vs Actuals
    estimated_hours = Column(Float, nullable=False)
    actual_hours = Column(Float)
    estimated_arrival = Column(DateTime)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey('technicians.id'))
    
    # SLA
    sla_met = Column(Boolean)
    response_time_hours = Column(Float)  # Time from submission to start
    
    # Equipment/Parts
    equipment_details = Column(JSON)  # {"brand": "Carrier", "model": "XYZ"}
    parts_needed = Column(JSON, default=list)
    
    # Relationships
    customer = relationship("Customer", back_populates="jobs")
    assignment = relationship("Assignment", back_populates="job", uselist=False)

class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    tech_id = Column(Integer, ForeignKey('technicians.id'), nullable=False)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    distance_miles = Column(Float)  # Distance from tech to job
    travel_time_hours = Column(Float)  # Calculated travel time
    match_score = Column(Float)  # Your matching algorithm score
    
    # Relationships
    job = relationship("Job", back_populates="assignment")
    technician = relationship("Technician", back_populates="assignments")

# Database connection
def get_engine(database_url=None):
    """Create database engine"""
    if database_url is None:
        # Default to local PostgreSQL
        database_url = "postgresql://localhost/hvac_dispatch"
    return create_engine(database_url, echo=True)

def get_session(engine):
    """Create database session"""
    Session = sessionmaker(bind=engine)
    return Session()

def init_db(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")

if __name__ == "__main__":
    # Test database creation
    engine = get_engine()
    init_db(engine)