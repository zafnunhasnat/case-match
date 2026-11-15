 import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def required_database_url(variable_name: str) -> str:
    value = os.getenv(variable_name)

    if not value:
        raise RuntimeError(
            f"{variable_name} must be configured"
        )

    return value


# Administrator connection: migrations and administrative scripts only.
ADMIN_URL = required_database_url("DATABASE_URL")

# Restricted application connections.
APP_URL = required_database_url("APP_DATABASE_URL")
REVIEW_URL = required_database_url("REVIEWER_DATABASE_URL")


admin_engine = create_engine(
    ADMIN_URL,
    pool_pre_ping=True,
)

engine = create_engine(
    APP_URL,
    pool_pre_ping=True,
)

review_engine = create_engine(
    REVIEW_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)

ReviewSessionLocal = sessionmaker(
    bind=review_engine,
    autoflush=False,
)

AdminSessionLocal = sessionmaker(
    bind=admin_engine,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


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
