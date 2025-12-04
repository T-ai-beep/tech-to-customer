"""
Calculate job profitability and financial metrics
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.models import Job, JobFinancial, JobPart, Technician, JobStatus, Assignment

import logging

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Calculate job-level financial metrics"""
    
    def __init__(self, session: Session):
        self.db = session
        
        # Default rates
        self.default_fuel_cost_per_mile = 0.65
        self.default_overhead_rate = 0.15  # 15% of revenue
    
    def calculate_job_financials(self, job_id: int) -> Optional[JobFinancial]:
        """
        Calculate complete financial breakdown for a job
        Must be called AFTER job is completed
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        
        if not job or job.status != JobStatus.COMPLETED:
            logger.warning(f"Job {job_id} not completed, cannot calculate financials")
            return None
        
        # Get technician through assignment
        assignment = self.db.query(Assignment).filter(
            Assignment.job_id == job_id
        ).first()
        
        if not assignment:
            logger.error(f"No assignment found for job {job_id}")
            return None
            
        tech = self.db.query(Technician).filter(
            Technician.id == assignment.tech_id
        ).first()
        
        if not tech:
            logger.error(f"No tech found for job {job_id}")
            return None
        
        # ============ REVENUE ============
        
        # Labor revenue (use tech's hourly rate)
        labor_rate = tech.hourly_rate
        labor_hours = job.actual_hours or job.estimated_hours or 0
        labor_revenue = labor_rate * labor_hours
        
        # Parts revenue
        parts = self.db.query(JobPart).filter(JobPart.job_id == job_id).all()
        parts_revenue = sum(
            p.unit_price * p.quantity_used for p in parts
        )
        
        total_revenue = labor_revenue + parts_revenue
        
        # ============ COSTS ============
        
        # Labor cost (use tech's hourly cost)
        tech_cost = tech.hourly_cost
        labor_cost = tech_cost * labor_hours
        
        # Parts cost
        parts_cost = sum(
            p.unit_cost * p.quantity_used for p in parts
        )
        
        # Fuel cost
        distance = assignment.distance_miles or 0
        fuel_cost = distance * self.default_fuel_cost_per_mile
        
        # Overhead (allocated)
        overhead_cost = total_revenue * self.default_overhead_rate
        
        total_cost = labor_cost + parts_cost + fuel_cost + overhead_cost
        
        # ============ PROFITABILITY ============
        
        gross_profit = total_revenue - total_cost
        gross_margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Create or update financial record
        financial = self.db.query(JobFinancial).filter(
            JobFinancial.job_id == job_id
        ).first()
        
        if not financial:
            financial = JobFinancial(job_id=job_id)
            self.db.add(financial)
        
        # Update all fields
        financial.labor_rate_per_hour = labor_rate
        financial.labor_hours_charged = labor_hours
        financial.labor_revenue = labor_revenue
        financial.parts_revenue = parts_revenue
        financial.total_revenue = total_revenue
        
        financial.tech_hourly_cost = tech_cost
        financial.labor_cost = labor_cost
        financial.parts_cost = parts_cost
        financial.fuel_cost = fuel_cost
        financial.overhead_cost = overhead_cost
        financial.total_cost = total_cost
        
        financial.gross_profit = gross_profit
        financial.gross_margin_pct = gross_margin_pct
        financial.calculated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(financial)
        
        logger.info(
            f"Job {job_id} financials: "
            f"Revenue ${total_revenue:.2f}, "
            f"Profit ${gross_profit:.2f} ({gross_margin_pct:.1f}%)"
        )
        
        return financial
    
    def calculate_profitability_by_job_type(self) -> List[Dict[str, any]]:
        """
        Analyze which types of jobs are most profitable
        """
        jobs = self.db.query(Job).filter(
            Job.status == JobStatus.COMPLETED
        ).all()
        
        # Group by title (proxy for job type)
        job_types: Dict[str, Dict[str, any]] = {}
        
        for job in jobs:
            if not job.financial:
                continue
            
            job_type = job.title or "Unknown"
            
            if job_type not in job_types:
                job_types[job_type] = {
                    "count": 0,
                    "total_revenue": 0.0,
                    "total_profit": 0.0
                }
            
            job_types[job_type]["count"] += 1
            job_types[job_type]["total_revenue"] += job.financial.total_revenue
            job_types[job_type]["total_profit"] += job.financial.gross_profit
        
        # Calculate averages
        results = []
        for job_type, data in job_types.items():
            if data["count"] > 0:
                avg_revenue = data["total_revenue"] / data["count"]
                avg_profit = data["total_profit"] / data["count"]
                avg_margin = (avg_profit / avg_revenue * 100) if avg_revenue > 0 else 0
                
                results.append({
                    "job_type": job_type,
                    "count": data["count"],
                    "avg_revenue": round(avg_revenue, 2),
                    "avg_profit": round(avg_profit, 2),
                    "avg_margin_pct": round(avg_margin, 1)
                })
        
        # Sort by profitability
        results.sort(key=lambda x: x["avg_margin_pct"], reverse=True)
        
        return results