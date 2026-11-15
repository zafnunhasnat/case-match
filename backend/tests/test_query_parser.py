from pathlib import Path

import pytest

from backend.app.services.query_parser import ParsedQuery, parse_query
from backend.app.services.terminology import normalize

# (query, expected {(concept, excluded)}, expected duration)
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


# Extra cases from main. Each concept below must exist in
# data/terminology/terms.csv, otherwise add a row for it (do not delete the test).
EXTRA_CASES = [
    ("Patient has shortness of breath and chest pain", ["dyspnea", "chest pain"]),
    ("Patient reports fever for 3 days", ["fever"]),
    ("No cough but reports fatigue", ["cough", "fatigue"]),
    ("Hypertension with headache", ["hypertension", "headache"]),
    ("Patient has diabetes", ["diabetes mellitus"]),
    ("Patient reports dizziness for two weeks", ["dizziness"]),
    ("No fever or cough", ["fever", "cough"]),
    ("Patient has abdominal pain and nausea", ["abdominal pain", "nausea"]),
    ("Patient reports fatigue for 5 days", ["fatigue"]),
]


@pytest.mark.parametrize("query,expected", EXTRA_CASES)
def test_parse_query_extra_concepts(query, expected):
    result = parse_query(query)
    concepts = [f.concept.lower() for f in result.findings if f.concept]
    for concept in expected:
        assert concept in concepts


def test_negation_scope_stops_at_but():
    result = parse_query("No cough but reports fatigue")
    findings = {f.concept.lower(): f.excluded for f in result.findings if f.concept}
    assert findings["cough"] is True
    assert findings["fatigue"] is False


def test_no_x_or_y_excludes_both():
    result = parse_query("No fever or cough")
    findings = {f.concept.lower(): f.excluded for f in result.findings if f.concept}
    assert findings["fever"] is True
    assert findings["cough"] is True


@pytest.mark.xfail(
    reason="Known limitation: the parser splits on 'and', so the negation in "
    "'Denies nausea and vomiting' does not reach 'vomiting'. Fix by carrying "
    "negation across 'and' within one clause, then remove this xfail.",
    strict=True,
)
def test_denies_multiple_findings_joined_by_and():
    result = parse_query("Denies nausea and vomiting")
    findings = {f.concept.lower(): f.excluded for f in result.findings if f.concept}
    assert findings["nausea"] is True
    assert findings["vomiting"] is True


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
