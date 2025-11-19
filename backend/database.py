# database.py
from sqlalchemy.orm import Session
from models import Customer, Technician, Job, Assignment, Priority, JobStatus
from datetime import datetime, timedelta
from typing import List, Optional
import math

class DatabaseHelper:
    def __init__(self, session: Session):
        self.db = session
    
    # ========== CUSTOMER OPERATIONS ==========
    
    def create_customer(self, name: str, phone: str, address: str, 
                       lat: float, lon: float, **kwargs) -> Customer:
        """Create a new customer"""
        customer = Customer(
            name=name,
            phone=phone,
            address=address,
            latitude=lat,
            longitude=lon,
            **kwargs
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    # ========== TECHNICIAN OPERATIONS ==========
    
    def create_technician(self, name: str, phone: str, skills: List[str], **kwargs) -> Technician:
        """Create a new technician"""
        tech = Technician(
            name=name,
            phone=phone,
            skills=skills,
            free_at=datetime.utcnow(),
            **kwargs
        )
        self.db.add(tech)
        self.db.commit()
        self.db.refresh(tech)
        return tech
    
    def get_available_technicians(self, current_time: datetime = None) -> List[Technician]:
        """Get technicians who are currently available"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        return self.db.query(Technician).filter(
            Technician.active == True,
            Technician.free_at <= current_time
        ).all()
    
    def get_technicians_with_skills(self, required_skills: List[str]) -> List[Technician]:
        """Get technicians who have at least one required skill"""
        techs = self.db.query(Technician).filter(Technician.active == True).all()
        
        # Filter by skills (JSON contains check)
        matching_techs = []
        for tech in techs:
            if any(skill in tech.skills for skill in required_skills):
                matching_techs.append(tech)
        
        return matching_techs
    
    # ========== JOB OPERATIONS ==========
    
    def create_job(self, customer_id: int, title: str, required_skills: List[str],
                   priority: Priority, lat: float, lon: float, 
                   estimated_hours: float, **kwargs) -> Job:
        """Create a new job"""
        job = Job(
            customer_id=customer_id,
            title=title,
            required_skills=required_skills,
            priority=priority,
            latitude=lat,
            longitude=lon,
            estimated_hours=estimated_hours,
            status=JobStatus.PENDING,
            **kwargs
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_pending_jobs(self) -> List[Job]:
        """Get all unassigned jobs, sorted by priority and submission time"""
        return self.db.query(Job).filter(
            Job.status == JobStatus.PENDING
        ).order_by(
            Job.priority,  # Critical first, then emergency, urgent, routine
            Job.submitted_at  # Older jobs first within same priority
        ).all()
    
    def assign_job(self, job_id: int, tech_id: int, travel_time: float, 
                   distance: float, match_score: float) -> Assignment:
        """Assign a job to a technician"""
        # Update job
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.ASSIGNED
        job.assigned_to = tech_id
        job.assigned_at = datetime.utcnow()
        job.estimated_arrival = datetime.utcnow() + timedelta(hours=travel_time)
        
        # Update technician
        tech = self.db.query(Technician).filter(Technician.id == tech_id).first()
        tech.free_at = datetime.utcnow() + timedelta(hours=travel_time + job.estimated_hours)
        
        # Create assignment record
        assignment = Assignment(
            job_id=job_id,
            tech_id=tech_id,
            distance_miles=distance,
            travel_time_hours=travel_time,
            match_score=match_score
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def start_job(self, job_id: int) -> Job:
        """Mark job as started (tech clicked 'Start' in mobile app)"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        
        # Calculate SLA compliance
        job.response_time_hours = (job.started_at - job.submitted_at).total_seconds() / 3600
        job.sla_met = self.check_sla_met(job)
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def complete_job(self, job_id: int, actual_hours: float) -> Job:
        """Mark job as completed"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.actual_hours = actual_hours
        
        # Free up the technician
        tech = self.db.query(Technician).filter(Technician.id == job.assigned_to).first()
        tech.free_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    # ========== HELPER FUNCTIONS ==========
    
    def check_sla_met(self, job: Job) -> bool:
        """Check if job met SLA window"""
        SLA_WINDOWS = {
            Priority.CRITICAL: 1,
            Priority.EMERGENCY: 2,
            Priority.URGENT: 8,
            Priority.ROUTINE: 24
        }
        
        if not job.started_at:
            return False
        
        response_hours = job.response_time_hours
        sla_window = SLA_WINDOWS.get(job.priority, 24)
        
        return response_hours <= sla_window
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance in miles using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def calculate_travel_time(self, distance_miles: float, avg_speed_mph: float = 30) -> float:
        """Calculate travel time in hours"""
        return distance_miles / avg_speed_mph