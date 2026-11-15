from datetime import date

import pytest
from sqlalchemy import text

from backend.app.services.keyword_search import (
    SearchFilters,
    _get_engine,
    keyword_search,
)
from backend.app.services.query_parser import Finding, ParsedQuery, parse_query

DEPT = "pytest-keyword"
BULK = "pytest-keyword-bulk"

# key, status, text, document_type, date
DOCS = [
    ("sob", "approved", "Patient reports shortness of breath on exertion.",
     "progress_note", date(2024, 3, 1)),
    ("dyspnea", "approved", "Assessment: worsening dyspnea over two days.",
     "discharge_summary", date(2023, 1, 15)),
    ("chest", "approved", "Chest pain radiating to the left arm.",
     "progress_note", date(2024, 5, 10)),
    ("both", "approved", "Shortness of breath with chest pain at rest.",
     "progress_note", date(2024, 6, 2)),
    ("allsyn", "approved",
     "Dyspnea, shortness of breath and breathlessness noted on admission.",
     "progress_note", date(2024, 2, 2)),
    ("draft", "draft", "Severe dyspnea and shortness of breath.",
     "progress_note", date(2024, 3, 3)),
    ("rejected", "rejected", "Difficulty breathing and shortness of breath.",
     "progress_note", date(2024, 3, 4)),
]

INSERT = text(
    "INSERT INTO clinical_documents "
    "(title, screened_text, department, document_type, document_date, status) "
    "VALUES (:title, :body, :dept, :dtype, :d, :status) RETURNING id"
)


@pytest.fixture(scope="module")
def seeded():
    engine = _get_engine()
    ids = {"bulk": []}
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clinical_documents WHERE department LIKE 'pytest-keyword%'"))
        for key, status, body, dtype, d in DOCS:
            ids[key] = conn.execute(
                INSERT,
                {"title": key, "body": body, "dept": DEPT, "dtype": dtype, "d": d, "status": status},
            ).scalar_one()
        for n in range(60):
            ids["bulk"].append(
                conn.execute(
                    INSERT,
                    {"title": f"bulk{n}", "body": f"Dyspnea noted, bulk case {n}.",
                     "dept": BULK, "dtype": "progress_note", "d": date(2024, 1, 1),
                     "status": "approved"},
                ).scalar_one()
            )
    yield ids
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clinical_documents WHERE department LIKE 'pytest-keyword%'"))


def _ids(results):
    return [c.document_id for c in results]


def test_difficulty_breathing_finds_synonym_notes(seeded):
    results = keyword_search(parse_query("difficulty breathing"))
    got = {c.document_id: c for c in results}
    assert seeded["sob"] in got      # "shortness of breath"
    assert seeded["dyspnea"] in got  # "dyspnea"
    assert got[seeded["sob"]].matched_via == "synonym"
    assert got[seeded["sob"]].matched_findings == 1
    assert got[seeded["sob"]].total_findings == 1


def test_unapproved_note_never_appears(seeded):
    results = keyword_search(parse_query("difficulty breathing"))
    assert seeded["draft"] not in _ids(results)
    assert seeded["rejected"] not in _ids(results)


def test_finding_counts_once_however_many_synonyms_match(seeded):
    results = keyword_search(parse_query("difficulty breathing"))
    matches = [c for c in results if c.document_id == seeded["allsyn"]]
    assert len(matches) == 1
    assert matches[0].matched_findings == 1


def test_two_findings_rank_first(seeded):
    results = keyword_search(parse_query("shortness of breath and chest pain"))
    assert results[0].matched_findings == 2
    both = next(c for c in results if c.document_id == seeded["both"])
    assert both.matched_findings == 2 and both.total_findings == 2
    chest = next(c for c in results if c.document_id == seeded["chest"])
    assert chest.matched_findings == 1


def test_exact_match_reported_as_exact(seeded):
    results = keyword_search(parse_query("shortness of breath"))
    got = {c.document_id: c for c in results}
    assert got[seeded["sob"]].matched_via == "exact"
    assert got[seeded["dyspnea"]].matched_via == "synonym"


def test_snippets_are_highlighted(seeded):
    results = keyword_search(parse_query("difficulty breathing"))
    sob = next(c for c in results if c.document_id == seeded["sob"])
    assert sob.snippets and "<b>" in sob.snippets[0]


def test_no_limit_returns_every_match(seeded):
    results = keyword_search(parse_query("difficulty breathing"))
    assert set(seeded["bulk"]) <= set(_ids(results))


def test_filters(seeded):
    parsed = parse_query("difficulty breathing")
    by_dept = keyword_search(parsed, SearchFilters(department=DEPT))
    assert {c.department for c in by_dept} == {DEPT}

    by_type = keyword_search(parsed, {"department": DEPT, "document_type": "discharge_summary"})
    assert _ids(by_type) == [seeded["dyspnea"]]

    by_date = keyword_search(
        parsed, SearchFilters(department=DEPT, date_from=date(2024, 1, 1), date_to=date(2024, 3, 31))
    )
    assert seeded["sob"] in _ids(by_date)
    assert seeded["dyspnea"] not in _ids(by_date)


def test_excluded_findings_are_not_searched(seeded):
    assert keyword_search(parse_query("no fever")) == []


def test_sql_injection_text_is_harmless(seeded):
    evil = ParsedQuery(findings=[Finding(text="x'); DROP TABLE clinical_documents; --")])
    keyword_search(evil)
    with _get_engine().connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM clinical_documents")).scalar_one() > 0
