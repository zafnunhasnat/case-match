#!/usr/bin/env bash
# =============================================================================
# setup-github.sh  (CaseMatch)
# Bootstraps the GitHub side of the project: labels, 6 phase milestones,
# 29 fully detailed issues, phase epics, optional Projects board.
#
# Usage (run from inside your cloned repo):
#   DRY_RUN=1 ./setup-github.sh        # preview, touches nothing
#   ./setup-github.sh                  # for real
#   WITH_PROJECT=1 ./setup-github.sh   # also create a Projects board
#                                      # (needs: gh auth refresh -s project)
#
# Run it ONCE. Labels and milestones are safe to re-run; issues are not
# (they would be duplicated).
# =============================================================================
set -euo pipefail

DRY_RUN="${DRY_RUN:-0}"
WITH_PROJECT="${WITH_PROJECT:-0}"
PROJECT_TITLE="${PROJECT_TITLE:-CaseMatch Roadmap}"

if [ "$DRY_RUN" != "1" ]; then
  command -v gh >/dev/null || { echo "Install the GitHub CLI: https://cli.github.com"; exit 1; }
  gh auth status >/dev/null 2>&1 || { echo "Run: gh auth login"; exit 1; }
  gh repo view >/dev/null 2>&1 || { echo "Run this from inside your cloned repo (needs a GitHub remote)"; exit 1; }
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
COUNTER=0

# ---------------------------------------------------------------- milestones
ms_title() {
  case "$1" in
    1) echo "Phase 1: Foundation (repo, database, data)" ;;
    2) echo "Phase 2: Privacy pipeline" ;;
    3) echo "Phase 3: Search engine" ;;
    4) echo "Phase 4: Access control and provenance API" ;;
    5) echo "Phase 5: Frontend" ;;
    6) echo "Phase 6: Export, evaluation and ship" ;;
  esac
}

# -------------------------------------------------------------------- labels
make_label() { # name color description
  if [ "$DRY_RUN" = "1" ]; then echo "[dry-run] label: $1"; return; fi
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null
  echo "label: $1"
}

echo "== Labels =="
make_label "type: feature"  "1D76DB" "New functionality"
make_label "type: bug"      "D73A4A" "Something is broken"
make_label "type: chore"    "CFD3D7" "Tooling, setup, refactors"
make_label "type: docs"     "0075CA" "Documentation"
make_label "type: learning" "A371F7" "Study task that produces a note in docs/notes"
make_label "type: epic"     "3E4B9E" "Phase-level tracking issue"
make_label "area: data"     "0E8A16" "Synthetic data and labeled queries"
make_label "area: privacy"  "B100FF" "De-identification, review, leak tests"
make_label "area: search"   "F9A825" "Retrieval, ranking, NLP"
make_label "area: backend"  "FF8C00" "FastAPI, database, auth"
make_label "area: frontend" "FF2E88" "React UI"
make_label "area: eval"     "00BCD4" "Evaluation and metrics"
make_label "area: infra"    "5319E7" "Docker, CI, repo setup"
make_label "stretch"        "C5DEF5" "Nice to have, first to cut if behind"

echo; echo "== Milestones =="
EXISTING=""
if [ "$DRY_RUN" != "1" ]; then
  EXISTING="$(gh api "repos/{owner}/{repo}/milestones?state=all&per_page=100" --jq '.[].title')"
fi
for p in 1 2 3 4 5 6; do
  title="$(ms_title "$p")"
  if grep -Fxq "$title" <<<"$EXISTING"; then echo "skip (exists): $title"; continue; fi
  if [ "$DRY_RUN" = "1" ]; then echo "[dry-run] milestone: $title"; continue; fi
  gh api "repos/{owner}/{repo}/milestones" -f title="$title" -f state=open >/dev/null
  echo "milestone: $title"
done

# -------------------------------------------------------------------- issues
issue() { # phase labels title   (body on stdin)
  local phase="$1" labels="$2" title="$3" body num url
  body="$(cat)"
  if [ "$DRY_RUN" = "1" ]; then
    COUNTER=$((COUNTER + 1)); num="$COUNTER"; url="(dry-run)"
    echo "[dry-run] #$num [P$phase] $title"
  else
    url="$(gh issue create --title "$title" --body "$body" --label "$labels" \
            --milestone "$(ms_title "$phase")")"
    num="${url##*/}"
    echo "created #$num  [P$phase] $title"
  fi
  echo "- [ ] #$num $title" >> "$TMP/phase-$phase"
  echo "$url" >> "$TMP/urls"
}

echo; echo "== Issues =="

# ============================ PHASE 1: FOUNDATION ===========================
issue 1 "type: chore,area: infra" "chore: bootstrap repo structure, templates and branch rules" <<'EOF'
## Goal
Give the repo the structure and guardrails every later issue relies on.

## Purpose
Search, privacy, and provenance code must live in separate places so each can be tested alone. Branch rules stop anyone (including us) from breaking `main`.

## Resources
- GitHub docs: "About protected branches" and "About rulesets"
- GitHub docs: "Creating a pull request template"

## Tasks
- [ ] Create the folders: `backend/app/{api,services,models,database}`, `backend/tests`, `frontend/`, `evaluation/`, `data/synthetic_cases`, `scripts/`, `docs/notes`, `docs/decisions`. Add a `.gitkeep` to each empty one. **Why:** the folder names double as the architecture.
- [ ] Write `.gitignore` (`.env`, `__pycache__/`, `venv/`, `node_modules/`, `.DS_Store`, `data/synthetic_cases/*.json` is NOT ignored). **Why:** secrets and junk never reach the repo.
- [ ] Add `.github/pull_request_template.md` with: what changed, which issue it closes, how to test, screenshots. **Why:** consistent reviews.
- [ ] Rewrite `README.md` skeleton: name, one-line pitch ("Find the case. Preserve the evidence. Protect the patient."), planned features, "how we work".
- [ ] Settings -> General: allow **squash merging only** and **auto-delete head branches**.
- [ ] Settings -> Rules: protect `main` (require a pull request, block force pushes). Required status checks are added in the CI issue.
- [ ] Create `docs/decisions/0001-no-llm-in-core-search.md` (an ADR: context, decision, consequences). **Why:** documents our biggest design choice for judges.

## Done when
- [ ] This issue was closed by a merged PR
- [ ] `main` rejects direct pushes

## Learning goals
Branch -> commit -> PR -> squash-merge loop; what an ADR is.
EOF

issue 1 "type: chore,area: infra" "chore: Docker Compose with Postgres + pgvector and .env setup" <<'EOF'
## Goal
One command starts the database the same way on every laptop.

## Purpose
Everything depends on the database. Docker removes "works on my machine" problems.

## Resources
- pgvector README: https://github.com/pgvector/pgvector
- Docker Compose docs: "Compose file reference" (services, volumes, healthcheck)

## Tasks
- [ ] Install Docker Desktop and confirm `docker --version` works.
- [ ] Create `docker-compose.yml` with one service `db`, image `pgvector/pgvector:pg16`, port `5432:5432`, env from `.env`, a named volume `pgdata`, and a `healthcheck` using `pg_isready`. **Why:** this image ships Postgres with pgvector installed, so no manual compiling.
- [ ] Create `.env.example` with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`, `JWT_SECRET`. Copy to `.env` (never commit `.env`).
- [ ] Run `docker compose up -d`, then `docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS vector;"`.
- [ ] Verify with `\dx` that `vector` is listed.
- [ ] Add the three commands (`up`, `down`, `psql`) to the README.

## Done when
- [ ] A fresh clone plus `cp .env.example .env` plus `docker compose up -d` gives a healthy database with `vector` enabled

## Think-along hint
Why a named volume? What happens to your data without one when the container is removed?
EOF

issue 1 "type: learning,area: search" "learning: how clinical case retrieval systems work" <<'EOF'
## Goal
Understand what already exists so we position CaseMatch honestly and design with confidence.

## Purpose
Judges will ask "isn't this just EHR search?". We need a real answer, not a guess.

## Resources
- EMERSE (Electronic Medical Record Search Engine): search for the project page and its published paper
- SemEHR: search "SemEHR semantic search electronic health records" and read the abstract and architecture figure
- HL7 FHIR overview: https://hl7.org/fhir/overview.html

## Tasks
- [ ] Read the EMERSE and SemEHR abstracts and skim their architecture sections.
- [ ] Write `docs/notes/01-existing-systems.md` (about 1 page, your own words): what each does, what it does not do, and where CaseMatch differs (similarity retrieval + exact original wording + provenance + negation handling).
- [ ] End the note with a list of 5+ open questions our design must answer (for example: how do we show why a case matched?).
- [ ] Add a "Related work" paragraph to the README that names these systems and does not overclaim.

## Done when
- [ ] Note and README paragraph merged

## Think-along hint
Don't claim nobody built medical record search. Claim a specific workflow combination, and be able to say what is NOT new.
EOF

issue 1 "type: feature,area: backend" "feat: database schema and Alembic migrations" <<'EOF'
## Goal
Create every table the project needs, with originals stored separately from screened copies.

## Purpose
The privacy design lives in the schema. If originals and screened text share a table, a bug can leak identities. Separate tables plus separate database roles make leaks structurally harder.

## Resources
- SQLAlchemy 2.0 Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
- Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- PostgreSQL full-text search: https://www.postgresql.org/docs/current/textsearch.html
- pgvector README (HNSW index section)

## Tasks
- [ ] `pip install sqlalchemy alembic "psycopg[binary]" pgvector pydantic-settings` and add them to `backend/requirements.txt`.
- [ ] Write `backend/app/database/connection.py` (engine and session from `DATABASE_URL` via pydantic-settings).
- [ ] Write models in `backend/app/models/`: `Doctor`(id, name, department, role, password_hash), `ClinicalDocument`(id, original_author_id, department, document_type, created_at, source_reference, original_text), `ScreenedDocument`(id, clinical_document_id, screened_text, screening_status, redactions_applied, redaction_counts JSON, screening_method, reviewed_by, reviewed_at), `DocumentEmbedding`(id, screened_document_id, section, embedding Vector(384), model_name), `ClinicalTerm`(id, preferred_term, synonym, terminology_code, terminology_system), `SearchAuditLog`(id, doctor_id, document_id, action, detail JSON, timestamp). **Why:** author and reviewer are separate columns so redaction never overwrites the author.
- [ ] Add `search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', screened_text)) STORED` on `screened_documents` with `CREATE INDEX ... USING gin(search_vector)`. **Why:** fast keyword search with no extra service.
- [ ] Add `CREATE INDEX ON document_embeddings USING hnsw (embedding vector_cosine_ops);`. **Why:** fast approximate nearest-neighbor search.
- [ ] Run `alembic init backend/app/database/migrations`, point it at your models, then `alembic revision --autogenerate -m "initial schema"` and `alembic upgrade head`. Put `CREATE EXTENSION IF NOT EXISTS vector;` at the top of the first migration.
- [ ] Create two roles in a second migration: `app_user` (SELECT on `screened_documents`, `document_embeddings`, `clinical_terms`; INSERT on `search_audit_logs`) and `admin_user`. **Why:** even a buggy search query cannot read `clinical_documents`.
- [ ] Write a pytest that connects as `app_user` and asserts `SELECT * FROM clinical_documents` raises a permission error.

## Done when
- [ ] `alembic upgrade head` builds everything from an empty database
- [ ] The permission test passes
EOF

issue 1 "type: feature,area: data" "feat: synthetic clinical note generator with planted identifiers" <<'EOF'
## Goal
Generate 150 to 300 fictional notes that look messy and real, and record exactly which identifiers we planted.

## Purpose
We cannot use real patient data. The dataset must contain hard cases (negation, history, abbreviations) and known identifiers so we can measure search quality and privacy leaks.

## Resources
- Faker docs: https://faker.readthedocs.io
- Synthea (synthetic patients): https://synthetichealth.github.io/synthea/
- MTSamples (check license before copying anything): https://mtsamples.com
- Python `random` and `string.Template`

## Tasks
- [ ] Write `scripts/generate_data.py` using `Faker` with a fixed seed (`Faker.seed(42)`). **Why:** the same dataset every run makes tests repeatable.
- [ ] Create 8 fake doctors across Emergency Medicine, Internal Medicine, Pediatrics, Cardiology (name, department, role). Save to `data/synthetic_cases/doctors.json`.
- [ ] Write 4 template groups (respiratory, cardiac, GI, neurological), each with sections: `CHIEF COMPLAINT`, `HISTORY`, `ASSESSMENT`. **Why:** sections let us embed and highlight per section later.
- [ ] Vary wording from lists: dyspnea / shortness of breath / SOB / trouble breathing; chest discomfort / CP / chest tightness; HTN / high blood pressure. Add typos in about 5% of notes. **Why:** this is what makes synonym and semantic search worth building.
- [ ] Include hard cases on purpose, at least 15 notes each: negation ("denies chest pain"), history ("history of migraines"), family history ("mother had MI"), uncertainty ("possible pneumonia"). Store a `tags` list per note describing which hard cases it contains.
- [ ] Plant identifiers with Faker (names, DOB, phone, MRN, address) in the headers and bodies, plus subtle ones (rare job, small town, specific event). Write every planted value and its type to `data/synthetic_cases/planted_identifiers.json` mapped by note id. **Why:** this file is the answer key for the leak test.
- [ ] Save notes to `data/synthetic_cases/notes.json` (id, author_id, department, document_type, created_at, text, tags).
- [ ] Print counts per department and per tag to confirm coverage.

## Done when
- [ ] 150+ notes, doctors, and planted-identifier files are committed
- [ ] Running the script twice produces identical files

## Think-along hint
If a real doctor skimmed three notes, would they believe them? Add abbreviations and sentence fragments until they would.
EOF

issue 1 "type: feature,area: eval" "feat: labeled queries with dev/test split" <<'EOF'
## Goal
Write 25 to 40 test queries with the correct matching note ids, split into a dev set and a held-out test set.

## Purpose
This is our proof that search works. Tuning on the dev set and reporting on the test set keeps our numbers honest.

## Resources
- Manning, Raghavan, Schutze: "Introduction to Information Retrieval", chapter 8 (evaluation): https://nlp.stanford.edu/IR-book/

## Tasks
- [ ] Write `evaluation/labeled_queries.json`: each entry has `id`, `query`, `relevant_note_ids`, `must_not_match_note_ids`, `tags` (synonym, negation, history, abbreviation, multi-finding).
- [ ] Label by reading the notes (or filtering on the generator's `tags` and then spot-checking by hand). **Why:** labels from the generator are fast, but a human check catches mistakes.
- [ ] Cover each hard case: at least 5 synonym queries, 5 negation queries, 3 history, 3 abbreviation, 5 multi-finding.
- [ ] Split 60/40 into `dev` and `test` using a fixed seed. Never look at `test` results while tuning. **Why:** prevents overfitting.
- [ ] Write a small validator script that fails if a relevant id does not exist or a query has zero relevant notes.

## Done when
- [ ] 25+ queries labeled, split, and validated

## Learning goals
Ground truth, relevance judgments, why held-out data matters.
EOF

# ============================ PHASE 2: PRIVACY ==============================
issue 2 "type: learning,area: privacy" "learning: de-identification (Safe Harbor, Expert Determination, Presidio)" <<'EOF'
## Goal
Understand what real de-identification requires, so our claims are accurate.

## Purpose
Calling a prototype "HIPAA compliant" would be wrong and damaging. We need to know the real standards and where automated tools fall short.

## Resources
- HHS: "Guidance Regarding Methods for De-identification of Protected Health Information": https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
- Presidio docs: https://microsoft.github.io/presidio/ (Analyzer, Anonymizer, custom recognizers)
- spaCy 101: https://spacy.io/usage/spacy-101

## Tasks
- [ ] Read the HHS page: list the 18 Safe Harbor identifier categories and the idea of Expert Determination.
- [ ] Read Presidio's "Getting started" and "Adding custom recognizers" pages.
- [ ] Write `docs/notes/02-deidentification.md`: which identifiers we handle, which we cannot (indirect ones like rare conditions), and the exact sentence we will use publicly ("privacy-screened using automated tools plus human review, not certified de-identification").
- [ ] Run Presidio on three fake notes in a notebook or script and record what it misses.

## Done when
- [ ] Note merged, with a table of identifier type, detection method, and known weakness
EOF

issue 2 "type: feature,area: privacy" "feat: privacy screening pipeline (Presidio + regex + review flags)" <<'EOF'
## Goal
Turn an original note into a screened copy that keeps the clinician's wording but redacts identifiers.

## Purpose
Other doctors read these notes. Patient identity must not appear in the display text, the search index, the embeddings, or the PDF.

## Resources
- Presidio Analyzer and Anonymizer docs
- Python `re` docs (named groups, verbose patterns)

## Tasks
- [ ] `python -m spacy download en_core_web_lg` (Presidio's default NLP model).
- [ ] Write `backend/app/services/privacy.py` with `screen(text) -> ScreenResult(screened_text, redaction_counts, needs_manual_review)`.
- [ ] Use `AnalyzerEngine().analyze(text, language="en", entities=["PERSON","PHONE_NUMBER","EMAIL_ADDRESS","DATE_TIME","LOCATION"])`. **Why:** a maintained detector beats writing our own.
- [ ] Add custom recognizers with `PatternRecognizer(supported_entity="MRN", patterns=[Pattern("mrn", r"\bMRN[:# ]*\d{6,10}\b", 0.9)])` plus a phone-format and hospital-ID pattern. **Why:** Presidio does not know our ID formats.
- [ ] Replace matches using `AnonymizerEngine` with operators that output visible tags like `[REDACTED-NAME]`. **Why:** doctors should see that text was removed and what type.
- [ ] Generalize dates: replace exact dates with `[DATE]` but leave durations like "three days" untouched (add an allow-list regex before anonymizing). **Why:** timing is clinically useful; exact dates identify people.
- [ ] Flag `needs_manual_review` with simple rules: rare-occupation word list, very small town list, "first case", unusual-event phrases. **Why:** automated tools miss indirect identifiers.
- [ ] Never write to `clinical_documents`. Return results only. **Why:** originals stay immutable.
- [ ] Write pytest tests with 10 notes: one per identifier type plus one with a duration that must NOT be redacted.

## Done when
- [ ] Tests pass and redaction preserves clinical wording on a visual diff of three notes

## Think-along hint
Is redacting too much a problem? Yes: if every date and place disappears, the note loses clinical meaning. Decide where the line is and write it down.
EOF

issue 2 "type: feature,area: privacy" "feat: leak test harness using planted identifiers" <<'EOF'
## Goal
An automated test that fails if any planted identifier survives screening.

## Purpose
Privacy is our central claim. This test turns it into a measurable number (redaction recall by entity type) and protects it forever.

## Resources
- pytest docs: parametrize and fixtures

## Tasks
- [ ] Write `backend/tests/test_privacy_leak.py` that loads `notes.json` and `planted_identifiers.json`, runs `screen()` on every note, and asserts no planted value appears in the screened text (case-insensitive, also test partial matches like last names and 4-digit year of birth).
- [ ] Write `evaluation/redaction_report.py` that prints recall per entity type (NAME, PHONE, DOB, MRN, ADDRESS, subtle) and lists every miss. **Why:** the misses guide improvements and make an honest limitations slide.
- [ ] Add a reusable helper `assert_no_leaks(text, note_id)` that later issues call on search results, API responses, and the PDF.
- [ ] Save the first results table in `docs/notes/03-redaction-baseline.md`.

## Done when
- [ ] Zero planted direct identifiers survive; the subtle ones are listed as known limitations
EOF

issue 2 "type: feature,area: backend" "feat: ingestion and privacy-reviewer workflow (backend)" <<'EOF'
## Goal
Move a document through `pending -> screened -> reviewed -> approved` (or `failed`), and only index approved documents.

## Purpose
Screening is never perfect. A human approval step, plus a rule that only approved text becomes searchable, is what makes the design trustworthy.

## Resources
- FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/ (path operations, dependencies, background tasks)

## Tasks
- [ ] Create the FastAPI app in `backend/app/main.py` with `GET /health`.
- [ ] Write `scripts/seed_database.py`: load doctors and notes, insert originals, run `screen()`, insert screened rows with status `screened` (or `pending` if `needs_manual_review`). **Why:** a seed script replaces a full upload system and still proves the pipeline.
- [ ] `POST /documents/ingest` (admin only for now): stores the original, runs screening, returns the new ids.
- [ ] `GET /review/queue`, `POST /review/{id}/approve`, `POST /review/{id}/reject` (reason required).
- [ ] On approve: set status `approved`, record `reviewed_by` and `reviewed_at`. Indexing hooks (tsvector is automatic; embeddings are added by the semantic search issue) run only on approve. **Why:** unreviewed text must never reach search or embeddings.
- [ ] Add a `get_searchable_documents()` helper that filters `screening_status = 'approved'`, and use it everywhere. **Why:** one place enforces the privacy rule.
- [ ] pytest: a pending document is invisible to search; after approve it appears; a rejected one never appears.

## Done when
- [ ] The three lifecycle tests pass
EOF

# ============================ PHASE 3: SEARCH ===============================
issue 3 "type: learning,area: search" "learning: information retrieval basics (full-text, embeddings, fusion, metrics)" <<'EOF'
## Goal
Understand the three retrieval ideas we combine and how to measure them.

## Purpose
We must be able to explain, in plain words, why hybrid search beats keyword-only, and which numbers prove it.

## Resources
- PostgreSQL docs: "Full Text Search" chapters 12.1 to 12.3
- Sentence Transformers docs: https://www.sbert.net/ (Semantic Search page)
- pgvector README (distance operators)
- Cormack, Clarke, Buettcher (2009): "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods"
- Manning et al., Introduction to Information Retrieval, chapter 8

## Tasks
- [ ] In `psql`, try `SELECT to_tsvector('english','shortness of breath'), plainto_tsquery('english','difficulty breathing');` and note why these do NOT match.
- [ ] Run the sbert semantic search example with 5 sentences of your own and observe which pairs score high.
- [ ] Write `docs/notes/04-retrieval-basics.md`: define tsvector, embedding, cosine similarity, RRF (`score = sum(1 / (k + rank))`, k about 60), Precision@k, Recall@k, MRR, in your own words with one tiny worked example each.
- [ ] List the weaknesses of each method (keyword: synonyms; embeddings: negation; RRF: ignores score size).

## Done when
- [ ] Note merged with worked examples
EOF

issue 3 "type: feature,area: search" "feat: query parser and terminology normalization" <<'EOF'
## Goal
Turn typed text such as "no fever but difficulty breathing and chest discomfort for 3 days" into structured findings with synonyms, excluded findings, and duration.

## Purpose
Doctors do not type perfect keywords. This step makes "difficulty breathing" find "dyspnea" and keeps "no fever" from matching fever notes.

## Resources
- spaCy: Linguistic features (noun chunks, dependency parse)
- medspaCy README: https://github.com/medspacy/medspacy
- UMLS and SNOMED CT (read about licensing only; we use a small curated list now)

## Tasks
- [ ] Create `data/terminology/terms.csv` with 100 to 200 rows: `preferred_term, synonym, abbreviation, terminology_code` (for example `dyspnea, shortness of breath, SOB`). Load into `clinical_terms` with a seed script. **Why:** SNOMED CT/UMLS need a license, so we start small and name them as the future upgrade.
- [ ] Write `backend/app/services/terminology.py`: `normalize(phrase) -> concept` using lowercase, lemma, and exact lookup, with a fuzzy fallback (`rapidfuzz`, threshold 90).
- [ ] Write `backend/app/services/query_parser.py`: split on commas, "and", "but", "with"; extract noun chunks with spaCy; drop filler words ("patient", "has", "reports").
- [ ] Detect negation in the query with medspaCy ConText (`import medspacy; nlp = medspacy.load()`), mark the finding `excluded=True`. **Why:** "no fever" means exclude, not include.
- [ ] Extract duration with spaCy `DATE` entities plus a regex for "3 days", "two weeks".
- [ ] Return `ParsedQuery(findings=[{text, concept, synonyms, excluded}], duration)` as a Pydantic model.
- [ ] pytest with 10 example queries including the one above, abbreviations, and a typo.

## Done when
- [ ] The example query returns three findings (fever excluded) plus duration, and all tests pass
EOF

issue 3 "type: feature,area: search" "feat: keyword and terminology retrieval (Postgres full-text)" <<'EOF'
## Goal
Exact-match retrievers that return every candidate with a matched snippet.

## Purpose
This is the reliable base of search: fast, explainable, and it finds exact wording that embeddings can blur.

## Resources
- PostgreSQL: `ts_rank`, `ts_headline`, `websearch_to_tsquery`
- SQLAlchemy 2.0: `text()` and bound parameters

## Tasks
- [ ] Write `backend/app/services/keyword_search.py` with `keyword_search(parsed, filters) -> list[Candidate]`.
- [ ] Build one tsquery per finding by OR-ing its synonyms: `to_tsquery('english', 'dyspnea | (shortness & breath) | sob')`. A finding counts once however many synonyms match. **Why:** "dyspnea" should count as one match for "difficulty breathing", not three.
- [ ] Rank with `ts_rank(search_vector, query)` and create snippets with `ts_headline('english', screened_text, query, 'MaxFragments=2')`.
- [ ] Return `matched_findings`, `total_findings`, `matched_via` ("exact" or "synonym"), and snippets. Use bound parameters only. **Why:** blocks SQL injection from typed symptoms.
- [ ] No `LIMIT` on the final result. **Why:** the promise is every relevant case.
- [ ] Filters: department, document type, date range.
- [ ] Always read through `get_searchable_documents()` (approved only).
- [ ] pytest: "difficulty breathing" returns "shortness of breath" and "dyspnea" notes; an unapproved note never appears.

## Done when
- [ ] Synonym tests pass and results include snippets with match counts
EOF

issue 3 "type: feature,area: search" "feat: semantic retrieval with Sentence Transformers + pgvector" <<'EOF'
## Goal
Meaning-based search that finds relevant notes when the wording differs.

## Purpose
Synonym lists never cover everything. Embeddings catch phrasing our dictionary misses.

## Resources
- Sentence Transformers docs: https://www.sbert.net/
- pgvector README: cosine distance `<=>`, HNSW
- Hugging Face model hub (search for a biomedical sentence-embedding model and read its model card)

## Tasks
- [ ] `pip install sentence-transformers` and load `all-MiniLM-L6-v2` (384 dimensions, matches our `Vector(384)` column).
- [ ] Split each approved note into sections (chief complaint, history, assessment) and embed each section. **Why:** long notes blur into one vector and lose detail.
- [ ] Write `scripts/build_embeddings.py` that embeds only approved screened text and stores `section`, `embedding`, and `model_name`. **Why:** identifiers must never enter embeddings.
- [ ] Write `semantic_search(query_text)`: embed the query, then `SELECT screened_document_id, section, 1 - (embedding <=> :q) AS sim FROM document_embeddings ORDER BY embedding <=> :q LIMIT 200;` (200 is only the candidate pool; the final cutoff comes from the ranking issue).
- [ ] Group by document, keep the best section as evidence.
- [ ] Compare MiniLM against one biomedical model on the dev queries (recall@10). Store `model_name` so both can live side by side. Keep the better one and record the result in `docs/decisions/0002-embedding-model.md`. **Why:** a measured choice beats a guess.
- [ ] Do not present raw similarity as a clinical probability anywhere.

## Done when
- [ ] A reworded query with no shared keywords still finds the right notes on the dev set
EOF

issue 3 "type: learning,area: search" "learning: clinical context and negation (NegEx and ConText)" <<'EOF'
## Goal
Understand how clinical NLP decides whether a finding is present, negated, uncertain, historical, or about a relative.

## Purpose
"Denies chest pain" and "reports chest pain" share words but mean opposite things. This is our key differentiator, so we must understand it deeply.

## Resources
- Chapman et al. (2001): NegEx algorithm paper (search "A simple algorithm for identifying negated findings and diseases in discharge summaries")
- Harkema et al. (2009): ConText algorithm paper
- medspaCy docs and README (ConText component, target rules)

## Tasks
- [ ] Read both abstracts and the NegEx trigger-term idea.
- [ ] Run medspaCy on 10 hand-written sentences covering negation, uncertainty, history, and family history; print each entity's `ent._.is_negated`, `is_uncertain`, `is_historical`, `is_family`.
- [ ] Write `docs/notes/05-negation-context.md`: how the algorithm works, scope of a negation ("denies chest pain but reports cough"), and 5 cases where it is likely to fail.

## Done when
- [ ] Note merged with a table of sentence, expected tag, actual tag
EOF

issue 3 "type: feature,area: search" "feat: context tagging of findings at index time (medspaCy)" <<'EOF'
## Goal
Tag every finding in each approved note and use the tags in search.

## Purpose
This stops "denies chest pain" from appearing as a clean match for "chest pain", and it powers the "no fever" exclusion.

## Resources
- medspaCy: `medspacy.ner.TargetRule`, `medspacy.context`
- docs/notes/05-negation-context.md from the learning issue

## Tasks
- [ ] Define target rules from `clinical_terms` (each preferred term and its synonyms become a `TargetRule` with the concept as category).
- [ ] Write `backend/app/services/context.py`: `tag_findings(text) -> list[Finding(concept, span, negated, uncertain, historical, family)]`.
- [ ] Add a `finding_tags` table (screened_document_id, concept, start, end, negated, uncertain, historical, family) with a migration. Fill it when a document is approved. **Why:** run the slow NLP once, keep search fast.
- [ ] Update ranking inputs: a document whose only mention of a searched finding is negated, family, or historical is marked `context_flag` and demoted; documents containing an **excluded** query finding as present are dropped.
- [ ] Return flags in the evidence ("chest pain: negated").
- [ ] Build the negation test set from notes tagged `negation`, `history`, `family` and print accuracy to `evaluation/results/negation.json`.
- [ ] Keep `docs/notes/06-context-failures.md` listing every failure and why.

## Done when
- [ ] "chest pain" does not return a note that only says "denies chest pain" as a clean match, and accuracy is recorded
EOF

issue 3 "type: feature,area: search" "feat: fusion, ranking, cutoff, evidence and POST /cases/search" <<'EOF'
## Goal
Combine all retrievers into one ranked list that returns all relevant cases, each with an explanation.

## Purpose
This is what the doctor experiences as "search works". Weights must come from data and every result must explain itself.

## Resources
- Cormack et al. (2009) RRF paper
- scikit-learn `ParameterGrid` (for the weight grid search)

## Tasks
- [ ] Write `services/ranking.py`: merge candidates by document id, normalize each score to 0..1.
- [ ] Implement weighted fusion `score = wk*K + wt*T + ws*S` and Reciprocal Rank Fusion. Tune the weights by grid search on the **dev** queries only, maximizing MRR then Recall@5. Compare against RRF and keep the better. **Why:** weights from evidence, not guesses.
- [ ] Choose a relevance cutoff on the dev set (maximize F1 at the cutoff). **Why:** returns all relevant cases without flooding the doctor.
- [ ] Write `services/evidence.py`: for each result return `matched_findings`, `match_type` (exact, synonym, semantic), best snippet, context flags, and `Matched X of Y`. **Why:** every result shows why it appeared.
- [ ] `POST /cases/search` with body `{symptoms, department?, document_type?, page, page_size}`; response includes `total_count`, `parsed_query`, and results. Paginate, never truncate the total.
- [ ] Never expose a percentage as a clinical probability. Use "Matched 3 of 4 findings".
- [ ] Write `evaluation/tuning_log.md` with the weights tried and the winner.

## Done when
- [ ] The endpoint returns every relevant case above the cutoff with evidence, and beats keyword-only on the dev set
EOF

# ===================== PHASE 4: ACCESS CONTROL AND PROVENANCE ===============
issue 4 "type: feature,area: backend" "feat: authentication, roles, provenance endpoints and audit log" <<'EOF'
## Goal
Login, role checks on every route, provenance endpoints, and a log of every search, view, and export.

## Purpose
Real access control must live in the backend. Hiding things in the UI is not security. Audit logs give accountability.

## Resources
- FastAPI docs: "Security" tutorial (OAuth2 with Password and JWT)
- passlib bcrypt docs
- HL7 FHIR: AuditEvent and Provenance resources (read for ideas only)

## Tasks
- [ ] `pip install pyjwt "passlib[bcrypt]"`. Seed demo users: one `doctor`, one `privacy_reviewer`, one `admin`, with bcrypt-hashed passwords.
- [ ] `POST /auth/login` returns a JWT (short expiry). Write a `get_current_user` dependency.
- [ ] Write `require_role(*roles)` and apply it: doctors -> search and view; reviewers -> review queue; admins -> audit logs and ingest.
- [ ] `GET /documents/{id}` returns screened text, redaction summary, and context-tagged highlights. `GET /documents/{id}/provenance` returns author (only if the policy flag `SHOW_AUTHOR_NAMES` is true), department, document type, created date, screening status, redactions, method, reviewed_by. **Why:** author visibility is a hospital policy decision, not an assumption.
- [ ] No route may return `original_text` to a doctor. Only a reviewer-only route returns it for the side-by-side view.
- [ ] Write `services/audit.py` with `log(user, action, document_ids, detail)` called by search, document view, review actions, and export. `GET /audit-logs` is admin-only with filters.
- [ ] pytest: unauthenticated request returns 401; a doctor on `/review/queue` returns 403; a doctor cannot get original text; every search and view creates an audit row.

## Done when
- [ ] All access tests pass and audit rows exist for each action
EOF

# ============================ PHASE 5: FRONTEND =============================
issue 5 "type: learning,area: frontend" "learning: React, TypeScript, Tailwind and accessible UI primitives" <<'EOF'
## Goal
Get the mental model needed to build a fast, accessible clinical UI.

## Purpose
The UI must be quick to use under pressure. Accessibility and keyboard behavior are requirements, not extras.

## Resources
- React docs: https://react.dev/learn (Quick Start, Thinking in React)
- TypeScript Handbook: everyday types, interfaces, unions
- Tailwind docs: https://tailwindcss.com/docs (dark mode, theme config)
- Radix UI Primitives: https://www.radix-ui.com/primitives
- TanStack Query docs: https://tanstack.com/query/latest (Overview, Queries)
- WebAIM contrast checker: https://webaim.org/resources/contrastchecker/

## Tasks
- [ ] Work through React's Quick Start and Thinking in React.
- [ ] Build a tiny practice component with a Radix `Dialog` and tab through it with the keyboard.
- [ ] Check contrast for a candidate palette (text on a translucent dark card) and note which combinations pass 4.5:1.
- [ ] Write `docs/notes/07-frontend-basics.md`: components, props, state, effects, server state vs UI state, and what keyboard focus order means.

## Done when
- [ ] Note merged
EOF

issue 5 "type: chore,area: frontend" "chore(frontend): scaffold Vite + React + TypeScript + Tailwind + tooling" <<'EOF'
## Goal
A running, linted, tested frontend project that can talk to the backend.

## Purpose
Every screen builds on this foundation.

## Resources
- Vite guide: https://vite.dev/guide/
- Vitest docs, Playwright docs

## Tasks
- [ ] `npm create vite@latest frontend -- --template react-ts` and `cd frontend && npm install`.
- [ ] Install Tailwind (follow the current Vite guide), `react-router-dom`, `@tanstack/react-query`, `lucide-react`, and Radix packages as needed (`@radix-ui/react-dialog`, `-tabs`, `-dropdown-menu`, `-tooltip`).
- [ ] Add ESLint and Prettier; scripts: `npm run lint`, `npm run build`, `npm test` (Vitest).
- [ ] Create `src/services/api.ts`: a small `fetch` wrapper that adds the JWT and handles 401 by redirecting to login. Configure a Vite dev proxy to the FastAPI port. **Why:** avoids CORS problems during development.
- [ ] Generate TypeScript types from the backend OpenAPI schema (`npx openapi-typescript http://localhost:8000/openapi.json -o src/services/schema.d.ts`). **Why:** frontend and backend cannot silently drift apart.
- [ ] Short `frontend/README.md`.

## Done when
- [ ] `npm run dev` shows a page; lint, build, and test pass
EOF

issue 5 "type: feature,area: frontend" "feat(frontend): design system and app shell (dark glass UI)" <<'EOF'
## Goal
Tokens, reusable components, sidebar, and top bar in a dark glass style that stays fast and readable.

## Purpose
Every screen reuses these pieces. The look follows the dark gradient dashboard reference; readability and speed come first.

## Resources
- Tailwind docs: theme extension, `backdrop-blur`, CSS variables for theming
- Radix UI Primitives
- WCAG 2.1: contrast (1.4.3) and non-text contrast (1.4.11)

## Tasks
- [ ] Define tokens as CSS variables mapped in `tailwind.config`: background `#0B0D1F`, glass surface `rgba(255,255,255,0.06)` with a 1px border, violet accent `#7C5CFF`, blue accent `#3B82F6`, plus success, warning, danger.
- [ ] Verify body text is at least 4.5:1 on every surface and minimum 14px. **Why:** dark glass is easy to make unreadable.
- [ ] Never use color alone for status: each status has an icon and a label.
- [ ] Add a light theme using CSS variables and a toggle stored in memory plus `prefers-color-scheme`. **Why:** bright wards make dark UIs hard to read.
- [ ] Build components: `GlassCard`, `Chip`, `StatusBadge`, `Button`, `EmptyState`, `Skeleton`, `Dialog` (Radix), `Tooltip`.
- [ ] Build the shell: left icon sidebar (Home, Search, Review Queue, Audit, Settings) with labels on hover and an active-item highlight; top bar with user name, role, and theme toggle. Hide reviewer/admin links for other roles (the backend still enforces).
- [ ] Global shortcuts via a small `useHotkeys` hook: `/` focuses search, `Esc` closes the top dialog or goes back, `?` opens a shortcuts help dialog.
- [ ] Add `:focus-visible` rings that meet contrast requirements.
- [ ] Login page and route guards (redirect when unauthenticated).

## Done when
- [ ] Shell renders with sidebar, top bar, theme toggle, shortcuts, and passes a manual contrast check
EOF

issue 5 "type: feature,area: frontend" "feat(frontend): dashboard home with clinical widgets" <<'EOF'
## Goal
A home screen of glass widgets that puts the most useful actions one click away.

## Purpose
The reference design uses widgets. We keep the look but fill it with time-saving clinical content only.

## Resources
- TanStack Query: caching and `useQuery`
- CSS Grid guide (MDN)

## Tasks
- [ ] Greeting header with doctor name, department, and date.
- [ ] Large search input at the top that submits to the search page and is focused on load.
- [ ] Widgets: Recent searches (re-run in one click), Recently viewed cases, Saved case set (selected for PDF), Review queue count (reviewers only), Approved-documents count. Add small backend endpoints (`GET /me/recent-searches`, `GET /me/recent-views`) fed by the audit log.
- [ ] Do not add decorative widgets (music, habits, weather). **Why:** clutter slows scanning.
- [ ] Use skeleton loaders and TanStack Query caching so the page never feels blocked.
- [ ] Responsive grid that stacks on tablet width.

## Done when
- [ ] A doctor reaches a search or a recent case in one click from home
EOF

issue 5 "type: feature,area: frontend" "feat(frontend): search screen and results list with query chips" <<'EOF'
## Goal
The core experience: search, understand why each result appeared, and move through results quickly.

## Purpose
Doctors need speed and trust. Chips show how the system understood them; evidence shows why each case matched.

## Resources
- TanStack Query: `useMutation` or `useQuery` with keys
- Radix `Tooltip` for match-reason details

## Tasks
- [ ] Large symptom input, department filter, Search button; `Enter` submits.
- [ ] After parsing, show query chips (for example "difficulty breathing -> dyspnea"; excluded findings crossed out). Chips can be removed or toggled to exclude, which re-runs the search. **Why:** doctors can correct a misread instantly.
- [ ] Show result count ("23 matching cases") and pagination (20 per page).
- [ ] Result card: department, document type, excerpt with matched words highlighted, "Matched 3 of 4", context flags, privacy badge, select checkbox.
- [ ] Keyboard navigation: `j`/`k` move, `Enter` opens, `x` selects for the PDF. Show the focused card clearly.
- [ ] Sticky filter bar (department, document type, date range).
- [ ] Empty state ("No matching cases. Try fewer or broader terms") and error state with retry.
- [ ] A short notice that this searches historical documentation, not diagnoses.
- [ ] Vitest component tests for chips and result cards; one Playwright test: log in, search, open a result with the keyboard.

## Done when
- [ ] A doctor can search, scan explained results, open and select cases using only the keyboard
EOF

issue 5 "type: feature,area: frontend" "feat(frontend): document viewer with highlights and provenance panel" <<'EOF'
## Goal
Show the exact screened original wording, highlighted matches, redaction markers, and a provenance panel.

## Purpose
Our differentiator: doctors read what the original clinician wrote and see where it came from and what was removed.

## Resources
- React docs: rendering lists, `dangerouslySetInnerHTML` warnings (we avoid it; render highlight spans as components)
- Radix `Tabs`

## Tasks
- [ ] Two-column layout: note text on the left, provenance panel on the right (stacks on small screens).
- [ ] Render the note by splitting text into segments (plain, match, synonym-match, redaction, context-flagged) from API offsets, as React components. **Why:** no raw HTML injection.
- [ ] Highlight matches, including synonyms with a tooltip ("you searched difficulty breathing; note says dyspnea").
- [ ] Style redactions as obvious tags such as `[REDACTED-NAME]`.
- [ ] Provenance panel: author (if policy allows), department, document type, created date, screening status, redaction summary by type, screening method, reviewed by.
- [ ] Inline context flags (negated, historical, family) with icon plus label.
- [ ] "Back to results" restores scroll position and selection; `Esc` goes back.
- [ ] "Add to report" button and a selected-count bar.
- [ ] Viewing a document triggers the audit log through the backend (already logged server-side; verify in the UI test).

## Done when
- [ ] Opening a case shows highlighted text, redaction tags, and full provenance, and returning to results is instant
EOF

issue 5 "type: feature,area: frontend" "feat(frontend): reviewer queue and admin audit screens" <<'EOF'
## Goal
Screens for privacy reviewers (approve or reject) and admins (audit log).

## Purpose
Shows that human review is a real part of the system, not a claim on a slide.

## Resources
- TanStack Query: mutations and cache invalidation
- Radix `Dialog` for the reject-reason prompt

## Tasks
- [ ] Queue list sorted with "needs manual review" first, showing status, department, redaction counts.
- [ ] Side-by-side view: original on the left (reviewer-only route), screened on the right with redactions highlighted.
- [ ] Approve button; Reject opens a dialog requiring a reason.
- [ ] Shortcuts: `a` approve, `r` reject, `n` next, `p` previous.
- [ ] After approve, trigger embedding build for that document (call the backend hook) and invalidate the queue query.
- [ ] Admin audit table with filters (user, action, date) and a "Download CSV" button.
- [ ] Route guards that mirror backend roles.

## Done when
- [ ] A reviewer approves a pending note and it becomes searchable; an admin sees both actions in the audit table
EOF

# ============================ PHASE 6: EXPORT, EVAL, SHIP ===================
issue 6 "type: feature,area: backend" "feat: PDF report export (ReportLab) with leak check" <<'EOF'
## Goal
Export selected cases as a PDF from screened data only, with a disclaimer on every page.

## Purpose
Doctors want to take or share matching cases. The PDF is a common leak path, so it gets its own test.

## Resources
- ReportLab User Guide: https://docs.reportlab.com/ (Platypus, `SimpleDocTemplate`, page templates)

## Tasks
- [ ] `pip install reportlab`. Write `backend/app/services/report.py` with `build_report(case_ids, search_info) -> bytes`.
- [ ] Use `SimpleDocTemplate`, `Paragraph`, `Spacer`, `PageBreak`, `getSampleStyleSheet`. Include search terms, date, department, then for each case: document type, department, author (if policy allows), screening status, screened text.
- [ ] Draw the footer on every page with `onFirstPage` and `onLaterPages`: "This report contains historical clinical documentation for professional reference. Similarity does not establish equivalent diagnosis or treatment suitability. All clinical decisions remain the responsibility of the treating professional."
- [ ] Read only through `get_searchable_documents()`.
- [ ] Return bytes from `io.BytesIO` (nothing written to disk). `POST /reports` returns `application/pdf`.
- [ ] Frontend: selected-count bar with a "Generate PDF" button that downloads the blob; log the export.
- [ ] Extract text from the PDF (`pypdf`) in a test and run `assert_no_leaks` against the planted identifiers.

## Done when
- [ ] A 3-case PDF has the footer on every page and zero planted identifiers
EOF

issue 6 "type: feature,area: eval" "feat: evaluation harness, baselines and failure analysis" <<'EOF'
## Goal
Measure retrieval quality and compare four systems on the held-out test queries.

## Purpose
This is our proof. Real numbers turn "it seems to work" into "here is how well it works".

## Resources
- Manning et al., Introduction to Information Retrieval, chapter 8
- `matplotlib` docs (bar chart)

## Tasks
- [ ] Write `evaluation/run_eval.py` that runs each query through four systems: keyword-only, semantic-only, hybrid, hybrid plus context handling. **Why:** the ablation shows what each component adds.
- [ ] Compute Precision@5, Recall@5, MRR, and precision/recall/F1 at the cutoff. **Why:** top-5 metrics alone do not test "return all relevant cases".
- [ ] Report negation accuracy from the context issue and redaction recall from the leak report.
- [ ] Measure latency (median and 95th percentile) over 100 searches.
- [ ] Tune only on dev; report only on test. Save `evaluation/results/results.md` and a `results.csv`.
- [ ] Make one bar chart comparing the four systems for the slides.
- [ ] Write `docs/notes/08-failure-analysis.md`: 3 to 5 failed queries, why they failed, and what we would try next.

## Done when
- [ ] Results table, chart, and failure analysis exist and `python evaluation/run_eval.py` reruns end to end
EOF

issue 6 "type: chore,area: infra" "chore: CI pipeline and security hardening" <<'EOF'
## Goal
Every pull request automatically runs our tests, and basic protections are in place.

## Purpose
Privacy is our central claim; tests must run on every change and stop regressions before merge.

## Resources
- GitHub Actions docs: workflow syntax and service containers
- slowapi README (rate limiting for FastAPI)
- Pydantic docs: field constraints

## Tasks
- [ ] Create `.github/workflows/ci.yml`: backend job with a `pgvector/pgvector:pg16` service container, `pip install -r backend/requirements.txt`, spaCy model downloads, `alembic upgrade head`, seed, `pytest`; frontend job with `npm ci`, lint, build, test.
- [ ] Update the `main` ruleset to require both jobs. Add a CI badge to the README.
- [ ] Add `slowapi` rate limits to `/auth/login` and `/cases/search`.
- [ ] Add Pydantic length and character limits on all request bodies.
- [ ] Restrict CORS to the frontend origin; keep secrets only in `.env`.
- [ ] Add a test that proves no unapproved document can appear in search or the PDF.
- [ ] Run `git log --all -- .env` and confirm it prints nothing.

## Done when
- [ ] A deliberately failing PR is blocked, then fixed and merged
EOF

issue 6 "type: docs" "docs: demo script, README, slides and pitch answers" <<'EOF'
## Goal
A reliable demo and clear documentation.

## Purpose
A strong project can still lose with a broken or confusing demo. This makes judges understand it fast and see it work.

## Resources
- Your own `docs/notes/` files (reuse them)
- A screen recorder (QuickTime on macOS or OBS)

## Tasks
- [ ] Write `scripts/reset_demo.sh` that recreates the database, seeds, approves everything except two pending demo notes, and builds embeddings. **Why:** the demo must be repeatable.
- [ ] Write `docs/demo_script.md` (about 4 minutes): login, search "difficulty breathing and chest discomfort", show query chips, open a case, point out redactions and provenance, show a negation case, approve a pending note as reviewer and search again, export the PDF, show the evaluation chart, show the audit log.
- [ ] Record a backup video of the full demo and take screenshots. **Why:** Wi-Fi and Docker fail at the worst time.
- [ ] README: pitch, architecture diagram, setup, screenshots, results table, privacy claims and limits, related work (EMERSE, SemEHR), future work (FHIR, SNOMED CT/UMLS, SSO, encryption, expert determination).
- [ ] 5 slides: problem, solution and demo, why it is different, evaluation results, privacy and limitations.
- [ ] Prepare answers to: "Isn't this just search?", "Is it HIPAA compliant?", "Can embeddings leak data?", "How do you know it works?", "How is this different from EMERSE or SemEHR?".
- [ ] Do a full run from a fresh clone on a teammate's laptop and fix whatever breaks.

## Done when
- [ ] A teammate runs the whole demo from a fresh clone with no help
EOF

# --------------------------------------------------------------------- epics
echo; echo "== Epics =="
epic() { # phase title blurb
  local p="$1" title="$2" blurb="$3" tasks body url
  tasks="$(cat "$TMP/phase-$p" 2>/dev/null || true)"
  body="$blurb

## Tasks
$tasks

_GitHub ticks these boxes automatically when the linked issues close._"
  if [ "$DRY_RUN" = "1" ]; then echo "[dry-run] epic: $title"; return; fi
  url="$(gh issue create --title "$title" --body "$body" --label "type: epic" --milestone "$(ms_title "$p")")"
  echo "created epic: $title"
  echo "$url" >> "$TMP/urls"
}

epic 1 "Epic: Phase 1 - Foundation" "Repo, Docker database, schema, synthetic data, labeled queries."
epic 2 "Epic: Phase 2 - Privacy pipeline" "Screening, leak tests, reviewer workflow."
epic 3 "Epic: Phase 3 - Search engine" "Query parsing, keyword, semantic, context, fusion."
epic 4 "Epic: Phase 4 - Access control and provenance API" "Auth, roles, provenance, audit log."
epic 5 "Epic: Phase 5 - Frontend" "Design system, dashboard, search, viewer, reviewer and admin screens."
epic 6 "Epic: Phase 6 - Export, evaluation and ship" "PDF, evaluation, CI, demo."

# ------------------------------------------------------------ projects board
if [ "$WITH_PROJECT" = "1" ] && [ "$DRY_RUN" != "1" ]; then
  echo; echo "== Project board =="
  OWNER="$(gh repo view --json owner --jq .owner.login)"
  NUM="$(gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json \
        | python3 -c 'import sys, json; print(json.load(sys.stdin)["number"])')"
  while read -r url; do
    gh project item-add "$NUM" --owner "$OWNER" --url "$url" >/dev/null
  done < "$TMP/urls"
  echo "Board #$NUM created with all issues."
fi

echo; echo "Done. Next steps:"
echo "  1. Open the Issues tab and check the milestones."
echo "  2. Start with Phase 1, issue 1: branch -> PR -> squash merge."
