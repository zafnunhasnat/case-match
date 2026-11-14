# CaseMatch AI
Find the case. Preserve the evidence. Protect the patient.

## How to run
1. `cp .env.example .env`
2. `docker compose up -d`
3. `python3 -m venv venv && source venv/bin/activate`
4. `pip install -r backend/requirements.txt`
5. `uvicorn backend.app.main:app --reload`
