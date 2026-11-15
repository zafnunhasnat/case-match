import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth import get_current_user
from app.database.connection import get_db, get_review_db
from app.api import documents as documents_api


class FakeResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def first(self):
        return self.row

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.added = []
        self.committed = False
        self.rolled_back = False

    def execute(self, statement):
        return FakeResult(row=self.row, rows=self.rows)

    def add(self, item):
        self.added.append(item)

    def flush(self):
        for item in self.added:
            if hasattr(item, "original_author_id") and item.id is None:
                item.id = uuid.uuid4()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def client():
    app.dependency_overrides.clear()

    fake_db = FakeDB()

    def override_db():
        yield fake_db

    def override_review_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_review_db] = override_review_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def make_user(role="doctor", user_id=None):
    return SimpleNamespace(
        id=user_id or uuid.uuid4(),
        name="Synthetic Test User",
        email="synthetic@example.com",
        department="Testing",
        role=role,
    )


def test_unauthenticated_user_cannot_access_pending_reviews(client):
    response = client.get("/review/pending")

    assert response.status_code == 401


def test_ordinary_doctor_cannot_access_pending_reviews(client):
    doctor = make_user(role="doctor")

    app.dependency_overrides[get_current_user] = lambda: doctor

    response = client.get("/review/pending")

    assert response.status_code == 403


def test_reviewer_can_access_pending_reviews(client):
    reviewer = make_user(role="reviewer")

    app.dependency_overrides[get_current_user] = lambda: reviewer

    response = client.get("/review/pending")

    assert response.status_code == 200
    assert response.json() == []


def test_reviewer_cannot_review_own_submission(client):
    reviewer_id = uuid.uuid4()
    reviewer = make_user(role="reviewer", user_id=reviewer_id)

    clinical = SimpleNamespace(
        id=uuid.uuid4(),
        original_author_id=reviewer_id,
        original_author_name="Synthetic Test User",
        department="Testing",
        document_type="Synthetic document",
        ingested_at=datetime.now(timezone.utc),
    )

    screened = SimpleNamespace(
        screened_text="Redacted synthetic text",
        redactions_applied=True,
        redaction_count=1,
        screening_status="pending_review",
    )

    original = SimpleNamespace(original_text="Synthetic original text")

    fake_db = FakeDB(row=(screened, clinical, original))

    def override_review_db():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: reviewer
    app.dependency_overrides[get_review_db] = override_review_db

    response = client.get(f"/review/{clinical.id}")

    assert response.status_code == 403
    assert "own submission" in response.json()["detail"]


def test_already_reviewed_document_cannot_receive_another_decision(client):
    reviewer = make_user(role="reviewer")

    clinical = SimpleNamespace(
        id=uuid.uuid4(),
        original_author_id=uuid.uuid4(),
    )

    screened = SimpleNamespace(
        screening_status="approved",
        reviewed_by_id=None,
        reviewed_at=None,
        review_note=None,
    )

    fake_db = FakeDB(row=(screened, clinical))

    def override_review_db():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: reviewer
    app.dependency_overrides[get_review_db] = override_review_db

    response = client.post(
        f"/review/{clinical.id}/decision",
        json={"decision": "rejected"},
    )

    assert response.status_code == 409
    assert fake_db.committed is False


def test_document_submission_does_not_return_original_text(client, monkeypatch):
    doctor = make_user(role="doctor")
    fake_db = FakeDB()

    def override_db():
        yield fake_db

    app.dependency_overrides[get_current_user] = lambda: doctor
    app.dependency_overrides[get_db] = override_db

    monkeypatch.setattr(
        documents_api,
        "screen_text",
        lambda text: SimpleNamespace(
            screened_text="[REDACTED]",
            redactions_applied=True,
            redaction_count=1,
            screening_method="synthetic_test",
        ),
    )

    original_text = "Synthetic patient John Example, MRN ABC123456"

    response = client.post(
        "/documents/",
        json={
            "text": original_text,
            "document_type": "Synthetic test document",
        },
    )

    assert response.status_code == 201
    assert original_text not in response.text
    assert "John Example" not in response.text
    assert "ABC123456" not in response.text
    assert "document_id" in response.json()
    assert fake_db.committed is True
