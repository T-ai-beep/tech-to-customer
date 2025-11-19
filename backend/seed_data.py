# seed_data.py
from models import get_engine, get_session, init_db, Priority
from database import DatabaseHelper
from datetime import datetime, timedelta

def seed_database():
    """Populate database with test data"""
    engine = get_engine()
    init_db(engine)
    session = get_session(engine)
    db = DatabaseHelper(session)
    
    print("🌱 Seeding database with test data...")
    
    # Create customers
    customers = [
        db.create_customer(
            name="John Smith",
            phone="512-555-0101",
            address="123 Main St, Austin TX 78701",
            lat=30.2672,
            lon=-97.7431,
            email="john@example.com"
        ),
        db.create_customer(
            name="Jane Doe",
            phone="512-555-0102",
            address="456 Oak Ave, Austin TX 78702",
            lat=30.2741,
            lon=-97.7306
        ),
        db.create_customer(
            name="Bob Johnson",
            phone="512-555-0103",
            address="789 Elm St, Austin TX 78703",
            lat=30.2808,
            lon=-97.7461
        ),
    ]
    print(f"✅ Created {len(customers)} customers")
    
    # Create technicians
    techs = [
        db.create_technician(
            name="Mike Rodriguez",
            phone="512-555-0201",
            skills=["hvac", "residential", "commercial"],
            certifications=["EPA_608_Type_II", "NATE_Certified"],
            equipment=["recovery_machine", "manifold_gauges", "vacuum_pump"],
            current_latitude=30.2672,
            current_longitude=-97.7431,
            shift_start=8,
            shift_end=17
        ),
        db.create_technician(
            name="Sarah Chen",
            phone="512-555-0202",
            skills=["hvac", "residential", "heat_pumps"],
            certifications=["EPA_608_Universal", "NATE_Certified"],
            equipment=["recovery_machine", "leak_detector"],
            current_latitude=30.2808,
            current_longitude=-97.7461,
            shift_start=8,
            shift_end=17
        ),
        db.create_technician(
            name="Carlos Martinez",
            phone="512-555-0203",
            skills=["hvac", "commercial", "refrigeration"],
            certifications=["EPA_608_Type_I", "Universal_Cert"],
            equipment=["recovery_machine", "gauges", "compressor"],
            current_latitude=30.2741,
            current_longitude=-97.7306,
            shift_start=10,
            shift_end=19,
            on_call=True
        ),
    ]
    print(f"✅ Created {len(techs)} technicians")
    
    # Create jobs
    jobs = [
        db.create_job(
            customer_id=customers[0].id,
            title="AC Not Cooling - Emergency",
            description="AC blowing warm air, 95°F outside",
            required_skills=["hvac", "residential"],
            priority=Priority.EMERGENCY,
            lat=customers[0].latitude,
            lon=customers[0].longitude,
            estimated_hours=2.0,
            equipment_details={"brand": "Carrier", "age_years": 8}
        ),
        db.create_job(
            customer_id=customers[1].id,
            title="Annual Maintenance",
            description="Scheduled tune-up",
            required_skills=["hvac"],
            priority=Priority.ROUTINE,
            lat=customers[1].latitude,
            lon=customers[1].longitude,
            estimated_hours=1.5,
            scheduled_for=datetime.utcnow() + timedelta(days=2)
        ),
        db.create_job(
            customer_id=customers[2].id,
            title="Heater Not Working",
            description="No heat, clicking sound",
            required_skills=["hvac", "residential"],
            priority=Priority.URGENT,
            lat=customers[2].latitude,
            lon=customers[2].longitude,
            estimated_hours=2.5,
            equipment_details={"brand": "Trane", "age_years": 12}
        ),
    ]
    print(f"✅ Created {len(jobs)} jobs")
    
    print("\n✅ Database seeded successfully!")
    print(f"   - {len(customers)} customers")
    print(f"   - {len(techs)} technicians")
    print(f"   - {len(jobs)} jobs")

if __name__ == "__main__":
    seed_database()