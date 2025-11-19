# database.py - COMPLETE VERSION
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
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers"""
        return self.db.query(Customer).all()
    
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
    
    def get_technician(self, tech_id: int) -> Optional[Technician]:
        """Get technician by ID"""
        return self.db.query(Technician).filter(Technician.id == tech_id).first()
    
    def get_all_technicians(self) -> List[Technician]:
        """Get all active technicians"""
        return self.db.query(Technician).filter(Technician.active == True).all()
    
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
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        return self.db.query(Job).all()
    
    def get_pending_jobs(self) -> List[Job]:
        """Get all unassigned jobs, sorted by priority and submission time"""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.EMERGENCY: 1,
            Priority.URGENT: 2,
            Priority.ROUTINE: 3
        }
        
        jobs = self.db.query(Job).filter(
            Job.status == JobStatus.PENDING
        ).all()
        
        jobs.sort(key=lambda j: (priority_order.get(j.priority, 99), j.submitted_at))
        
        return jobs
    
    def assign_job(self, job_id: int, tech_id: int, travel_time: float, 
                   distance: float, match_score: float) -> Assignment:
        """Assign a job to a technician"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.ASSIGNED
        job.assigned_to = tech_id
        job.assigned_at = datetime.utcnow()
        job.estimated_arrival = datetime.utcnow() + timedelta(hours=travel_time)
        
        tech = self.db.query(Technician).filter(Technician.id == tech_id).first()
        tech.free_at = datetime.utcnow() + timedelta(hours=travel_time + job.estimated_hours)
        
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
        """Mark job as started"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        
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
        
        tech = self.db.query(Technician).filter(Technician.id == job.assigned_to).first()
        tech.free_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def cancel_job(self, job_id: int) -> Job:
        """Cancel a job"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.CANCELLED
        
        if job.assigned_to:
            tech = self.db.query(Technician).filter(Technician.id == job.assigned_to).first()
            tech.free_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    # ========== SEARCH & FILTER ==========
    
    def search_jobs(self, 
                    customer_name: Optional[str] = None,
                    status: Optional[JobStatus] = None,
                    priority: Optional[Priority] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    skip: int = 0,
                    limit: int = 100) -> List[Job]:
        """Search jobs with filters and pagination"""
        query = self.db.query(Job)
        
        if customer_name:
            query = query.join(Customer).filter(
                Customer.name.ilike(f"%{customer_name}%")
            )
        
        if status:
            query = query.filter(Job.status == status)
        
        if priority:
            query = query.filter(Job.priority == priority)
        
        if start_date:
            query = query.filter(Job.submitted_at >= start_date)
        if end_date:
            query = query.filter(Job.submitted_at <= end_date)
        
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def search_customers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Search customers by name, phone, or address"""
        query = self.db.query(Customer).filter(
            (Customer.name.ilike(f"%{search_term}%")) |
            (Customer.phone.ilike(f"%{search_term}%")) |
            (Customer.address.ilike(f"%{search_term}%"))
        ).offset(skip).limit(limit)
        
        return query.all()
    
    def get_jobs_by_customer(self, customer_id: int) -> List[Job]:
        """Get all jobs for a specific customer"""
        return self.db.query(Job).filter(Job.customer_id == customer_id).order_by(Job.submitted_at.desc()).all()
    
    def get_jobs_by_tech(self, tech_id: int) -> List[Job]:
        """Get all jobs assigned to a specific technician"""
        return self.db.query(Job).filter(Job.assigned_to == tech_id).order_by(Job.assigned_at.desc()).all()
    
    # ========== AUTO-ASSIGNMENT ==========
    
    def auto_assign_job(self, job_id: int) -> Optional[Assignment]:
        """Automatically assign job to best available technician"""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.PENDING:
            return None
        
        available_techs = self.get_technicians_with_skills(job.required_skills)
        available_techs = [t for t in available_techs if t.free_at <= datetime.utcnow()]
        
        if not available_techs:
            return None
        
        best_tech = None
        best_score = -1
        best_distance = 0
        
        for tech in available_techs:
            distance = self.calculate_distance(
                tech.current_latitude or 0,
                tech.current_longitude or 0,
                job.latitude,
                job.longitude
            )
            
            skill_match = len(set(tech.skills) & set(job.required_skills)) / len(job.required_skills)
            skill_score = skill_match * 2
            
            distance_score = max(0, 2 - (distance / 25))
            
            priority_bonus = 1.0 if job.priority in [Priority.CRITICAL, Priority.EMERGENCY] else 0.5
            
            has_advanced_cert = any(cert in tech.certifications for cert in ["EPA_608_Universal", "NATE_Certified"])
            cert_bonus = 1.0 if has_advanced_cert else 0.5
            
            total_score = skill_score + distance_score + priority_bonus + cert_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_tech = tech
                best_distance = distance
        
        if best_tech:
            travel_time = self.calculate_travel_time(best_distance)
            return self.assign_job(job_id, best_tech.id, travel_time, best_distance, best_score)
        
        return None
    
    def auto_assign_all_pending(self) -> dict:
        """Auto-assign all pending jobs"""
        pending_jobs = self.get_pending_jobs()
        assigned = 0
        failed = 0
        failed_jobs = []
        
        for job in pending_jobs:
            assignment = self.auto_assign_job(job.id)
            if assignment:
                assigned += 1
            else:
                failed += 1
                failed_jobs.append({
                    "job_id": job.id,
                    "title": job.title,
                    "reason": "No available technician with required skills"
                })
        
        return {
            "total_pending": len(pending_jobs),
            "assigned": assigned,
            "failed": failed,
            "failed_jobs": failed_jobs
        }
    
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
        R = 3959
        
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
    
    # ========== METRICS ==========
    
    def get_sla_metrics(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        """Get SLA performance metrics"""
        query = self.db.query(Job).filter(Job.status == JobStatus.COMPLETED)
        
        if start_date:
            query = query.filter(Job.completed_at >= start_date)
        if end_date:
            query = query.filter(Job.completed_at <= end_date)
        
        completed_jobs = query.all()
        
        if not completed_jobs:
            return {
                "total_jobs": 0,
                "sla_met": 0,
                "sla_violated": 0,
                "sla_compliance_rate": 0.0,
                "avg_response_time_hours": 0.0
            }
        
        sla_met = sum(1 for j in completed_jobs if j.sla_met)
        sla_violated = len(completed_jobs) - sla_met
        
        response_times = [j.response_time_hours for j in completed_jobs if j.response_time_hours]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_jobs": len(completed_jobs),
            "sla_met": sla_met,
            "sla_violated": sla_violated,
            "sla_compliance_rate": round((sla_met / len(completed_jobs)) * 100, 2),
            "avg_response_time_hours": round(avg_response, 2)
        }
    
    def get_dashboard_stats(self) -> dict:
        """Get summary statistics for dashboard"""
        total_jobs = len(self.db.query(Job).all())
        pending_jobs = len(self.get_pending_jobs())
        
        assigned_jobs = self.db.query(Job).filter(Job.status == JobStatus.ASSIGNED).count()
        in_progress_jobs = self.db.query(Job).filter(Job.status == JobStatus.IN_PROGRESS).count()
        completed_jobs = self.db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        total_techs = len(self.get_all_technicians())
        available_techs = len(self.get_available_technicians())
        
        sla_metrics = self.get_sla_metrics()
        
        emergency_count = self.db.query(Job).filter(Job.priority == Priority.EMERGENCY).count()
        urgent_count = self.db.query(Job).filter(Job.priority == Priority.URGENT).count()
        routine_count = self.db.query(Job).filter(Job.priority == Priority.ROUTINE).count()
        
        return {
            "jobs": {
                "total": total_jobs,
                "pending": pending_jobs,
                "assigned": assigned_jobs,
                "in_progress": in_progress_jobs,
                "completed": completed_jobs,
                "by_priority": {
                    "emergency": emergency_count,
                    "urgent": urgent_count,
                    "routine": routine_count
                }
            },
            "technicians": {
                "total": total_techs,
                "available": available_techs,
                "busy": total_techs - available_techs
            },
            "sla": sla_metrics
        }