#!/usr/bin/env python3
"""
Migration script to add advanced tables to existing database
"""
from backend.models import get_engine, Base, init_db

def migrate():
    print("🔄 Running migration: add_advanced_tables")
    engine = get_engine()
    
    # This will create new tables without dropping existing ones
    Base.metadata.create_all(engine)
    
    print("✅ Migration complete")

if __name__ == "__main__":
    migrate()
