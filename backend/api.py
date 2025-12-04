# api.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Database imports
from backend.models import get_engine, get_session, Priority, JobStatus
from backend.database import DatabaseHelper

# ===================== FASTAPI SETUP =====================
app = FastAPI(
    title="HVAC Dispatch API",
    description="Complete API for HVAC technician scheduling and dispatch management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ===================== DATABASE =====================
engine = get_engine()
session = get_session()
db = DatabaseHelper(session)

# ===================== REQUEST / RESPONSE MODELS =====================
class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: str
    lat: float
    lon: float
    email: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    name: str
    phone: str
    address: str
    lat: float
    lon: float
    email: Optional[str] = None

    class Config:
        from_attributes = True

class TechnicianCreate(BaseModel):
    name: str
    phone: str
    skills: List[str]
    certifications: Optional[List[str]] = []
    equipment: Optional[List[str]] = []
    shift_start: int = 8
    shift_end: int = 17
    on_call: bool = False
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    hourly_rate: Optional[float] = 95.0
    hourly_cost: Optional[float] = 35.0

class TechnicianResponse(BaseModel):
    id: int
    name: str
    phone: str
    skills: List[str]
    certifications: List[str]
    shift_start: int
    shift_end: int
    on_call: bool
    current_lat: Optional[float]
    current_lon: Optional[float]
    free_at: Optional[datetime]
    active: bool
    hourly_rate: float
    hourly_cost: float

    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    customer_id: int
    title: str
    description: Optional[str] = None
    required_skills: List[str]
    priority: str
    lat: float
    lon: float
    estimated_hours: float
    address: Optional[str] = None
    equipment_details: Optional[dict] = None

class JobResponse(BaseModel):
    id: int
    customer_id: int
    title: str
    description: Optional[str]
    required_skills: List[str]
    priority: str
    status: str
    lat: float
    lon: float
    submitted_at: datetime
    estimated_hours: float
    actual_hours: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    sla_met: Optional[bool]

    class Config:
        from_attributes = True

# ===================== HEALTH =====================
@app.get("/")
def root():
    return {"message": "HVAC Dispatch API is running", "version": "2.0.0", "status": "healthy"}

@app.get("/health")
def health_check():
    try:
        db.get_all_customers()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# ===================== CUSTOMER ENDPOINTS =====================
@app.get("/customers", response_model=List[CustomerResponse])
def get_customers():
    return db.get_all_customers()

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int):
    customer = db.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(customer: CustomerCreate):
    return db.create_customer(
        name=customer.name,
        phone=customer.phone,
        address=customer.address,
        lat=customer.lat,
        lon=customer.lon,
        email=customer.email,
        notes=customer.notes
    )

# ===================== TECHNICIAN ENDPOINTS =====================
@app.get("/technicians", response_model=List[TechnicianResponse])
def get_technicians(available_only: bool = Query(False)):
    return db.get_available_technicians() if available_only else db.get_all_technicians()

@app.get("/technicians/{tech_id}", response_model=TechnicianResponse)
def get_technician(tech_id: int):
    tech = db.get_technician(tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    return tech

@app.post("/technicians", response_model=TechnicianResponse, status_code=201)
def create_technician(tech: TechnicianCreate):
    from backend.models import Technician as TechModel
    
    try:
        new_tech = TechModel(
            name=tech.name,
            phone=tech.phone,
            skills=tech.skills,
            certifications=tech.certifications or [],
            equipment=tech.equipment or [],
            shift_start=tech.shift_start,
            shift_end=tech.shift_end,
            on_call=tech.on_call,
            current_lat=tech.current_lat,
            current_lon=tech.current_lon,
            hourly_rate=tech.hourly_rate or 95.0,
            hourly_cost=tech.hourly_cost or 35.0,
            active=True
        )
        session.add(new_tech)
        session.commit()
        session.refresh(new_tech)
        return new_tech
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ===================== JOB ENDPOINTS =====================
@app.get("/jobs")
def get_jobs(status: Optional[str] = None, priority: Optional[str] = None):
    jobs = db.get_all_jobs()
    
    # Convert enum values to strings for JSON serialization
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "customer_id": job.customer_id,
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
            "priority": job.priority.value,
            "status": job.status.value,
            "lat": job.lat,
            "lon": job.lon,
            "submitted_at": job.submitted_at,
            "estimated_hours": job.estimated_hours,
            "actual_hours": job.actual_hours,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "sla_met": job.sla_met
        }
        
        # Filter by status if provided
        if status and job.status.value.lower() != status.lower():
            continue
            
        # Filter by priority if provided
        if priority and job.priority.value.lower() != priority.lower():
            continue
            
        result.append(job_dict)
    
    return result

@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get assignment info
    assignment = db.get_assignment_by_job(job_id)
    assigned_tech_id = assignment.tech_id if assignment else None
    
    return {
        "id": job.id,
        "customer_id": job.customer_id,
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "priority": job.priority.value,
        "status": job.status.value,
        "lat": job.lat,
        "lon": job.lon,
        "submitted_at": job.submitted_at,
        "estimated_hours": job.estimated_hours,
        "actual_hours": job.actual_hours,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "sla_met": job.sla_met,
        "assigned_tech_id": assigned_tech_id
    }

@app.post("/jobs", status_code=201)
def create_job(job: JobCreate):
    try:
        # Convert string priority to enum
        priority_map = {
            "routine": Priority.ROUTINE,
            "urgent": Priority.URGENT,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL,
            "emergency": Priority.EMERGENCY
        }
        
        priority_enum = priority_map.get(job.priority.lower())
        if not priority_enum:
            raise HTTPException(status_code=400, detail="Invalid priority")
        
        new_job = db.create_job(
            customer_id=job.customer_id,
            title=job.title,
            required_skills=job.required_skills,
            priority=priority_enum,
            lat=job.lat,
            lon=job.lon,
            estimated_hours=job.estimated_hours,
            description=job.description,
            address=job.address,
            equipment_details=job.equipment_details
        )
        
        return {
            "id": new_job.id,
            "title": new_job.title,
            "priority": new_job.priority.value,
            "status": new_job.status.value,
            "message": "Job created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs/{job_id}/auto-assign")
def auto_assign_job(job_id: int):
    assignment = db.auto_assign_job(job_id)
    if not assignment:
        raise HTTPException(status_code=400, detail="No available technician found")
    
    return {
        "message": "Job assigned successfully",
        "assignment_id": assignment.id,
        "tech_id": assignment.tech_id,
        "match_score": assignment.match_score,
        "distance_miles": assignment.distance_miles
    }

@app.post("/jobs/{job_id}/start")
def start_job(job_id: int):
    job = db.start_job(job_id)
    if not job:
        raise HTTPException(status_code=400, detail="Could not start job")
    
    return {"message": "Job started", "job_id": job_id, "status": job.status.value}

@app.post("/jobs/{job_id}/complete")
def complete_job(job_id: int, actual_hours: float):
    job = db.complete_job(job_id, actual_hours)
    if not job:
        raise HTTPException(status_code=400, detail="Could not complete job")
    
    return {
        "message": "Job completed",
        "job_id": job_id,
        "status": job.status.value,
        "actual_hours": actual_hours
    }

# ===================== DASHBOARD ENDPOINTS =====================
@app.get("/dashboard/stats")
def get_dashboard_stats():
    return db.get_dashboard_stats()

@app.get("/dashboard/sla-metrics")
def get_sla_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    from datetime import datetime as dt
    
    start = dt.fromisoformat(start_date) if start_date else None
    end = dt.fromisoformat(end_date) if end_date else None
    
    return db.get_sla_metrics(start, end)

# ===================== RUN SERVER =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)