"""Add current_lat_lon to technicians and fix jobs.priority for SQLite"""

from alembic import op
import sqlalchemy as sa

# -------------------------------
# Alembic revision identifiers
# -------------------------------
revision = '9813f0662005'      # unique id for this migration
down_revision = 'c722eb140033' # the previous migration's revision id
branch_labels = None
depends_on = None

def upgrade():
    # SQLite-safe migration for jobs.priority
    op.create_table(
        'jobs_new',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('required_skills', sa.JSON, default=[]),
        sa.Column('priority', sa.Enum('ROUTINE','URGENT','HIGH','CRITICAL','EMERGENCY', name='priority'), nullable=False),
        sa.Column('status', sa.Enum('PENDING','ASSIGNED','IN_PROGRESS','COMPLETED', name='jobstatus'), nullable=False),
        sa.Column('lat', sa.Float),
        sa.Column('lon', sa.Float),
        sa.Column('address', sa.String),
        sa.Column('estimated_hours', sa.Float, nullable=False),
        sa.Column('equipment_details', sa.JSON, default={}),
        sa.Column('submitted_at', sa.DateTime, default=sa.func.now()),
        sa.Column('sla_met', sa.Boolean)
    )

    op.execute("""
        INSERT INTO jobs_new (id, customer_id, title, description, required_skills, priority, status,
                              lat, lon, address, estimated_hours, equipment_details, submitted_at, sla_met)
        SELECT id, customer_id, title, description, required_skills, priority, status,
               lat, lon, address, estimated_hours, equipment_details, submitted_at, sla_met
        FROM jobs
    """)

    op.drop_table('jobs')
    op.rename_table('jobs_new', 'jobs')

    # Add columns to technicians
    op.add_column('technicians', sa.Column('current_lat', sa.Float))
    op.add_column('technicians', sa.Column('current_lon', sa.Float))


def downgrade():
    # Reverse the column additions
    op.drop_column('technicians', 'current_lat')
    op.drop_column('technicians', 'current_lon')
    # You can add SQLite-safe downgrade for jobs table if needed
