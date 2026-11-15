from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock, patch
from backend.app.services.keyword_search import keyword_search, Candidate


@dataclass
class DummyFinding:
    text: str
    concept: str
    synonyms: List[str] = field(default_factory=list)
    excluded: bool = False


@dataclass
class DummyParsedQuery:
    findings: List[DummyFinding]


def test_difficulty_breathing_matches_dyspnea_and_sob_once():
    parsed = DummyParsedQuery(
        findings=[
            DummyFinding(
                text="difficulty breathing",
                concept="dyspnea",
                synonyms=["shortness of breath", "sob"],
            )
        ]
    )

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        (101, 0.91, "Patient has acute <b>dyspnea</b>.", True, False),
        (102, 0.78, "Reports <b>shortness of breath</b> on exertion.", True, False),
    ]

    mock_db = MagicMock()
    mock_db.execute.return_value = mock_result

    with patch("backend.app.services.keyword_search.SessionLocal", return_value=mock_db):
        results = keyword_search(parsed)

    assert len(results) == 2
    assert all(isinstance(r, Candidate) for r in results)
    assert [r.document_id for r in results] == [101, 102]
    assert results[0].matched_findings == ["dyspnea"]
    assert results[0].total_findings == 1
    assert results[0].matched_via == "synonym"
    assert "dyspnea" in results[0].snippets[0].lower()
    assert "shortness of breath" in results[1].snippets[0].lower()

    executed_sql = str(mock_db.execute.call_args[0][0])
    bound_params = mock_db.execute.call_args[0][1]
    assert "status = 'approved'" in executed_sql
    assert "LIMIT" not in executed_sql.upper()
    assert "dyspnea" in bound_params["q_0"]
    assert "shortness & of & breath" in bound_params["q_0"]
    assert "sob" in bound_params["q_0"]


def test_unapproved_notes_never_appear_and_filters_bind():
    parsed = DummyParsedQuery(
        findings=[DummyFinding(text="dyspnea", concept="dyspnea", synonyms=["sob"])]
    )

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []

    mock_db = MagicMock()
    mock_db.execute.return_value = mock_result

    filters = {
        "department": "Cardiology",
        "document_type": "discharge_summary",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
    }

    with patch("backend.app.services.keyword_search.SessionLocal", return_value=mock_db):
        results = keyword_search(parsed, filters=filters)

    assert results == []
    executed_sql = str(mock_db.execute.call_args[0][0])
    bound_params = mock_db.execute.call_args[0][1]
    assert "status = 'approved'" in executed_sql
    assert bound_params["department"] == "Cardiology"
    assert bound_params["document_type"] == "discharge_summary"
    assert bound_params["date_from"] == "2026-01-01"
    assert bound_params["date_to"] == "2026-12-31"
