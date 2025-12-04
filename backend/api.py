# api.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

# Database imports
from backend.models import get_engine, get_session, Priority, JobStatus, Assignment
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
session = get_session(engine)
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
    assigned_to: Optional[int]
    estimated_hours: float
    sla_met: Optional[bool]

    class Config:
        from_attributes = True

# ===================== CONNECTION MANAGER =====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dispatchers": set(),
            "techs": set()
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections.setdefault(client_type, set()).add(websocket)
        print(f"{client_type} connected ({len(self.active_connections[client_type])})")

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections.get(client_type, set()).discard(websocket)
        print(f"{client_type} disconnected ({len(self.active_connections.get(client_type, []))})")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, client_type: str):
        disconnected = set()
        for conn in self.active_connections.get(client_type, set()):
            try:
                await conn.send_json(message)
            except:
                disconnected.add(conn)
        for conn in disconnected:
            self.disconnect(conn, client_type)

manager = ConnectionManager()

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
    return db.create_technician(
        name=tech.name,
        phone=tech.phone,
        skills=tech.skills,
        certifications=tech.certifications,
        equipment=tech.equipment,
        shift_start=tech.shift_start,
        shift_end=tech.shift_end,
        on_call=tech.on_call,
        current_lat=tech.current_lat,
        current_lon=tech.current_lon
    )

# ===================== JOB ENDPOINTS =====================
@app.get("/jobs")
def get_jobs(status: Optional[str] = None, priority: Optional[str] = None):
    jobs = db.get_all_jobs()
    if status:
        status_enum = JobStatus[status.upper()]
        jobs = [j for j in jobs if j.status == status_enum]
    if priority:
        priority_enum = Priority[priority.upper()]
        jobs = [j for j in jobs if j.priority == priority_enum]
    for job in jobs:
        job.priority = job.priority.value
        job.status = job.status.value
    return jobs

@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.priority = job.priority.value
    job.status = job.status.value
    return job

@app.post("/jobs", status_code=201)
def create_job(job: JobCreate):
    priority_enum = Priority[job.priority.upper()]
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
    new_job.priority = new_job.priority.value
    new_job.status = new_job.status.value
    return new_job

@app.post("/jobs/{job_id}/auto-assign")
async def auto_assign_job(job_id: int):
    assignment = db.auto_assign_job(job_id)
    if not assignment:
        raise HTTPException(status_code=400, detail="No available technician found")
    return {"message": "Job assigned", "assignment": assignment}

# ===================== RUN SERVER =====================
if __name__ == "__main__":
    # Optional: seed a job before running server
    from backend.database import DatabaseHelper
    db_helper = DatabaseHelper(session)
    
    # Example: create a job
    db_helper.create_job(
        customer_id=1,
        title="Fix AC",
        description="AC not cooling",
        required_skills=["HVAC"],
        priority=Priority.ROUTINE,
        lat=40.7128,
        lon=-74.0060,
        estimated_hours=2
    )

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
