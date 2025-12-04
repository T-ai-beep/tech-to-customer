print("TOP OF FILE: running reset_db.py")

from backend.models import Base
from backend.database import engine

print("Imported engine + Base successfully")

# Drop all
Base.metadata.drop_all(engine)
print("Dropped all tables")

# Create all
Base.metadata.create_all(engine)
print("Created all tables")
print("BOTTOM OF FILE: finished reset_db.py")