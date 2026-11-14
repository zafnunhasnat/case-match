# CaseMatch AI
Find the case. Preserve the evidence. Protect the patient.

## How to run

### 1. Python environment
    python3 -m venv venv
    source venv/bin/activate
    cp .env.example .env
    pip install -r backend/requirements.txt
    python -m spacy download en_core_web_lg
    python -m spacy download en_core_web_sm

### 2. Database (choose ONE)

**Option A: Docker**

    docker compose up -d                  # start
    docker compose exec db psql -U casematch -d casematch -c "CREATE EXTENSION IF NOT EXISTS vector;"
    docker compose exec db psql -U casematch -d casematch   # open psql
    docker compose down                   # stop

**Option B: Homebrew on a Mac (if Docker will not run)**

    brew install postgresql@17 pgvector
    brew services stop postgresql@14      # only if you have it installed
    brew services start postgresql@17
    createdb casematch
    psql casematch -c "CREATE EXTENSION IF NOT EXISTS vector;"

Then set `DATABASE_URL=postgresql+psycopg://YOUR_USERNAME@localhost:5432/casematch` in your `.env`.

### 3. Check it works
    psql casematch -c "\dx"                # should list vector
    uvicorn backend.app.main:app --reload  # open http://127.0.0.1:8000/health
