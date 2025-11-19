# database.py - MINIMAL WORKING VERSION
from sqlalchemy.orm import Session
from backend.models import Customer, Technician, Job, Assignment, Priority, JobStatus
from datetime import datetime, timedelta
from typing import List, Optional
import math

class DatabaseHelper:
    def __init__(self, session: Session):
        self.db = session
    
    def create_customer(self, name: str, phone: str, address: str, lat: float, lon: float, **kwargs):
        customer = Customer(name=name, phone=phone, address=address, latitude=lat, longitude=lon, **kwargs)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def get_customer(self, customer_id: int):
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_all_customers(self):
        return self.db.query(Customer).all()
    
    def create_technician(self, name: str, phone: str, skills: List[str], **kwargs):
        tech = Technician(name=name, phone=phone, skills=skills, free_at=datetime.utcnow(), **kwargs)
        self.db.add(tech)
        self.db.commit()
        self.db.refresh(tech)
        return tech
    
    def get_technician(self, tech_id: int):
        return self.db.query(Technician).filter(Technician.id == tech_id).first()
    
    def get_all_technicians(self):
        return self.db.query(Technician).filter(Technician.active == True).all()
    
    def get_available_technicians(self, current_time: datetime = None):
        if current_time is None:
            current_time = datetime.utcnow()
        return self.db.query(Technician).filter(Technician.active == True, Technician.free_at <= current_time).all()
    
    def get_technicians_with_skills(self, required_skills: List[str]):
        techs = self.db.query(Technician).filter(Technician.active == True).all()
        return [t for t in techs if any(skill in t.skills for skill in required_skills)]
    
    def create_job(self, customer_id: int, title: str, required_skills: List[str], priority: Priority, lat: float, lon: float, estimated_hours: float, **kwargs):
        job = Job(customer_id=customer_id, title=title, required_skills=required_skills, priority=priority, latitude=lat, longitude=lon, estimated_hours=estimated_hours, status=JobStatus.PENDING, **kwargs)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_job(self, job_id: int):
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_all_jobs(self):
        return self.db.query(Job).all()
    
    def get_pending_jobs(self):
        priority_order = {Priority.CRITICAL: 0, Priority.EMERGENCY: 1, Priority.URGENT: 2, Priority.ROUTINE: 3}
        jobs = self.db.query(Job).filter(Job.status == JobStatus.PENDING).all()
        jobs.sort(key=lambda j: (priority_order.get(j.priority, 99), j.submitted_at))
        return jobs
    
    def assign_job(self, job_id: int, tech_id: int, travel_time: float, distance: float, match_score: float):
        job = self.db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.ASSIGNED
        job.assigned_to = tech_id
        job.assigned_at = datetime.utcnow()
        job.estimated_arrival = datetime.utcnow() + timedelta(hours=travel_time)
        
        tech = self.db.query(Technician).filter(Technician.id == tech_id).first()
        tech.free_at = datetime.utcnow() + timedelta(hours=travel_time + job.estimated_hours)
        
        assignment = Assignment(job_id=job_id, tech_id=tech_id, distance_miles=distance, travel_time_hours=travel_time, match_score=match_score)
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def auto_assign_job(self, job_id: int):
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
            distance = self.calculate_distance(tech.current_latitude or 0, tech.current_longitude or 0, job.latitude, job.longitude)
            skill_score = len(set(tech.skills) & set(job.required_skills)) / len(job.required_skills) * 2
            distance_score = max(0, 2 - (distance / 25))
            priority_bonus = 1.0 if job.priority in [Priority.CRITICAL, Priority.EMERGENCY] else 0.5
            cert_bonus = 1.0 if any(c in tech.certifications for c in ["EPA_608_Universal", "NATE_Certified"]) else 0.5
            total_score = skill_score + distance_score + priority_bonus + cert_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_tech = tech
                best_distance = distance
        
        if best_tech:
            travel_time = self.calculate_travel_time(best_distance)
            return self.assign_job(job_id, best_tech.id, travel_time, best_distance, best_score)
        
        return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float):
        R = 3959
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def calculate_travel_time(self, distance_miles: float, avg_speed_mph: float = 30):
        return distance_miles / avg_speed_mph
    
    def start_job(self, job_id: int):
        """Mark job as started"""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.IN_PROGRESS
            job.started_at = datetime.utcnow()
            job.response_time_hours = (job.started_at - job.submitted_at).total_seconds() / 3600
            self.db.commit()
            self.db.refresh(job)
        return job
    
    def complete_job(self, job_id: int, actual_hours: float):
        """Mark job as completed"""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.actual_hours = actual_hours
            if job.assigned_to:
                tech = self.get_technician(job.assigned_to)
                if tech:
                    tech.free_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job
    
    def cancel_job(self, job_id: int):
        """Cancel a job"""
        job = self.get_job(job_id)
        if job:
            job.status = JobStatus.CANCELLED
            if job.assigned_to:
                tech = self.get_technician(job.assigned_to)
                if tech:
                    tech.free_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job
    
    def update_technician(self, tech_id: int, **kwargs):
        """Update technician"""
        tech = self.get_technician(tech_id)
        if tech:
            for key, value in kwargs.items():
                if hasattr(tech, key):
                    setattr(tech, key, value)
            self.db.commit()
            self.db.refresh(tech)
        return tech
    
    def update_tech_location(self, tech_id: int, lat: float, lon: float):
        """Update tech location"""
        return self.update_technician(tech_id, current_latitude=lat, current_longitude=lon)
    
    def deactivate_technician(self, tech_id: int):
        """Deactivate a technician"""
        tech = self.update_technician(tech_id, active=False)
        return tech is not None
    
    def get_jobs_by_customer(self, customer_id: int):
        """Get jobs for a customer"""
        return self.db.query(Job).filter(Job.customer_id == customer_id).order_by(Job.submitted_at.desc()).all()
    
    def get_jobs_by_tech(self, tech_id: int):
        """Get jobs for a tech"""
        return self.db.query(Job).filter(Job.assigned_to == tech_id).order_by(Job.assigned_at.desc()).all()
    
    def search_jobs(self, customer_name: Optional[str] = None, status: Optional[JobStatus] = None, 
                   priority: Optional[Priority] = None, skip: int = 0, limit: int = 100):
        """Search jobs with filters"""
        query = self.db.query(Job)
        if customer_name:
            query = query.join(Customer).filter(Customer.name.ilike(f"%{customer_name}%"))
        if status:
            query = query.filter(Job.status == status)
        if priority:
            query = query.filter(Job.priority == priority)
        return query.offset(skip).limit(limit).all()
    
    def auto_assign_all_pending(self):
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
                failed_jobs.append({"job_id": job.id, "title": job.title, "reason": "No available technician"})
        
        return {"total_pending": len(pending_jobs), "assigned": assigned, "failed": failed, "failed_jobs": failed_jobs}
    
    def get_sla_metrics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """Get SLA metrics"""
        query = self.db.query(Job).filter(Job.status == JobStatus.COMPLETED)
        if start_date:
            query = query.filter(Job.completed_at >= start_date)
        if end_date:
            query = query.filter(Job.completed_at <= end_date)
        
        completed_jobs = query.all()
        if not completed_jobs:
            return {"total_jobs": 0, "sla_met": 0, "sla_violated": 0, "sla_compliance_rate": 0.0, "avg_response_time_hours": 0.0}
        
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
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        total_jobs = len(self.get_all_jobs())
        pending_jobs = len(self.get_pending_jobs())
        assigned_jobs = self.db.query(Job).filter(Job.status == JobStatus.ASSIGNED).count()
        in_progress_jobs = self.db.query(Job).filter(Job.status == JobStatus.IN_PROGRESS).count()
        completed_jobs = self.db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
        
        total_techs = len(self.get_all_technicians())
        available_techs = len(self.get_available_technicians())
        
        return {
            "jobs": {
                "total": total_jobs,
                "pending": pending_jobs,
                "assigned": assigned_jobs,
                "in_progress": in_progress_jobs,
                "completed": completed_jobs,
            },
            "technicians": {
                "total": total_techs,
                "available": available_techs,
                "busy": total_techs - available_techs
            }
        }
    
    def get_tech_performance(self, tech_id: int):
        """Get tech performance metrics"""
        tech = self.get_technician(tech_id)
        if not tech:
            return None
        
        jobs = self.get_jobs_by_tech(tech_id)
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED]
        
        if not completed_jobs:
            return {
                "tech_id": tech_id,
                "tech_name": tech.name,
                "total_jobs": 0,
                "completed_jobs": 0,
                "avg_completion_time": 0,
                "sla_compliance_rate": 0
            }
        
        total_hours = sum(j.actual_hours or j.estimated_hours for j in completed_jobs)
        avg_hours = total_hours / len(completed_jobs)
        sla_met_count = sum(1 for j in completed_jobs if j.sla_met)
        sla_rate = (sla_met_count / len(completed_jobs)) * 100
        
        return {
            "tech_id": tech_id,
            "tech_name": tech.name,
            "total_jobs": len(jobs),
            "completed_jobs": len(completed_jobs),
            "avg_completion_time_hours": round(avg_hours, 2),
            "sla_compliance_rate": round(sla_rate, 2),
            "total_hours_worked": round(total_hours, 2)
        }