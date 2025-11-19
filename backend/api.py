# api.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import math
from backend.models import get_engine, get_session, Priority, JobStatus, Assignment
from backend.database import DatabaseHelper

app = FastAPI(
    title="HVAC Dispatch API",
    description="Complete API for HVAC technician scheduling and dispatch management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow WebSocket upgrades from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Database
engine = get_engine()
session = get_session(engine)
db = DatabaseHelper(session)

# ===================== REQUEST/RESPONSE MODELS =====================
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
    latitude: float
    longitude: float
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
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

class TechnicianResponse(BaseModel):
    id: int
    name: str
    phone: str
    skills: List[str]
    certifications: List[str]
    shift_start: int
    shift_end: int
    on_call: bool
    current_latitude: Optional[float]
    current_longitude: Optional[float]
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
    latitude: float
    longitude: float
    submitted_at: datetime
    assigned_to: Optional[int]
    estimated_hours: float
    sla_met: Optional[bool]

    class Config:
        from_attributes = True

# ===================== CONNECTION MANAGER =====================
class ConnectionManager:
    """Manage WebSocket connections by type"""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dispatchers": set(),
            "techs": set()  # all techs
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections.setdefault(client_type, set()).add(websocket)
        print(f"✅ {client_type} connected. Total: {len(self.active_connections[client_type])}")

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections.get(client_type, set()).discard(websocket)
        print(f"❌ {client_type} disconnected. Remaining: {len(self.active_connections.get(client_type, []))}")

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

    async def broadcast_to_all(self, message: dict):
        for client_type in self.active_connections:
            await self.broadcast(message, client_type)

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
        current_latitude=tech.current_latitude,
        current_longitude=tech.current_longitude
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

@app.get("/jobs/pending")
def get_pending_jobs():
    jobs = db.get_pending_jobs()
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

# ===================== JOB ASSIGNMENT + BROADCAST =====================
@app.post("/jobs/{job_id}/auto-assign")
async def auto_assign_job(job_id: int):
    assignment = db.auto_assign_job(job_id)
    if not assignment:
        raise HTTPException(status_code=400, detail="No available technician found")

    job = db.get_job(job_id)
    tech = db.get_technician(assignment.tech_id)

    # Broadcast to dispatchers
    await manager.broadcast({
        "type": "job_assigned",
        "job_id": job_id,
        "job_title": job.title,
        "tech_id": tech.id,
        "tech_name": tech.name,
        "distance_miles": assignment.distance_miles,
        "travel_time_minutes": assignment.travel_time_hours * 60,
        "estimated_arrival": job.estimated_arrival.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }, "dispatchers")

    # Broadcast to all techs
    await manager.broadcast({
        "type": "new_assignment",
        "job_id": job_id,
        "job_title": job.title,
        "customer_name": job.customer.name if job.customer else "Unknown",
        "address": job.address,
        "priority": job.priority.value,
        "estimated_hours": job.estimated_hours,
        "distance_miles": assignment.distance_miles,
        "timestamp": datetime.utcnow().isoformat()
    }, "techs")

    return {"message": "Job assigned and broadcasted", "assignment": assignment}

# ===================== JOB STATUS BROADCAST =====================
@app.put("/jobs/{job_id}/start")
async def start_job(job_id: int):
    job = db.start_job(job_id)
    job.priority = job.priority.value
    job.status = job.status.value
    await manager.broadcast({
        "type": "job_started",
        "job_id": job_id,
        "job_title": job.title,
        "tech_id": job.assigned_to,
        "started_at": job.started_at.isoformat(),
        "sla_met": job.sla_met,
        "timestamp": datetime.utcnow().isoformat()
    }, "dispatchers")
    return job

@app.put("/jobs/{job_id}/complete")
async def complete_job(job_id: int, actual_hours: float):
    job = db.complete_job(job_id, actual_hours)
    job.priority = job.priority.value
    job.status = job.status.value
    await manager.broadcast({
        "type": "job_completed",
        "job_id": job_id,
        "job_title": job.title,
        "tech_id": job.assigned_to,
        "completed_at": job.completed_at.isoformat(),
        "actual_hours": actual_hours,
        "sla_met": job.sla_met,
        "timestamp": datetime.utcnow().isoformat()
    }, "dispatchers")
    return job

# ===================== WEBSOCKETS =====================
@app.websocket("/ws/dispatcher")
async def websocket_dispatcher(websocket: WebSocket):
    await manager.connect(websocket, "dispatchers")
    try:
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connected to HVAC Dispatch",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong", "timestamp": datetime.utcnow().isoformat()}, websocket)
            elif message.get("type") == "request_update":
                jobs = db.get_pending_jobs()
                techs = db.get_available_technicians()
                await manager.send_personal_message({
                    "type": "full_update",
                    "data": {"pending_jobs": len(jobs), "available_techs": len(techs)},
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dispatchers")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, "dispatchers")

@app.websocket("/ws/tech/{tech_id}")
async def websocket_tech(websocket: WebSocket, tech_id: int):
    await manager.connect(websocket, "techs")
    try:
        await manager.send_personal_message({
            "type": "connected",
            "message": f"Connected as Tech {tech_id}",
            "tech_id": tech_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "location_update":
                lat = message.get("lat")
                lon = message.get("lon")
                tech = db.get_technician(tech_id)
                if tech:
                    tech.current_latitude = lat
                    tech.current_longitude = lon
                    db.db.commit()
                    await manager.broadcast({
                        "type": "tech_location_update",
                        "tech_id": tech_id,
                        "tech_name": tech.name,
                        "lat": lat,
                        "lon": lon,
                        "timestamp": datetime.utcnow().isoformat()
                    }, "dispatchers")
    except WebSocketDisconnect:
        manager.disconnect(websocket, "techs")
    except Exception as e:
        print(f"Tech WebSocket error: {e}")
        manager.disconnect(websocket, "techs")

# ===================== DASHBOARD & METRICS =====================
@app.get("/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    try:
        return db.get_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/sla")
async def dashboard_sla(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None)):
    """Get SLA metrics for a date range"""
    try:
        sd = None
        ed = None
        if start_date:
            sd = datetime.fromisoformat(start_date)
        if end_date:
            ed = datetime.fromisoformat(end_date)
        return db.get_sla_metrics(start_date=sd, end_date=ed)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format; use ISO8601")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/technicians/{tech_id}/performance")
async def technician_performance(tech_id: int = Path(..., gt=0)):
    """Get technician performance metrics"""
    try:
        perf = db.get_tech_performance(tech_id)
        if perf is None:
            raise HTTPException(status_code=404, detail=f"Technician {tech_id} not found")
        return perf
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===================== RUN SERVER =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
