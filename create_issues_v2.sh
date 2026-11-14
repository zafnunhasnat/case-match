#!/usr/bin/env bash
# Creates all 20 CaseMatch issues in the current repo.
# Run from inside your casematch-ai folder, after `gh auth login`.
# Run it ONCE (running twice creates duplicates).
set -e

create_issue() {
  local title="$1"
  local body
  body="$(cat)"
  gh issue create --title "$title" --body "$body"
}

# ---------------------------------------------------------------- 1
create_issue "Issue 1: Repo, Docker and development environment" <<'EOF'
## Issue
Create the GitHub repo structure and a Docker-based environment so every teammate can start the whole project (database, backend, frontend) with the same commands.

## Purpose
Without a shared setup, the project works on one laptop and breaks on the next. Every later issue depends on this one.

## Tasks
- [ ] **Create the folders** `backend/app/{api,services,models,database}`, `backend/tests`, `frontend/`, `evaluation/`, `data/synthetic_cases`, `scripts/`. **Why:** separating search, privacy, and provenance code makes debugging and testing easier.
- [ ] **Write `docker-compose.yml`** with the image `pgvector/pgvector:pg16` (port 5432, password from `.env`). **Why:** this image is Postgres with pgvector already installed, so nobody compiles extensions by hand.
- [ ] **Create the backend project** with FastAPI and `uvicorn`, and a `/health` endpoint. **Why:** a working skeleton lets everyone test their code immediately.
- [ ] **Create the frontend project** with `npm create vite@latest frontend -- --template react`, then add Tailwind CSS. **Why:** Vite starts in under a second, which keeps development fast.
- [ ] **Create `requirements.txt`**: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pgvector`, `pydantic-settings`, `pyjwt`, `passlib[bcrypt]`, `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `medspacy`, `sentence-transformers`, `reportlab`, `faker`, `pandas`, `pytest`, `httpx`. **Why:** pinning one list keeps versions identical across laptops.
- [ ] **Download spaCy models**: `python -m spacy download en_core_web_lg` (Presidio) and `en_core_web_sm` (medspaCy). **Why:** each library expects its own model.
- [ ] **Add `.env.example`** (`DATABASE_URL`, `JWT_SECRET`) and put `.env` in `.gitignore`. **Why:** secrets must never be committed.
- [ ] **Write a README "How to run"** section. **Why:** a fresh clone must work with no help.

**Done when:** a teammate clones the repo, follows the README, and sees `/health` return OK and the React page load.
EOF

# ---------------------------------------------------------------- 2
create_issue "Issue 2: Database schema and migrations" <<'EOF'
## Issue
Design and create the PostgreSQL tables for doctors, original documents, screened documents, embeddings, clinical terms, and audit logs.

## Purpose
The privacy design depends on the database: original notes must be stored separately from the screened copies that search uses. If this is wrong, privacy and provenance break later.

## Tasks
- [ ] **Define models with SQLAlchemy 2** for: `doctors`, `clinical_documents` (restricted originals), `screened_documents`, `document_embeddings`, `clinical_terms`, `search_audit_logs`. **Why:** an ORM keeps the schema in one readable place and prevents SQL typos.
- [ ] **Store provenance fields on the source record**: `original_author_id`, `department`, `document_type`, `created_at`, and on the screened record `screening_status`, `redactions_applied`, `screening_method`, `reviewed_by`. **Why:** the author and the reviewer must be separate fields so redaction never overwrites the author.
- [ ] **Add a `search_vector` tsvector column** to `screened_documents` with a GIN index. **Why:** this is what makes PostgreSQL full-text search fast.
- [ ] **Add a `vector(384)` column** in `document_embeddings` with an HNSW index (`vector_cosine_ops`). **Why:** 384 matches the MiniLM model; HNSW gives fast similarity search. Store `model_name` so we can compare models later.
- [ ] **Enable the extension** with `CREATE EXTENSION IF NOT EXISTS vector;` inside the first migration. **Why:** keeps setup repeatable.
- [ ] **Set up Alembic migrations.** **Why:** the team can change the schema without wiping each other's databases.
- [ ] **Create two database roles**: `app_user` (can read `screened_documents` only) and `admin_user`. **Why:** even a bug in search code cannot read original notes.

**Done when:** `alembic upgrade head` builds all tables from scratch and `app_user` is blocked from selecting `clinical_documents`.
EOF

# ---------------------------------------------------------------- 3
create_issue "Issue 3: Synthetic clinical notes and labeled test queries" <<'EOF'
## Issue
Generate 150 to 300 fictional clinical notes with planted identifiers and hard cases, plus 25 to 40 test queries with the correct matching notes recorded.

## Purpose
The project is only as convincing as its data. The labeled queries are our proof that search works, so they must exist before we build search.

## Tasks
- [ ] **Write note templates** by symptom group (respiratory, cardiac, GI, neurological) in `scripts/generate_data.py`. **Why:** templates give control over exactly what each note says, which we need for labeling.
- [ ] **Vary the language**: synonyms (dyspnea, shortness of breath, trouble breathing), abbreviations (SOB, CP, HTN), typos, short and long notes. **Why:** real notes are messy, and synonym handling needs something to prove.
- [ ] **Add the hard cases on purpose**: negation ("denies chest pain"), history ("history of migraines"), family history ("mother had MI"), uncertainty ("possible pneumonia"). **Why:** these are where naive search fails, and our best differentiator.
- [ ] **Plant identifiers** with Faker: names, DOBs, phone numbers, MRNs, addresses, plus subtle ones (rare job, small town, specific event). Save a `planted_identifiers.json` listing every one. **Why:** this list is the answer key for leak tests.
- [ ] **Create 6 to 8 fake doctors** across Emergency, Internal Medicine, Pediatrics, Cardiology. **Why:** provenance needs authors and departments.
- [ ] **Write `evaluation/labeled_queries.json`**: each query with the note IDs that should and should not match. Split it into a **dev set** (tune on this) and a **test set** (report on this). **Why:** tuning and reporting on the same data would make our numbers look better than they are.
- [ ] **Optional realism:** compare a few notes against public samples such as MTSamples (check the license first). **Why:** helps confirm the fake notes look believable.

**Done when:** 150+ notes, a planted-identifier list, and 25+ labeled queries (dev/test split) are committed. Real patient data is never used.
EOF

# ---------------------------------------------------------------- 4
create_issue "Issue 4: Privacy screening pipeline" <<'EOF'
## Issue
Build the pipeline that turns an original note into a privacy-screened copy by detecting and redacting patient identifiers while keeping the clinician's wording.

## Purpose
Doctors will read other doctors' notes. Patient identity must not leak into the display copy, the search index, the embeddings, or the PDF.

## Tasks
- [ ] **Detect with Presidio Analyzer** (`PERSON`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `DATE_TIME`, `LOCATION`) in `services/privacy.py`. **Why:** a maintained open-source tool beats writing detection from scratch.
- [ ] **Add custom recognizers with regex** for MRNs, phone formats, and hospital-style IDs. **Why:** Presidio does not know our ID formats.
- [ ] **Replace matches with visible tags** like `[REDACTED-NAME]` using Presidio Anonymizer. **Why:** doctors should see that something was removed and what type.
- [ ] **Generalize dates** (for example, keep month and year or use `[DATE]`) and document the rule. **Why:** exact dates can identify a person, but clinical timing ("three days") must stay.
- [ ] **Flag risky notes** with a simple rule (rare occupations, very small towns, unusual events) as `needs_manual_review`. **Why:** automated tools miss indirect identifiers, so a human should look at the risky ones.
- [ ] **Record `redactions_applied`, `screening_method`, and the redaction counts by type** on the screened record. **Why:** the viewer must show what was redacted.
- [ ] **Never modify the original.** Write only to `screened_documents`. **Why:** the source must stay immutable.
- [ ] **Write a leak test** that runs all planted identifiers through the pipeline and fails if any survive. **Why:** this gives us a measurable redaction recall by entity type.
- [ ] **Document the honest claim** in the README: "privacy-screened with automated tools plus human review", not "HIPAA compliant". Mention HHS Safe Harbor and Expert Determination. **Why:** overclaiming would hurt credibility with judges.

**Done when:** the leak test reports zero planted identifiers in screened text, and redaction recall per entity type is written down.
EOF

# ---------------------------------------------------------------- 5
create_issue "Issue 5: Ingestion and reviewer workflow (backend)" <<'EOF'
## Issue
Create the process that moves a document from "pending" to "approved", and only index approved documents.

## Purpose
Screening is never perfect. A human approval step, and a rule that only approved text is searchable, is what makes the privacy design trustworthy.

## Tasks
- [ ] **Define the statuses** `pending`, `screened`, `reviewed`, `approved`, `failed`. **Why:** clear states make the workflow testable.
- [ ] **Write `scripts/seed_database.py`** that loads synthetic notes, runs screening, and stores results. **Why:** a seed script replaces a full upload system, saving time while still proving the pipeline.
- [ ] **Build `POST /documents/ingest`** that stores the original, runs screening, and sets status to `screened`. **Why:** shows how real documents would enter the system.
- [ ] **Build `GET /review/queue`** and `POST /review/{id}/approve|reject` for the `privacy_reviewer` role. **Why:** gives the human-in-the-loop step.
- [ ] **Index only on approval**: on approve, build the `search_vector` and create embeddings. **Why:** unreviewed text must never reach the search index or embeddings.
- [ ] **Record `reviewed_by` and the time** on approval, separate from the original author. **Why:** keeps provenance accurate.

**Done when:** a seeded document appears in the queue, becomes searchable only after approval, and a rejected one never appears in search.
EOF

# ---------------------------------------------------------------- 6
create_issue "Issue 6: Query understanding (terminology and parser)" <<'EOF'
## Issue
Turn typed text like "no fever but difficulty breathing and chest discomfort for 3 days" into structured findings with synonyms, negations, and duration.

## Purpose
Doctors do not type perfect keywords. This step makes "difficulty breathing" find notes that say "dyspnea", and it prevents "no fever" from matching fever notes.

## Tasks
- [ ] **Create the `clinical_terms` table and a curated synonym file** of 100 to 200 terms (preferred term, synonyms, abbreviations, optional code). **Why:** SNOMED CT and UMLS need licensing, so a small curated list is realistic for now and we name the real ones as the future path.
- [ ] **Parse the query with spaCy** (noun chunks plus splitting on commas and "and"). **Why:** handles both short phrases and full sentences.
- [ ] **Normalize each finding** to its preferred concept (for example, "trouble breathing" becomes dyspnea). **Why:** one concept id lets all retrievers agree on what was asked.
- [ ] **Detect negation in the query** with medspaCy ("no fever", "denies cough") and mark that finding as excluded. **Why:** doctors search for absent findings too, and treating them as present gives wrong results.
- [ ] **Extract duration** with regex and spaCy `DATE` entities. **Why:** useful for display and for later ranking.
- [ ] **Return the parsed result as JSON** (`findings`, `excluded`, `duration`). **Why:** the UI shows these as editable chips so the doctor can correct a misread.
- [ ] **Write pytest tests** with 10 example queries. **Why:** protects the parser from regressions.

**Done when:** the example query above returns three findings (one excluded) plus the duration, and all 10 tests pass.
EOF

# ---------------------------------------------------------------- 7
create_issue "Issue 7: Keyword and terminology retrieval" <<'EOF'
## Issue
Implement the two exact-matching retrievers: PostgreSQL full-text search and synonym-based matching, returning every candidate with its evidence.

## Purpose
This is the reliable base of search. It is easy to explain, fast, and finds exact wording that embeddings can blur.

## Tasks
- [ ] **Full-text search** in `services/keyword_search.py` using `to_tsquery` and `ts_rank` on `screened_documents.search_vector`. **Why:** built into Postgres, fast, and no extra service to run.
- [ ] **Terminology search**: for each finding, match any of its synonyms (one group counts once). **Why:** a note saying "dyspnea" should count as matching "difficulty breathing" exactly one time.
- [ ] **Return all candidates, with no `LIMIT`**, plus `matched_findings`, `total_findings`, and the matched snippet. **Why:** the product promise is every relevant case, and the snippet powers the evidence display.
- [ ] **Add filters** for department, document type, and date. **Why:** doctors often want to narrow to their specialty.
- [ ] **Use parameterized queries only.** **Why:** prevents SQL injection from typed symptoms.
- [ ] **Search only approved screened documents.** **Why:** enforces the privacy rule.
- [ ] **Write pytest tests**, including the synonym case. **Why:** proves terminology matching works.

**Done when:** "difficulty breathing" returns "shortness of breath" and "dyspnea" notes, with snippets and match counts.
EOF

# ---------------------------------------------------------------- 8
create_issue "Issue 8: Semantic retrieval with embeddings" <<'EOF'
## Issue
Add meaning-based search that finds relevant notes even when the wording differs, using embeddings stored in pgvector.

## Purpose
Synonym tables never cover everything. Semantic search catches phrasing our dictionary misses.

## Tasks
- [ ] **Embed with Sentence Transformers** using `all-MiniLM-L6-v2` as the baseline. **Why:** small, fast, runs on a laptop with no API.
- [ ] **Embed per section** (chief complaint, history, assessment), not the whole note. **Why:** long notes blur into one vector and lose detail.
- [ ] **Embed only approved screened text.** **Why:** identifying text must never enter embeddings.
- [ ] **Search with the pgvector cosine operator `<=>`** in `services/semantic_search.py`, convert to similarity (`1 - distance`). **Why:** native to our database.
- [ ] **Compare a biomedical model** (for example `S-PubMedBert-MS-MARCO`, verify the exact name on Hugging Face) against MiniLM on the dev set. Keep the better one. **Why:** a measured model choice is stronger than a guess.
- [ ] **Return the best matching section** as evidence. **Why:** the viewer needs to show why a note matched.
- [ ] **Never show raw similarity as a clinical probability.** **Why:** it is not one, and presenting it that way misleads.

**Done when:** a reworded query with no shared keywords still finds the right notes on the dev set.
EOF

# ---------------------------------------------------------------- 9
create_issue "Issue 9: Context and negation handling" <<'EOF'
## Issue
Tag every finding in each note as present, negated, uncertain, historical, or family history, and use those tags in search.

## Purpose
"Denies chest pain" and "reports chest pain" share words but mean opposite things. Handling this correctly is our biggest technical differentiator.

## Tasks
- [ ] **Use medspaCy (ConText)** to attach context attributes to each finding in a note. **Why:** a tested clinical-context tool beats hand-written rules.
- [ ] **Run it at indexing time** and store the tags per finding. **Why:** doing the work once keeps search fast.
- [ ] **Demote or flag documents** where the only mention of a searched finding is negated, family, or historical. **Why:** they should not look like clean matches.
- [ ] **Support excluded findings** from the query (Issue 6): drop notes where an excluded finding is present. **Why:** completes the "no fever" behavior.
- [ ] **Return context flags** in the evidence ("chest pain: negated"). **Why:** doctors see why a case was demoted.
- [ ] **Build a negation test set** from the hard cases in Issue 3 and report accuracy. **Why:** this becomes a headline number in the presentation.
- [ ] **Keep a list of failures.** **Why:** an honest failure analysis builds trust.

**Done when:** "chest pain" does not return a note that only says "denies chest pain" as a clean match, and negation accuracy is measured.
EOF

# ---------------------------------------------------------------- 10
create_issue "Issue 10: Fusion, ranking, cutoff and evidence" <<'EOF'
## Issue
Combine terminology, keyword, and semantic results into one ranked list that returns all relevant cases, with a clear explanation for each.

## Purpose
This is the part the doctor experiences as "search works". Ranking must be tuned on data, and every result must explain itself.

## Tasks
- [ ] **Merge candidates** from the three retrievers into one list per document. **Why:** one document may be found by several methods.
- [ ] **Start with a weighted score** (for example 0.4 keyword, 0.3 terminology, 0.3 semantic) and **tune the weights with a grid search on the dev set**. **Why:** weights must come from evidence, not guesses.
- [ ] **Also try Reciprocal Rank Fusion** and keep whichever scores better on the dev set. **Why:** RRF needs no tuning and is a strong baseline.
- [ ] **Apply a relevance cutoff** chosen on the dev set. **Why:** returns all relevant cases without flooding the doctor with noise.
- [ ] **Build the evidence object** per result: matched findings, match type (exact, synonym, semantic), snippet, and context flags. **Why:** every result must show why it appeared.
- [ ] **Show "Matched 3 of 4 findings"** instead of a percentage. **Why:** clearer and cannot be mistaken for a clinical probability.
- [ ] **Expose `POST /cases/search`** with pagination. **Why:** the frontend needs one endpoint.
- [ ] **Never use the test set while tuning.** **Why:** keeps final results honest.

**Done when:** a search returns all relevant cases above the cutoff, ranked, with evidence, and results beat keyword-only on the dev set.
EOF

# ---------------------------------------------------------------- 11
create_issue "Issue 11: Authentication, roles, provenance API and audit log" <<'EOF'
## Issue
Add login, role-based permissions, provenance endpoints, and a log of every search, view, and export.

## Purpose
Real access control must live in the backend. Hiding things in the UI is not security. Audit logs show who accessed what.

## Tasks
- [ ] **Add login with JWT** (`/auth/login`) and bcrypt password hashes via `passlib`. **Why:** standard, simple, and enough for a prototype.
- [ ] **Create roles** `doctor`, `privacy_reviewer`, `admin`, and a dependency that checks the role on every endpoint. **Why:** each role sees only what it needs.
- [ ] **Build `GET /documents/{id}` and `/documents/{id}/provenance`** returning screened text and approved provenance. **Why:** the viewer needs both, separately.
- [ ] **Make author visibility a configurable policy flag.** **Why:** showing a clinician's name is a hospital decision, not an assumption.
- [ ] **Block any route to originals** for doctors. **Why:** original notes stay restricted.
- [ ] **Write `services/audit.py`** logging doctor, action (search, view, export), document ids, and time. **Why:** accountability.
- [ ] **Build `GET /audit-logs`** for admins only. **Why:** lets admins review activity.
- [ ] **Write access-control tests**: unauthenticated request fails, a doctor cannot open the review queue, a doctor cannot reach originals. **Why:** proves the rules work.

**Done when:** all access-control tests pass and every search and document view creates an audit row.
EOF

# ---------------------------------------------------------------- 12
create_issue "Issue 12: Design system and app shell (dark glass UI)" <<'EOF'
## Issue
Build the visual foundation: dark theme with glass-style cards, left icon sidebar, top bar, and reusable components, designed for fast clinical use.

## Purpose
Every screen reuses these pieces. Getting them right once makes all later screens quick to build and consistent. The look follows the dark gradient dashboard style, with readability and speed first.

## Tasks
- [ ] **Define design tokens in Tailwind config**: deep navy background (`#0B0D1F`), glass surfaces (`rgba(255,255,255,0.06)` with a thin border and `backdrop-blur`), violet accent (`#7C5CFF`), blue accent (`#3B82F6`), and status colors. **Why:** one source of truth keeps screens consistent.
- [ ] **Check contrast**: body text at least 4.5:1 against surfaces, minimum 14px text. **Why:** dark glass looks good but can be hard to read, and doctors read quickly in all lighting.
- [ ] **Never rely on color alone**: every status gets an icon and a text label. **Why:** accessibility and quick scanning.
- [ ] **Add a light-theme toggle** using CSS variables. **Why:** bright wards and projectors can make dark UIs hard to read.
- [ ] **Use Radix UI primitives** (dialog, tabs, dropdown, tooltip) plus `lucide-react` icons. **Why:** accessible keyboard behavior for free, and we only style them.
- [ ] **Build the shell**: left icon sidebar (Home, Search, Review Queue, Audit, Settings) with labels on hover and the active item highlighted, plus a top bar with user and role. **Why:** matches the reference layout and keeps navigation to one click.
- [ ] **Set up React Router and TanStack Query.** **Why:** simple routing and cached data make screens feel instant.
- [ ] **Add global keyboard shortcuts**: `/` focuses search, `Esc` closes panels. **Why:** doctors are busy, and fewer clicks means faster work.
- [ ] **Build core components**: `GlassCard`, `Chip`, `StatusBadge`, `Button`, `EmptyState`, `Skeleton` loaders. **Why:** reuse and consistent loading states.
- [ ] **Hide role-restricted sidebar items** (reviewer and admin links only for those roles). **Why:** a clean menu for each user, with the real checks still on the backend.

**Done when:** the shell renders with sidebar, top bar, theme toggle, and shortcuts, and passes a contrast check.
EOF

# ---------------------------------------------------------------- 13
create_issue "Issue 13: Dashboard home (clinical widgets)" <<'EOF'
## Issue
Build the home screen as a grid of glass widgets that put the most useful actions in front of the doctor immediately.

## Purpose
The reference design uses widgets. We keep that look but fill it with clinical, time-saving content only. No decorative widgets.

## Tasks
- [ ] **Greeting header** with the doctor's name, department, and time. **Why:** matches the reference and confirms who is logged in.
- [ ] **Large search bar at the top**, focused on page load. **Why:** search is the main job, so it is one keystroke away.
- [ ] **"Recent searches" widget** with one-click re-run. **Why:** doctors repeat similar searches.
- [ ] **"Recently viewed cases" widget.** **Why:** quick return to a case.
- [ ] **"Saved case sets" widget** for cases selected for a PDF. **Why:** continues unfinished work.
- [ ] **"Review queue" widget** (reviewers only) showing pending count. **Why:** the reviewer's main task on the home screen.
- [ ] **"Privacy status" widget** showing how many documents are approved. **Why:** quick trust signal.
- [ ] **Do not add** music, habit, or weather widgets. **Why:** they add clutter, and speed matters here.
- [ ] **Use the TanStack Query cache and skeleton loaders.** **Why:** the page should never feel blocked.
- [ ] **Make the grid responsive** (stacks on tablets). **Why:** many clinicians use tablets.

**Done when:** a doctor can reach a search or a recent case in one click from the home screen.
EOF

# ---------------------------------------------------------------- 14
create_issue "Issue 14: Search screen and results list" <<'EOF'
## Issue
Build the search interface and the results list, with query chips and match explanations.

## Purpose
This is the core experience. A doctor must be able to search, understand why each result appeared, and move through results quickly.

## Tasks
- [ ] **Single large symptom input** with a department filter and Search button, submit on `Enter`. **Why:** minimum steps to a result.
- [ ] **Show query chips** after parsing ("difficulty breathing → dyspnea", "no fever" in a crossed style). Chips can be removed or edited, then re-run. **Why:** doctors can see and correct how the system understood them.
- [ ] **Show the result count** ("23 matching cases") and pagination (20 per page). **Why:** all matches are returned, so the list must stay readable.
- [ ] **Result card** with department, document type, short screened excerpt with matched words highlighted, "Matched 3 of 4", context flags, and a privacy badge. **Why:** enough information to decide whether to open it, without clicking.
- [ ] **Keyboard navigation**: `j`/`k` to move, `Enter` to open, `x` to select for PDF. **Why:** fastest way through a long list.
- [ ] **Sticky filter bar** (department, document type, date). **Why:** refine without losing the list.
- [ ] **Empty and error states** ("No matching cases found. Try fewer or broader terms"). **Why:** never leave a blank screen.
- [ ] **Show a notice** that this searches historical documentation, not diagnoses. **Why:** sets correct expectations.

**Done when:** a doctor can search, scan results with explanations, and open or select a case using only the keyboard.
EOF

# ---------------------------------------------------------------- 15
create_issue "Issue 15: Document viewer with provenance panel" <<'EOF'
## Issue
Build the screen that shows the exact original wording (screened), highlighted matches, redaction markers, and the provenance panel.

## Purpose
This is our differentiator: doctors read what the original clinician wrote, and they can see where it came from and what was removed.

## Tasks
- [ ] **Two-column layout**: note text on the left, provenance panel on the right. **Why:** both visible at once with no tab switching.
- [ ] **Highlight matched words**, including synonyms ("you searched *difficulty breathing*, the note says *dyspnea*"). **Why:** shows exactly why the case matched.
- [ ] **Show redactions as clear tags** like `[REDACTED-NAME]`. **Why:** doctors should know where text was removed.
- [ ] **Provenance panel**: original author (if policy allows), department, document type, approved date, screening status, redaction summary, screening method. **Why:** transparency about where the information came from.
- [ ] **Show context flags inline** (negated, historical, family). **Why:** prevents misreading a negated finding.
- [ ] **"Back to results" keeps scroll position and selection**, and `Esc` goes back. **Why:** doctors compare several cases quickly.
- [ ] **"Add to report" button** on the viewer. **Why:** select cases without leaving the note.
- [ ] **Log the view** through the audit endpoint. **Why:** completes the audit trail.

**Done when:** opening a case shows highlighted text, redaction tags, and a full provenance panel, and returning to results is instant.
EOF

# ---------------------------------------------------------------- 16
create_issue "Issue 16: Reviewer queue and admin audit screens" <<'EOF'
## Issue
Build the screens for privacy reviewers (approve or reject screened documents) and admins (review the audit log).

## Purpose
Shows judges that human review is a real part of the design, not a claim.

## Tasks
- [ ] **Queue list** with status, department, and a "needs manual review" flag at the top. **Why:** risky notes get attention first.
- [ ] **Side-by-side view**: original on the left (reviewer only), screened on the right with redactions highlighted. **Why:** the fastest way to spot a missed identifier.
- [ ] **Approve and Reject buttons** with a required reason on reject. **Why:** creates a traceable decision.
- [ ] **Keyboard shortcuts** (`a` approve, `r` reject, `n` next). **Why:** reviewers process many documents.
- [ ] **Audit log table** with filters (user, action, date) and CSV export, admin only. **Why:** easy to inspect during the demo.
- [ ] **Route guards** in the frontend that match the backend roles. **Why:** consistent behavior, with the backend as the true enforcer.

**Done when:** a reviewer approves a pending note and it becomes searchable, and an admin sees both actions in the audit table.
EOF

# ---------------------------------------------------------------- 17
create_issue "Issue 17: PDF report export" <<'EOF'
## Issue
Let a doctor export the selected cases as a PDF using only screened data.

## Purpose
Doctors want to take or share matching cases. The report must never leak identifiers and must always carry the disclaimer.

## Tasks
- [ ] **Build `POST /reports`** that takes case ids and returns a PDF. **Why:** generating on the backend keeps unscreened data away from the browser.
- [ ] **Use ReportLab** (`SimpleDocTemplate`, `Paragraph`, `Spacer`). **Why:** pure Python, no browser or system dependencies.
- [ ] **Include** search terms, search date, department, and for each case: screened text, author and department (if policy allows), document type, screening status. **Why:** a complete, traceable report.
- [ ] **Add the disclaimer to every page footer:** "This report contains historical clinical documentation for professional reference. Similarity does not establish equivalent diagnosis or treatment suitability. All clinical decisions remain the responsibility of the treating professional." **Why:** required context on every page, even if pages are separated.
- [ ] **Read only from `screened_documents`.** **Why:** same privacy rule as search.
- [ ] **Return bytes in memory** (`io.BytesIO`). **Why:** no files left on the server.
- [ ] **Add the "Generate PDF" bar in the frontend** showing the selected count. **Why:** clear and one click.
- [ ] **Run the planted-identifier leak test on the PDF text.** **Why:** the PDF is a common leak path.
- [ ] **Log the export** in the audit log. **Why:** full accountability.

**Done when:** exporting three cases produces a PDF with a footer on every page and zero planted identifiers.
EOF

# ---------------------------------------------------------------- 18
create_issue "Issue 18: Evaluation and baseline comparison" <<'EOF'
## Issue
Measure retrieval quality and compare keyword-only, semantic-only, hybrid, and hybrid with negation handling on the held-out test queries.

## Purpose
This is our proof. Real numbers turn "it seems to work" into "here is how well it works".

## Tasks
- [ ] **Write `evaluation/run_eval.py`** that runs all labeled queries through each system. **Why:** repeatable and rerunnable after every change.
- [ ] **Compute Precision@5, Recall@5, and MRR**. **Why:** standard retrieval measures judges recognize.
- [ ] **Compute precision and recall at the cutoff.** **Why:** tests our "return all relevant cases" promise, since top-5 metrics alone do not.
- [ ] **Run the negation test set** and report accuracy. **Why:** shows the differentiator in numbers.
- [ ] **Report redaction recall by entity type and the leak test result.** **Why:** shows privacy performance honestly.
- [ ] **Measure search latency** (median and 95th percentile). **Why:** speed matters for doctors.
- [ ] **Report only on the test set**, tuned on the dev set. **Why:** avoids inflated results.
- [ ] **Save a results table and a failure analysis** (3 to 5 failed queries and why). **Why:** honesty and a better story.
- [ ] **Make one chart** comparing the four systems for the slides. **Why:** judges see the improvement immediately.

**Done when:** a results table and chart exist for all four systems, and the failure analysis is written.
EOF

# ---------------------------------------------------------------- 19
create_issue "Issue 19: Security tests and hardening" <<'EOF'
## Issue
Add automated tests and basic protections for privacy leaks, access control, and unsafe input.

## Purpose
Privacy is our central claim. Tests prove it holds and protect it from accidental breaks.

## Tasks
- [ ] **Leak test across every output**: screened text, search results, evidence snippets, API responses, and the PDF. **Why:** identifiers can leak through any of them, not just the main viewer.
- [ ] **Test that unscreened or unapproved documents never appear** in search. **Why:** protects the review rule.
- [ ] **Test that `app_user` cannot read original documents** at the database level. **Why:** defense even if the code has a bug.
- [ ] **Add rate limiting on login and search** (`slowapi`). **Why:** basic protection against abuse.
- [ ] **Validate all inputs with Pydantic** (length limits, allowed characters). **Why:** blocks malformed or hostile input.
- [ ] **Set CORS to the frontend origin only** and keep secrets in `.env`. **Why:** standard hygiene.
- [ ] **Run `pytest` in a GitHub Actions workflow** on every pull request. **Why:** catches breakage before merging.
- [ ] **Run `git log --all -- .env`** and confirm it prints nothing. **Why:** secrets must never reach the repo history.

**Done when:** the CI pipeline runs all leak and access tests green on every pull request.
EOF

# ---------------------------------------------------------------- 20
create_issue "Issue 20: Demo, documentation and pitch" <<'EOF'
## Issue
Prepare a reliable demo, documentation, and presentation.

## Purpose
A strong project can still lose with a broken or confusing demo. This issue makes sure judges understand it fast and see it work.

## Tasks
- [ ] **Write the demo script** (about 4 minutes): login, search "difficulty breathing and chest discomfort", show query chips, open a case, point out redactions and provenance, show the negation case, approve a pending note as a reviewer, export a PDF, show the evaluation chart, show the audit log. **Why:** one clear scenario beats a long feature list.
- [ ] **Create a demo reset script** that reseeds the database to a known state. **Why:** the demo must be repeatable.
- [ ] **Prepare a fallback**: screen recording and screenshots in case Wi-Fi or Docker fails. **Why:** protects against live failures.
- [ ] **Write the README**: overview, architecture diagram, setup, screenshots, privacy claims and limits, future work (FHIR, SNOMED CT/UMLS, real SSO and encryption). **Why:** judges often read it.
- [ ] **Prepare 5 slides**: problem, solution and demo, why it is different (EMERSE and SemEHR already exist, so position as similarity retrieval plus original wording plus provenance), evaluation results, privacy and limitations. **Why:** honest positioning is more credible than claiming novelty.
- [ ] **Prepare answers** to likely questions: "Isn't this just search?", "Is it HIPAA compliant?", "Can embeddings leak data?", "How do you know it works?". **Why:** confident answers win judges.
- [ ] **Do a full run from a fresh clone** on a teammate's laptop. **Why:** the final check that everything works.

**Done when:** a teammate runs the full demo from a fresh clone with no help, and the slides and README are complete.
EOF

echo "Done. All 20 issues created."
