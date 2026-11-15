import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# DATABASE_URL = admin (migrations, seed scripts).
ADMIN_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://casematch:change-me@localhost:5432/casematch")
# Restricted roles. Fall back to the admin URL so teammates' code works before their .env is updated.
APP_URL = os.getenv("APP_DATABASE_URL", ADMIN_URL)
REVIEW_URL = os.getenv("REVIEWER_DATABASE_URL", ADMIN_URL)

admin_engine = create_engine(ADMIN_URL, pool_pre_ping=True)
engine = create_engine(APP_URL, pool_pre_ping=True)            # app_user: cannot read original text
review_engine = create_engine(REVIEW_URL, pool_pre_ping=True)  # review_user: reviewer routes only

SessionLocal = sessionmaker(bind=engine, autoflush=False)
ReviewSessionLocal = sessionmaker(bind=review_engine, autoflush=False)
AdminSessionLocal = sessionmaker(bind=admin_engine, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_review_db():
    db = ReviewSessionLocal()
    try:
        yield db
    finally:
        db.close()