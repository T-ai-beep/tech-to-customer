# init_db.py
from backend.models import Base
from backend.database import engine

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")

if __name__ == "__main__":
    init_db()
