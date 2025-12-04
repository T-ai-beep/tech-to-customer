"""
Calculate and track technician performance metrics
"""
from typing import Dict, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from backend.models import (
    Technician, Job, JobStatus, TechPerformanceMetric,
    JobFinancial, Assignment
)

import logging

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Track and calculate tech performance metrics"""
    
    def __init__(self, session: Session):
        self.db = session
    
    def calculate_daily_performance(
        self, 
        tech_id: int, 
        target_date: date
    ) -> TechPerformanceMetric:
        """
        Calculate all performance metrics for a tech for a specific day
        """
        # Query all assignments for this tech on this day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        assignments = self.db.query(Assignment).filter(
            Assignment.tech_id == tech_id,
            Assignment.assigned_at >= start_of_day,
            Assignment.assigned_at <= end_of_day
        ).options(joinedload(Assignment.job)).all()
        
        # Get jobs from assignments
        jobs = [ass.job for ass in assignments if ass.job]
        
        # Initialize counters
        shift_hours = 8.0
        billable_hours = 0
        drive_time_hours = 0
        jobs_completed = 0
        jobs_cancelled = 0
        callbacks = 0
        revenue_generated = 0
        
        for assignment in assignments:
            job = assignment.job
            if not job:
                continue
                
            try:
                if job.status == JobStatus.COMPLETED:
                    jobs_completed += 1
                    billable_hours += job.actual_hours or job.estimated_hours or 0
                    
                    # Check if callback
                    if job.is_callback:
                        callbacks += 1
                    
                    # Add revenue
                    if job.financial:
                        revenue_generated += job.financial.total_revenue or 0
                
                elif job.status == JobStatus.CANCELLED:
                    jobs_cancelled += 1
                    
                # Add travel time
                drive_time_hours += assignment.travel_time_hours or 0
                    
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {e}")
        
        # Calculate idle time
        idle_time_hours = max(0, shift_hours - billable_hours - drive_time_hours)
        
        # Calculate rates
        utilization_rate = (billable_hours / shift_hours) if shift_hours > 0 else 0
        
        first_time_fix_rate = 0
        if jobs_completed > 0:
            successful_fixes = jobs_completed - callbacks
            first_time_fix_rate = successful_fixes / jobs_completed
        
        avg_job_value = 0
        if jobs_completed > 0:
            avg_job_value = revenue_generated / jobs_completed
        
        # Create or update metric record
        metric = self.db.query(TechPerformanceMetric).filter(
            TechPerformanceMetric.tech_id == tech_id,
            func.date(TechPerformanceMetric.date) == target_date
        ).first()
        
        if not metric:
            metric = TechPerformanceMetric(
                tech_id=tech_id,
                date=datetime.combine(target_date, datetime.min.time())
            )
            self.db.add(metric)
        
        # Update all fields
        metric.shift_hours = shift_hours
        metric.billable_hours = billable_hours
        metric.drive_time_hours = drive_time_hours
        metric.idle_time_hours = idle_time_hours
        metric.jobs_completed = jobs_completed
        metric.jobs_cancelled = jobs_cancelled
        metric.callbacks = callbacks
        metric.revenue_generated = revenue_generated
        metric.avg_job_value = avg_job_value
        metric.utilization_rate = utilization_rate
        metric.first_time_fix_rate = first_time_fix_rate
        
        self.db.commit()
        self.db.refresh(metric)
        
        logger.info(
            f"Tech {tech_id} performance on {target_date}: "
            f"Util: {utilization_rate:.1%}, "
            f"Rev: ${revenue_generated:.0f}, "
            f"FTF: {first_time_fix_rate:.1%}"
        )
        
        return metric
    
    def calculate_team_performance(self, target_date: date) -> Dict:
        """
        Calculate aggregate team performance for a day
        """
        metrics = self.db.query(TechPerformanceMetric).filter(
            func.date(TechPerformanceMetric.date) == target_date
        ).all()
        
        if not metrics:
            return {
                "date": target_date.isoformat(),
                "tech_count": 0,
                "total_revenue": 0,
                "avg_utilization": 0,
                "avg_ftf_rate": 0
            }
        
        total_revenue = sum(m.revenue_generated for m in metrics)
        avg_utilization = sum(m.utilization_rate for m in metrics) / len(metrics)
        avg_ftf = sum(m.first_time_fix_rate for m in metrics) / len(metrics)
        
        return {
            "date": target_date.isoformat(),
            "tech_count": len(metrics),
            "total_revenue": round(total_revenue, 2),
            "avg_utilization": round(avg_utilization, 3),
            "avg_ftf_rate": round(avg_ftf, 3),
            "metrics": [
                {
                    "tech_id": m.tech_id,
                    "utilization": m.utilization_rate,
                    "revenue": m.revenue_generated,
                    "jobs": m.jobs_completed
                }
                for m in metrics
            ]
        }
    
    def get_tech_performance_history(
        self, 
        tech_id: int, 
        days: int = 30
    ) -> List[TechPerformanceMetric]:
        """
        Get performance history for a tech
        """
        start_date = date.today() - timedelta(days=days)
        
        return self.db.query(TechPerformanceMetric).filter(
            TechPerformanceMetric.tech_id == tech_id,
            TechPerformanceMetric.date >= start_date
        ).order_by(TechPerformanceMetric.date.desc()).all()