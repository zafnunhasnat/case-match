"""Unit tests for keyword_search (no database needed).

These check the SQL structure and the result handling using a fake session.
Tests that run against a real database live in test_keyword_search_db.py.
"""
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

from backend.app.services.keyword_search import (
    Candidate,
    SearchFilters,
    get_searchable_documents,
    keyword_search,
)
from backend.app.services.query_parser import Finding, ParsedQuery

PATCH_SESSION = "backend.app.services.keyword_search.SessionLocal"


def finding(text, concept=None, synonyms=None, excluded=False):
    return Finding(
        text=text, concept=concept, synonyms=synonyms or [], excluded=excluded
    )


def breathing():
    return finding(
        "difficulty breathing", "dyspnea", ["shortness of breath", "sob"]
    )


def row(doc_id="doc-1", matched=(True,), exact=(False,), rank=(0.5,),
        headline=("... <b>dyspnea</b> ...",), department="Cardiology",
        document_type="progress_note"):
    data = {
        "document_id": doc_id,
        "department": department,
        "document_type": document_type,
        "document_date": date(2024, 3, 1),
    }
    for i, m in enumerate(matched):
        data[f"m{i}"] = m
        data[f"e{i}"] = exact[i]
        data[f"r{i}"] = rank[i] if m else 0
        data[f"h{i}"] = headline[i] if m else None
    return data


def fake_session(rows):
    session = MagicMock()
    session.execute.return_value.mappings.return_value.all.return_value = rows
    return session


def run(parsed, rows, filters=None):
    session = fake_session(rows)
    results = keyword_search(parsed, filters, db=session)
    sql = str(session.execute.call_args[0][0])
    params = session.execute.call_args[0][1]
    return results, sql, params


def test_synonym_match_returns_one_candidate_with_counts():
    parsed = ParsedQuery(findings=[breathing()])
    results, _, _ = run(parsed, [row()])

    assert len(results) == 1
    c = results[0]
    assert isinstance(c, Candidate)
    assert c.matched_findings == 1
    assert c.total_findings == 1
    assert c.matched_texts == ["difficulty breathing"]
    assert c.matched_via == "synonym"
    assert "<b>dyspnea</b>" in c.snippets[0]


def test_each_synonym_gets_its_own_bound_tsquery_or_ed_together():
    parsed = ParsedQuery(findings=[breathing()])
    _, sql, params = run(parsed, [row()])

    assert sql.count("plainto_tsquery('english', :t0_") >= 4
    assert "||" in sql
    values = {v for k, v in params.items() if k.startswith("t0_")}
    assert values == {
        "difficulty breathing", "dyspnea", "shortness of breath", "sob"
    }


def test_user_text_is_only_ever_a_bound_parameter():
    evil = "x'); DROP TABLE clinical_documents; --"
    parsed = ParsedQuery(findings=[finding(evil)])
    _, sql, params = run(parsed, [])

    assert "DROP TABLE" not in sql
    assert any("drop table" in str(v).lower() for v in params.values())


def test_only_approved_documents_are_searched_and_no_limit():
    parsed = ParsedQuery(findings=[breathing()])
    _, sql, _ = run(parsed, [])

    assert "screening_status = 'approved'" in get_searchable_documents()
    assert "screening_status = 'approved'" in sql
    assert "LIMIT" not in sql.upper()


def test_excluded_findings_are_not_searched():
    parsed = ParsedQuery(findings=[finding("fever", "fever", excluded=True)])
    with patch(PATCH_SESSION) as session_factory:
        assert keyword_search(parsed) == []
        session_factory.assert_not_called()


def test_no_findings_returns_empty_without_touching_the_database():
    with patch(PATCH_SESSION) as session_factory:
        assert keyword_search(ParsedQuery(findings=[])) == []
        session_factory.assert_not_called()


def test_filters_are_bound_and_accept_dict_or_model():
    parsed = ParsedQuery(findings=[breathing()])
    as_dict = {
        "department": "Cardiology",
        "document_type": "discharge_summary",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }
    _, sql, params = run(parsed, [], as_dict)

    assert params["f_department"] == "Cardiology"
    assert params["f_document_type"] == "discharge_summary"
    assert params["f_date_from"] == date(2026, 1, 1)
    assert params["f_date_to"] == date(2026, 12, 31)
    assert "d.department = :f_department" in sql
    assert "Cardiology" not in sql

    _, _, params2 = run(parsed, [], SearchFilters(department="ER"))
    assert params2["f_department"] == "ER"


def test_documents_matching_more_findings_rank_first():
    parsed = ParsedQuery(
        findings=[
            finding("shortness of breath", "dyspnea"),
            finding("chest pain", "chest pain"),
        ]
    )
    rows = [
        row("only-one", matched=(True, False), exact=(True, False),
            rank=(0.9, 0), headline=("a", None)),
        row("both", matched=(True, True), exact=(True, True),
            rank=(0.2, 0.2), headline=("a", "b")),
    ]
    results, _, _ = run(parsed, rows)

    assert [c.document_id for c in results] == ["both", "only-one"]
    assert results[0].matched_findings == 2
    assert results[0].total_findings == 2
    assert results[1].matched_findings == 1


def test_matched_via_is_exact_when_typed_words_matched():
    parsed = ParsedQuery(findings=[breathing()])
    results, _, _ = run(parsed, [row(exact=(True,))])
    assert results[0].matched_via == "exact"


def test_uuid_document_ids_become_strings():
    parsed = ParsedQuery(findings=[breathing()])
    doc_id = uuid.uuid4()
    results, _, _ = run(parsed, [row(doc_id)])
    assert results[0].document_id == str(doc_id)


def test_session_is_closed_only_when_the_function_opened_it():
    parsed = ParsedQuery(findings=[breathing()])

    own = fake_session([])
    with patch(PATCH_SESSION, return_value=own):
        keyword_search(parsed)
    own.close.assert_called_once()

    injected = fake_session([])
    keyword_search(parsed, db=injected)
    injected.close.assert_not_called()
