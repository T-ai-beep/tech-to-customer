"""
Calculate and track technician performance metrics
"""
from typing import Dict, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    Technician, Job, JobStatus, TechPerformanceMetric,
    JobFinancial
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
        # Query all jobs for this tech on this day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        jobs = self.db.query(Job).filter(
            Job.assigned_to == tech_id,
            Job.assigned_at >= start_of_day,
            Job.assigned_at <= end_of_day
        ).all()
        
        # Initialize counters
        shift_hours = 8.0  # Standard shift
        billable_hours = 0
        drive_time_hours = 0
        jobs_completed = 0
        jobs_cancelled = 0
        callbacks = 0
        revenue_generated = 0
        
        for job in jobs:
            try:
                # Use .is_() for SQLAlchemy enum comparison instead of ==
                if job.status.is_(JobStatus.COMPLETED):  # type: ignore
                    jobs_completed += 1
                    billable_hours += job.actual_hours or job.estimated_hours
                    
                    # Check if callback
                    if job.is_callback:
                        callbacks += 1
                    
                    # Add revenue
                    if job.financial:
                        revenue_generated += job.financial.total_revenue or 0
                
                elif job.status.is_(JobStatus.CANCELLED):  # type: ignore
                    jobs_cancelled += 1
            except:
                pass
            
            # Calculate drive time from assignment record
            if job.assignment:
                drive_time_hours += job.assignment.travel_time_hours or 0
        
        # Calculate idle time
        idle_time_hours = shift_hours - billable_hours - drive_time_hours
        idle_time_hours = max(0, idle_time_hours)
        
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
        metric.shift_hours = shift_hours  # type: ignore
        metric.billable_hours = billable_hours  # type: ignore
        metric.drive_time_hours = drive_time_hours  # type: ignore
        metric.idle_time_hours = idle_time_hours  # type: ignore
        metric.jobs_completed = jobs_completed  # type: ignore
        metric.jobs_cancelled = jobs_cancelled  # type: ignore
        metric.callbacks = callbacks  # type: ignore
        metric.revenue_generated = revenue_generated  # type: ignore
        metric.avg_job_value = avg_job_value  # type: ignore
        metric.utilization_rate = utilization_rate  # type: ignore
        metric.first_time_fix_rate = first_time_fix_rate  # type: ignore
        
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
            "total_revenue": round(float(total_revenue), 2),  # type: ignore
            "avg_utilization": round(float(avg_utilization), 3),  # type: ignore
            "avg_ftf_rate": round(float(avg_ftf), 3),  # type: ignore
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