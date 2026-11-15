from pathlib import Path

import pytest

from backend.app.services.query_parser import ParsedQuery, parse_query
from backend.app.services.terminology import normalize

CASES = [
    ("patient has shortness of breath for 3 days, no fever",
     {("dyspnea", False), ("fever", True)}, "3 days"),
    ("chest pain and cough",
     {("chest pain", False), ("cough", False)}, None),
    ("SOB and HTN",
     {("dyspnea", False), ("hypertension", False)}, None),
    ("patient has hedache and nausea",
     {("headache", False), ("nausea", False)}, None),
    ("no fever, no chills, but has cough",
     {("fever", True), ("chills", True), ("cough", False)}, None),
    ("denies chest pain",
     {("chest pain", True)}, None),
    ("SOB for two weeks",
     {("dyspnea", False)}, "two weeks"),
    ("patient reports heartburn and difficulty swallowing",
     {("gastroesophageal reflux", False), ("dysphagia", False)}, None),
    ("fever with chills and night sweats for 5 days",
     {("fever", False), ("chills", False), ("night sweats", False)}, "5 days"),
    ("patient reports no nausea or vomiting",
     {("nausea", True), ("vomiting", True)}, None),
]


@pytest.mark.parametrize("query,expected,duration", CASES)
def test_parse_query(query, expected, duration):
    result = parse_query(query)
    assert isinstance(result, ParsedQuery)
    got = {(f.concept, f.excluded) for f in result.findings}
    assert expected <= got
    assert result.duration == duration


def test_normalize_exact_and_case_insensitive():
    c = normalize("Shortness of Breath")
    assert c.preferred_term == "dyspnea"
    assert c.method == "exact"


def test_normalize_lemma():
    assert normalize("loose stool").preferred_term == "diarrhea"


def test_normalize_abbreviation():
    assert normalize("HTN").preferred_term == "hypertension"


def test_normalize_fuzzy_typo():
    c = normalize("hedache")
    assert c.preferred_term == "headache"
    assert c.method == "fuzzy"
    assert c.score >= 90


def test_normalize_unknown_returns_none():
    assert normalize("zzzzzzzz") is None


def test_terms_csv_size():
    lines = Path("data/terminology/terms.csv").read_text(encoding="utf-8").strip().splitlines()
    assert 100 <= len(lines) - 1 <= 200
