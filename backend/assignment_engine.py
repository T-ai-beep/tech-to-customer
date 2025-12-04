"""
Advanced job assignment engine with multi-factor scoring
"""
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from math import radians, cos, sin, sqrt, atan2
import logging

from backend.models import Job, Technician, TechSkillLevel, TechInventory, JobPart, Priority, JobStatus, TechPerformanceMetric

logger = logging.getLogger(__name__)


class AssignmentEngine:
    """
    Intelligent job assignment with multi-factor optimization
    
    Scoring factors:
    1. Skill match & proficiency (35%)
    2. Utilization balancing (25%)
    3. Geographic efficiency (20%)
    4. Parts availability (15%)
    5. Customer preference (5%)
    """
    
    def __init__(self, session: Session):
        self.db = session
        
        # Configurable weights
        self.weights = {
            'skill': 0.35,
            'utilization': 0.25,
            'geography': 0.20,
            'parts': 0.15,
            'customer': 0.05
        }
        
        # Priority multipliers
        self.priority_multipliers = {
            Priority.CRITICAL: 2.0,
            Priority.EMERGENCY: 1.5,
            Priority.URGENT: 1.2,
            Priority.ROUTINE: 1.0,
            Priority.HIGH: 1.1
        }
    
    def calculate_assignment_score(
        self, 
        tech: Technician, 
        job: Job
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate comprehensive assignment score
        
        Returns:
            (total_score, score_breakdown)
        """
        breakdown: Dict[str, Any] = {}
        
        # 1. SKILL SCORE (35%)
        breakdown['skill'] = self._score_skill_match(tech, job)
        
        # 2. UTILIZATION SCORE (25%)
        breakdown['utilization'] = self._score_utilization(tech, job)
        
        # 3. GEOGRAPHIC SCORE (20%)
        breakdown['geography'] = self._score_geography(tech, job)
        
        # 4. PARTS SCORE (15%)
        breakdown['parts'] = self._score_parts_availability(tech, job)
        
        # 5. CUSTOMER PREFERENCE SCORE (5%)
        breakdown['customer'] = self._score_customer_preference(tech, job)
        
        # Calculate weighted total
        total = sum(
            breakdown[factor] * self.weights[factor]
            for factor in self.weights.keys()
        )
        
        # Apply priority multiplier
        try:
            priority_enum = job.priority if isinstance(job.priority, Priority) else Priority.ROUTINE
        except:
            priority_enum = Priority.ROUTINE
        priority_multiplier = self.priority_multipliers.get(priority_enum, 1.0)
        total *= priority_multiplier
        
        breakdown['priority_multiplier'] = priority_multiplier
        breakdown['final_score'] = total
        
        return total, breakdown
    
    def _score_skill_match(self, tech: Technician, job: Job) -> float:
        """
        Score based on skill match AND proficiency level
        
        Returns 0.0 - 1.0
        """
        try:
            required_skills = job.required_skills if isinstance(job.required_skills, list) else []
        except:
            required_skills = []
            
        if len(required_skills) == 0:
            return 1.0
        
        # Get tech's skill levels
        tech_skills = {
            sk.skill_name: sk.proficiency_level 
            for sk in tech.skill_levels
        }
        
        total_score = 0
        for required_skill in required_skills:
            if required_skill not in tech_skills:
                # Missing required skill = disqualified
                return 0.0
            
            # Normalize proficiency (1-5 scale to 0-1)
            proficiency = tech_skills[required_skill]
            normalized = proficiency / 5.0
            total_score += normalized
        
        # Average proficiency across all required skills
        avg_score = total_score / len(required_skills)
        
        # Bonus for over-qualification on critical/emergency jobs
        try:
            priority_enum = job.priority if isinstance(job.priority, Priority) else Priority.ROUTINE
        except:
            priority_enum = Priority.ROUTINE
            
        if priority_enum in [Priority.CRITICAL, Priority.EMERGENCY]:
            if avg_score > 0.8:  # Level 4-5 techs
                avg_score = min(1.0, avg_score * 1.1)
        
        return avg_score
    
    def _score_utilization(self, tech: Technician, job: Job) -> float:
        """
        Score to balance workload across team
        Target: 6 billable hours per day
        
        Returns 0.0 - 1.0
        """
        target_hours = 6.0
        
        # Get today's performance metric
        today = datetime.utcnow().date()
        perf = self.db.query(TechPerformanceMetric).filter(
            TechPerformanceMetric.tech_id == tech.id,
            func.date(TechPerformanceMetric.date) == today
        ).first()
        
        current_billable = 0.0
        if perf:
            try:
                current_billable = float(perf.billable_hours) if perf.billable_hours is not None else 0.0  # type: ignore
            except:
                current_billable = 0.0
        
        # Calculate projected hours after this job
        try:
            estimated_hours = float(job.estimated_hours) if job.estimated_hours is not None else 0.0  # type: ignore
        except:
            estimated_hours = 0.0
            
        projected_hours = current_billable + estimated_hours
        
        # Score based on how close to target
        score = 0.5
        try:
            if projected_hours <= target_hours:
                # Under target - prefer this tech (help them hit target)
                score = 1.0 - (abs(projected_hours - target_hours) / target_hours)
            else:
                # Over target - penalize (don't overload)
                overage = projected_hours - target_hours
                score = max(0, 1.0 - (overage / 3.0))
        except:
            score = 0.5
        
        return max(0.0, min(1.0, score))
    
    def _score_geography(self, tech: Technician, job: Job) -> float:
        """
        Score based on route efficiency
        Considers current location AND next scheduled job
        
        Returns 0.0 - 1.0
        """
        try:
            tech_lat = float(tech.current_lat) if tech.current_lat is not None else None  # type: ignore
            tech_lon = float(tech.current_lon) if tech.current_lon is not None else None  # type: ignore
            job_lat = float(job.lat) if job.lat is not None else 0.0  # type: ignore
            job_lon = float(job.lon) if job.lon is not None else 0.0  # type: ignore
        except:
            return 0.5
        
        if not tech_lat or not tech_lon:
            return 0.5
        
        # Calculate distance to job
        distance_to_job = self._haversine(
            tech_lat, tech_lon,
            job_lat, job_lon
        )
        
        # Check if tech has a next scheduled job
        next_job = self.db.query(Job).filter(
            Job.id != job.id
        ).first()
        
        try:
            if next_job is not None and next_job.lat is not None and next_job.lon is not None:
                # Calculate route efficiency
                next_lat = float(next_job.lat)  # type: ignore
                next_lon = float(next_job.lon)  # type: ignore
                
                # Option 1: Current -> Job -> Next
                route_with_job = (
                    distance_to_job + 
                    self._haversine(job_lat, job_lon, 
                                   next_lat, next_lon)
                )
                
                # Option 2: Current -> Next (skip this job)
                direct_to_next = self._haversine(
                    tech_lat, tech_lon,
                    next_lat, next_lon
                )
                
                # How much detour does this job add?
                detour = route_with_job - direct_to_next
                
                # Score based on detour (less detour = better)
                if detour < 5:  # Less than 5 miles detour
                    score = 1.0
                elif detour < 15:
                    score = 0.7
                else:
                    score = 0.3
            else:
                # No next job - just score on distance
                if distance_to_job < 5:
                    score = 1.0
                elif distance_to_job < 15:
                    score = 0.8
                elif distance_to_job < 30:
                    score = 0.5
                else:
                    score = 0.2
        except:
            # No next job - just score on distance
            if distance_to_job < 5:
                score = 1.0
            elif distance_to_job < 15:
                score = 0.8
            elif distance_to_job < 30:
                score = 0.5
            else:
                score = 0.2
        
        return score
    
    def _score_parts_availability(self, tech: Technician, job: Job) -> float:
        """
        Score based on whether tech has required parts in truck
        
        Returns 0.0 - 1.0
        """
        # Get required parts for job
        required_parts = self.db.query(JobPart).filter(
            JobPart.job_id == job.id
        ).all()
        
        if not required_parts:
            return 1.0  # No parts needed
        
        # Check tech's inventory
        tech_inventory = {
            inv.part_sku: inv.quantity 
            for inv in tech.inventory
        }
        
        parts_available = 0
        for part in required_parts:
            if part.part_sku in tech_inventory:
                if tech_inventory[part.part_sku] >= part.quantity_used:
                    parts_available += 1
        
        # Percentage of parts available
        score = parts_available / len(required_parts)
        
        return score
    
    def _score_customer_preference(self, tech: Technician, job: Job) -> float:
        """
        Score based on customer history with this tech
        
        Returns 0.0 - 1.0
        """
        # Simple scoring - could be enhanced with CustomerHistory model
        # For now, return neutral score
        return 0.5
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in miles"""
        try:
            R = 3958.8
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlambda = radians(lon2 - lon1)
            a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c
        except (TypeError, ValueError):
            return 0.0
    
    def find_best_technician(
        self, 
        job_id: int,
        available_techs: Optional[List[Technician]] = None
    ) -> Optional[Tuple[Technician, float, Dict[str, Any]]]:
        """
        Find best technician for a job
        
        Returns:
            (best_tech, best_score, score_breakdown) or None
        """
        from .database import DatabaseHelper
        db = DatabaseHelper(self.db)
        
        job = db.get_job(job_id)
        if not job:
            return None
        
        if not available_techs:
            available_techs = db.get_available_technicians()
        
        if not available_techs:
            return None
        
        best_tech: Optional[Technician] = None
        best_score = -1.0
        best_breakdown: Optional[Dict[str, Any]] = None
        
        for tech in available_techs:
            score, breakdown = self.calculate_assignment_score(tech, job)
            
            # Must have required skills (score > 0 means qualified)
            if breakdown.get('skill', 0) == 0:
                continue
            
            if score > best_score:
                best_score = score
                best_tech = tech
                best_breakdown = breakdown
        
        if best_tech and best_breakdown is not None:
            logger.info(
                f"Best tech for job {job_id}: {best_tech.name} "
                f"(score: {best_score:.3f})"
            )
            logger.debug(f"Score breakdown: {best_breakdown}")
            return (best_tech, best_score, best_breakdown)
        
        return None
