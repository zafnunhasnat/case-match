from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db


class FakeDB:
    def scalar(self, statement):
        return None


def test_login_rate_limit():
    fake_db = FakeDB()

    def override_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            responses = []

            for _ in range(6):
                response = client.post(
                    "/auth/login",
                    json={
                        "email": "synthetic@example.com",
                        "password": "SyntheticTestPassword123!",
                    },
                )
                responses.append(response.status_code)

        assert responses[:5] == [401, 401, 401, 401, 401]
        assert responses[5] == 429

    finally:
        app.dependency_overrides.clear()
