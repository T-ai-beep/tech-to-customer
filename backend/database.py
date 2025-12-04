# backend/database.py
"""
Complete DatabaseHelper class for HVAC Dispatch System
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from math import radians, cos, sin, sqrt, atan2
from typing import List, Optional, Dict, Any
import logging

from backend.models import (
    Customer, Technician, Job, Assignment,
    Priority, JobStatus, JobFinancial, JobPart,
    TechSkillLevel, TechInventory
)

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """Centralized database operations for HVAC dispatch system"""
    
    def __init__(self, session: Session):
        self.db = session
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two lat/lon points in miles"""
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return 0.0
            
        R = 3958.8
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    # ============================================================================
    # CUSTOMER OPERATIONS
    # ============================================================================
    
    def create_customer(
        self, 
        name: str, 
        phone: str, 
        address: str, 
        lat: float, 
        lon: float,
        email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Customer:
        """Create a new customer"""
        try:
            customer = Customer(
                name=name,
                phone=phone,
                address=address,
                lat=lat,
                lon=lon,
                email=email,
                notes=notes
            )
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            logger.info(f"Created customer: {customer.id} - {customer.name}")
            return customer
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating customer: {e}")
            raise
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers"""
        return self.db.query(Customer).all()
    
    # ============================================================================
    # TECHNICIAN OPERATIONS
    # ============================================================================
    
    def create_technician(
        self,
        name: str,
        phone: str,
        skills: List[str],
        certifications: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None,
        shift_start: int = 8,
        shift_end: int = 17,
        on_call: bool = False,
        current_lat: Optional[float] = None,
        current_lon: Optional[float] = None
    ) -> Technician:
        """Create a new technician"""
        try:
            tech = Technician(
                name=name,
                phone=phone,
                skills=skills,
                certifications=certifications or [],
                equipment=equipment or [],
                shift_start=shift_start,
                shift_end=shift_end,
                on_call=on_call,
                current_lat=current_lat,
                current_lon=current_lon,
                active=True
            )
            self.db.add(tech)
            self.db.commit()
            self.db.refresh(tech)
            logger.info(f"Created technician: {tech.id} - {tech.name}")
            return tech
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating technician: {e}")
            raise
    
    def get_technician(self, tech_id: int) -> Optional[Technician]:
        """Get technician by ID"""
        return self.db.query(Technician).filter(Technician.id == tech_id).first()
    
    def get_all_technicians(self) -> List[Technician]:
        """Get all technicians"""
        return self.db.query(Technician).all()
    
    def get_available_technicians(self) -> List[Technician]:
        """Get technicians that are currently available"""
        now = datetime.utcnow()
        return self.db.query(Technician).filter(
            Technician.active == True,
            or_(
                Technician.free_at == None,
                Technician.free_at <= now
            )
        ).all()
    
    def update_tech_location(self, tech_id: int, lat: float, lon: float) -> bool:
        """Update technician's current location"""
        try:
            tech = self.get_technician(tech_id)
            if tech:
                tech.current_lat = lat
                tech.current_lon = lon
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating tech location: {e}")
            return False
    
    # ============================================================================
    # JOB OPERATIONS
    # ============================================================================
    
    def create_job(
        self,
        customer_id: int,
        title: str,
        required_skills: List[str],
        priority: Priority,
        lat: float,
        lon: float,
        estimated_hours: float,
        description: Optional[str] = None,
        address: Optional[str] = None,
        equipment_details: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create a new job"""
        try:
            job = Job(
                customer_id=customer_id,
                title=title,
                description=description,
                required_skills=required_skills,
                priority=priority,
                status=JobStatus.PENDING,
                address=address,
                lat=lat,
                lon=lon,
                estimated_hours=estimated_hours,
                equipment_details=equipment_details or {},
                submitted_at=datetime.utcnow()
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Created job: {job.id} - {job.title} ({job.priority.value})")
            return job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        return self.db.query(Job).filter(Job.id == job_id).first()
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        return self.db.query(Job).all()
    
    def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs"""
        return self.db.query(Job).filter(Job.status == JobStatus.PENDING).all()
    
    def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get jobs by status"""
        return self.db.query(Job).filter(Job.status == status).all()
    
    def get_jobs_by_priority(self, priority: Priority) -> List[Job]:
        """Get jobs by priority"""
        return self.db.query(Job).filter(Job.priority == priority).all()
    
    # ============================================================================
    # JOB LIFECYCLE OPERATIONS
    # ============================================================================
    
    def start_job(self, job_id: int) -> Optional[Job]:
        """Mark a job as started"""
        try:
            job = self.get_job(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return None
            
            if job.status != JobStatus.ASSIGNED:
                logger.warning(f"Job {job_id} is not in ASSIGNED state")
                return None
            
            job.status = JobStatus.IN_PROGRESS
            job.assigned_at = datetime.utcnow()
            
            # Calculate SLAelon musk
            
            if job.submitted_at:
                response_hours = (job.started_at - job.submitted_at).total_seconds() / 3600
                
                # Define SLA windows based on priority
                sla_windows = {
                    Priority.CRITICAL: 1,
                    Priority.EMERGENCY: 2,
                    Priority.URGENT: 8,
                    Priority.HIGH: 4,
                    Priority.ROUTINE: 24
                }
                sla_window = sla_windows.get(job.priority, 24)
                job.sla_met = response_hours <= sla_window
            
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Started job: {job_id}")
            return job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting job: {e}")
            raise
    
    def complete_job(self, job_id: int, actual_hours: float) -> Optional[Job]:
        """Mark a job as completed"""
        try:
            job = self.get_job(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return None
            
            if job.status != JobStatus.IN_PROGRESS:
                logger.warning(f"Job {job_id} is not in IN_PROGRESS state")
                return None
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.actual_hours = actual_hours
            
            # Free up the technician
            assignment = self.get_assignment_by_job(job_id)
            if assignment:
                tech = self.get_technician(assignment.tech_id)
                if tech:
                    tech.free_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Completed job: {job_id} in {actual_hours} hours")
            return job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error completing job: {e}")
            raise
    
    def cancel_job(self, job_id: int) -> Optional[Job]:
        """Cancel a job"""
        try:
            job = self.get_job(job_id)
            if not job:
                return None
            
            job.status = JobStatus.CANCELLED
            
            # Free up technician if assigned
            assignment = self.get_assignment_by_job(job_id)
            if assignment:
                tech = self.get_technician(assignment.tech_id)
                if tech:
                    tech.free_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Cancelled job: {job_id}")
            return job
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling job: {e}")
            raise
    
    # ============================================================================
    # ASSIGNMENT OPERATIONS
    # ============================================================================
    
     def auto_assign_job(self, job_id: int) -> Optional[Assignment]:
        """
        Auto-assign using advanced scoring engine
        """
        # Use local import to avoid circular dependency
        try:
            from backend.assignment_engine import AssignmentEngine
        except ImportError:
            # Fallback to simple assignment if engine not available
            return self._simple_assign_job(job_id)
        
        try:
            job = self.get_job(job_id)
            if not job or job.status != JobStatus.PENDING:
                return None
            
            # Use assignment engine
            engine = AssignmentEngine(self.db)
            result = engine.find_best_technician(job_id)
            
            if not result:
                logger.warning(f"No qualified tech found for job {job_id}")
                return None
            
            best_tech, score, breakdown = result
            
            # Calculate travel metrics
            distance = self.haversine(
                job.lat or 0, job.lon or 0,
                best_tech.current_lat or 0,
                best_tech.current_lon or 0
            )
            travel_hours = distance / 30  # Assume 30 mph average
            
            # Create assignment
            now = datetime.utcnow()
            assignment = Assignment(
                job_id=job.id,
                tech_id=best_tech.id,
                distance_miles=distance,
                travel_time_hours=travel_hours,
                match_score=score,
                assigned_at=now
            )
            
            # Update job - ONLY update status, not started_at
            job.status = JobStatus.ASSIGNED
            
            # Update tech availability
            best_tech.free_at = now + timedelta(hours=travel_hours + (job.estimated_hours or 0))
            
            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)
            
            logger.info(
                f"Assigned job {job_id} to {best_tech.name} | "
                f"Score: {score:.2f} | Distance: {distance:.1f}mi"
            )
            
            return assignment
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in auto_assign_job: {e}")
            return None
    
    def _simple_assign_job(self, job_id: int) -> Optional[Assignment]:
        """Simple assignment fallback without engine"""
        try:
            job = self.get_job(job_id)
            if not job or job.status != JobStatus.PENDING:
                return None
            
            # Get available technicians
            available_techs = self.get_available_technicians()
            if not available_techs:
                return None
            
            # Find first tech with matching skills
            job_skills = set(job.required_skills or [])
            for tech in available_techs:
                tech_skills = set(tech.skills or [])
                if job_skills.issubset(tech_skills):
                    # Calculate distance
                    distance = self.haversine(
                        job.lat or 0, job.lon or 0,
                        tech.current_lat or 0,
                        tech.current_lon or 0
                    )
                    travel_hours = distance / 30
                    
                    # Create assignment
                    now = datetime.utcnow()
                    assignment = Assignment(
                        job_id=job.id,
                        tech_id=tech.id,
                        distance_miles=distance,
                        travel_time_hours=travel_hours,
                        match_score=0.5,  # Default score
                        assigned_at=now
                    )
                    
                    # Update job
                    job.status = JobStatus.ASSIGNED
                    tech.free_at = now + timedelta(hours=travel_hours + (job.estimated_hours or 0))
                    
                    self.db.add(assignment)
                    self.db.commit()
                    self.db.refresh(assignment)
                    
                    logger.info(f"Simple assigned job {job_id} to {tech.name}")
                    return assignment
            
            return None
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in simple_assign_job: {e}")
            return None
    
    # ============================================================================
    # DASHBOARD & METRICS
    # ============================================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            total_jobs = self.db.query(Job).count()
            pending_jobs = self.db.query(Job).filter(Job.status == JobStatus.PENDING).count()
            in_progress_jobs = self.db.query(Job).filter(Job.status == JobStatus.IN_PROGRESS).count()
            completed_jobs = self.db.query(Job).filter(Job.status == JobStatus.COMPLETED).count()
            
            active_techs = self.db.query(Technician).filter(Technician.active == True).count()
            available_techs = len(self.get_available_technicians())
            
            # SLA violations today
            today = datetime.utcnow() - timedelta(days=1)
            sla_violations = self.db.query(Job).filter(
                Job.sla_met == False,
                Job.submitted_at >= today
            ).count()
            
            return {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "in_progress_jobs": in_progress_jobs,
                "completed_jobs": completed_jobs,
                "active_technicians": active_techs,
                "available_technicians": available_techs,
                "sla_violations_today": sla_violations
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    def get_sla_metrics(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get SLA performance metrics for a date range"""
        try:
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
                    "sla_compliance_rate": 0.0
                }
            
            sla_met = sum(1 for j in completed_jobs if j.sla_met)
            sla_violated = len(completed_jobs) - sla_met
            compliance_rate = (sla_met / len(completed_jobs)) * 100 if completed_jobs else 0
            
            return {
                "total_jobs": len(completed_jobs),
                "sla_met": sla_met,
                "sla_violated": sla_violated,
                "sla_compliance_rate": round(compliance_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting SLA metrics: {e}")
            return {}