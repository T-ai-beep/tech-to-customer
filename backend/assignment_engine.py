"""
Advanced job assignment engine with multi-factor scoring
"""
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from math import radians, cos, sin, sqrt, atan2
import logging

from backend.models import Job, Technician, TechSkillLevel, TechInventory, JobPart, Priority, JobStatus
from backend.database import DatabaseHelper

logger = logging.getLogger(__name__)


class AssignmentEngine:
    """
    Intelligent job assignment with multi-factor optimization
    """
    
    def __init__(self, session: Session):
        self.db = session
        self.db_helper = DatabaseHelper(session)
        
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
            Priority.ROUTINE: 1.0,
            Priority.URGENT: 1.2,
            Priority.HIGH: 1.1,
            Priority.CRITICAL: 2.0,
            Priority.EMERGENCY: 1.5
        }
    
    def calculate_assignment_score(
        self, 
        tech: Technician, 
        job: Job
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate comprehensive assignment score
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
        priority_multiplier = self.priority_multipliers.get(job.priority, 1.0)
        total *= priority_multiplier
        
        breakdown['priority_multiplier'] = priority_multiplier
        breakdown['final_score'] = total
        
        return total, breakdown
    
    def _score_skill_match(self, tech: Technician, job: Job) -> float:
        """Score based on skill match AND proficiency level"""
        required_skills = job.required_skills or []
        
        if len(required_skills) == 0:
            return 1.0
        
        # Get tech's skill levels
        tech_skills = {}
        for sk in tech.skill_levels:
            tech_skills[sk.skill_name.lower()] = sk.proficiency_level
        
        total_score = 0
        for required_skill in required_skills:
            skill_lower = required_skill.lower()
            if skill_lower not in tech_skills:
                # Missing required skill = disqualify
                return 0.0
            
            # Normalize proficiency (1-5 scale to 0-1)
            proficiency = tech_skills[skill_lower]
            normalized = proficiency / 5.0
            total_score += normalized
        
        # Average proficiency across all required skills
        avg_score = total_score / len(required_skills)
        
        # Bonus for over-qualification on critical/emergency jobs
        if job.priority in [Priority.CRITICAL, Priority.EMERGENCY]:
            if avg_score > 0.8:  # Level 4-5 techs
                avg_score = min(1.0, avg_score * 1.1)
        
        return avg_score
    
    def _score_utilization(self, tech: Technician, job: Job) -> float:
        """Score to balance workload across team"""
        # Simple availability scoring
        now = datetime.utcnow()
        
        if tech.free_at and tech.free_at > now:
            # Tech is busy, penalize based on how long until free
            hours_until_free = (tech.free_at - now).total_seconds() / 3600
            if hours_until_free > 4:
                return 0.2
            elif hours_until_free > 2:
                return 0.5
            else:
                return 0.8
        else:
            # Tech is available now
            return 1.0
    
    def _score_geography(self, tech: Technician, job: Job) -> float:
        """Score based on route efficiency"""
        if not tech.current_lat or not tech.current_lon or not job.lat or not job.lon:
            return 0.5
        
        # Calculate distance to job
        distance_to_job = self._haversine(
            tech.current_lat, tech.current_lon,
            job.lat, job.lon
        )
        
        # Score based on distance
        if distance_to_job < 5:
            return 1.0
        elif distance_to_job < 15:
            return 0.8
        elif distance_to_job < 30:
            return 0.5
        else:
            return 0.2
    
    def _score_parts_availability(self, tech: Technician, job: Job) -> float:
        """Score based on whether tech has required parts in truck"""
        # Get required parts for job
        required_parts = self.db.query(JobPart).filter(
            JobPart.job_id == job.id
        ).all()
        
        if not required_parts:
            return 1.0  # No parts needed
        
        # Check tech's inventory
        tech_inventory = {}
        for inv in tech.inventory:
            tech_inventory[inv.part_sku] = inv.quantity
        
        parts_available = 0
        for part in required_parts:
            if part.part_sku in tech_inventory:
                if tech_inventory[part.part_sku] >= (part.quantity_used or 1):
                    parts_available += 1
        
        # Percentage of parts available
        return parts_available / len(required_parts)
    
    def _score_customer_preference(self, tech: Technician, job: Job) -> float:
        """Score based on customer history with this tech"""
        # For now, return neutral score
        # Could be enhanced with historical data
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
        """
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None
        
        if not available_techs:
            available_techs = self.db_helper.get_available_technicians()
        
        if not available_techs:
            return None
        
        best_tech: Optional[Technician] = None
        best_score = -1.0
        best_breakdown: Optional[Dict[str, Any]] = None
        
        for tech in available_techs:
            # Eager load related data
            tech = self.db.query(Technician).options(
                joinedload(Technician.skill_levels),
                joinedload(Technician.inventory)
            ).filter(Technician.id == tech.id).first()
            
            if not tech:
                continue
                
            score, breakdown = self.calculate_assignment_score(tech, job)
            
            # Must have required skills
            if breakdown.get('skill', 0) == 0:
                continue
            
            if score > best_score:
                best_score = score
                best_tech = tech
                best_breakdown = breakdown
        
        if best_tech and best_breakdown:
            logger.info(
                f"Best tech for job {job_id}: {best_tech.name} "
                f"(score: {best_score:.3f})"
            )
            return (best_tech, best_score, best_breakdown)
        
        return None