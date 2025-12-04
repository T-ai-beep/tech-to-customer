import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import your Base
from backend.models import Base  # make sure this is the file where Base is defined

# Alembic Config object
config = context.config

# Override sqlalchemy.url from .env if needed
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "sqlite:///./app.db"))

# Set up Python logging
fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata

# ------------------ Offline mode ------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# ------------------ Online mode ------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # detects column type changes
        )

        with context.begin_transaction():
            context.run_migrations()

# ------------------ Run ------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
