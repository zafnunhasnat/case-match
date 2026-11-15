import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError

load_dotenv()

def _connect(env_var):
    url = os.getenv(env_var)
    if not url:
        pytest.skip(f"{env_var} not set")
    try:
        return create_engine(url).connect()
    except OperationalError:
        pytest.skip("database not available")

def test_app_user_cannot_read_original_documents():
    with _connect("APP_DATABASE_URL") as conn:
        with pytest.raises(ProgrammingError):
            conn.execute(text("SELECT original_text FROM original_documents"))

def test_review_user_can_read_original_documents():
    with _connect("REVIEWER_DATABASE_URL") as conn:
        conn.execute(text("SELECT original_text FROM original_documents LIMIT 1"))
