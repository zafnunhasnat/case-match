from alembic import context
from app.database.connection import admin_engine   # DATABASE_URL (admin) from .env
from app.models import Base                         # imports every model

target_metadata = Base.metadata

def run_migrations_online():
    with admin_engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()