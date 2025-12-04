import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./hvac_dispatch.db")

# Strip the sqlite:/// prefix to get the actual file path
db_path = DB_URL.replace("sqlite:///", "")

print("DB URL:", DB_URL)
print("Absolute path of DB file:", os.path.abspath(db_path))
print("Does the file exist?", os.path.exists(db_path))
