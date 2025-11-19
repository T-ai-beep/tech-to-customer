# models.py
import os
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, JSON, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

# Load environment variables
load_dotenv()

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
    
    jobs = relationship("Job", back_populates="customer")

class Technician(Base):
    __tablename__ = 'technicians'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(200))
    skills = Column(JSON, nullable=False, default=list)
    certifications = Column(JSON, default=list)
    equipment = Column(JSON, default=list)
    shift_start = Column(Integer, default=8)
    shift_end = Column(Integer, default=17)
    on_call = Column(Boolean, default=False)
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    free_at = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assignments = relationship("Assignment", back_populates="technician")

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    title = Column(String(200))
    description = Column(Text)
    required_skills = Column(JSON, nullable=False)
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.ROUTINE)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_for = Column(DateTime)
    assigned_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    estimated_hours = Column(Float, nullable=False)
    actual_hours = Column(Float)
    estimated_arrival = Column(DateTime)
    
    assigned_to = Column(Integer, ForeignKey('technicians.id'))
    
    sla_met = Column(Boolean)
    response_time_hours = Column(Float)
    
    equipment_details = Column(JSON)
    parts_needed = Column(JSON, default=list)
    
    customer = relationship("Customer", back_populates="jobs")
    assignment = relationship("Assignment", back_populates="job", uselist=False)

class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    tech_id = Column(Integer, ForeignKey('technicians.id'), nullable=False)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    distance_miles = Column(Float)
    travel_time_hours = Column(Float)
    match_score = Column(Float)
    
    job = relationship("Job", back_populates="assignment")
    technician = relationship("Technician", back_populates="assignments")

# Database connection functions
def get_engine(database_url=None):
    """Create database engine"""
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set in environment")
    
    # Handle old postgres:// URLs
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return create_engine(
        database_url,
        echo=True,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 30,
            "options": "-c statement_timeout=30000"
        }
    )

def get_session(engine):
    """Create database session"""
    Session = sessionmaker(bind=engine)
    return Session()

def init_db(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")

if __name__ == "__main__":
    engine = get_engine()
    init_db(engine)
