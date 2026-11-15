import pytest

from backend.app.services.query_parser import parse_query


@pytest.mark.parametrize(
    "query, expected",
    [
        (
            "Patient has shortness of breath and chest pain",
            ["dyspnea", "chest pain"],
        ),
        (
            "Patient reports fever for 3 days",
            ["fever"],
        ),
        (
            "No cough but reports fatigue",
            ["cough", "fatigue"],
        ),
        (
            "Denies nausea and vomiting",
            ["nausea", "vomiting"],
        ),
        (
            "Hypertension with headache",
            ["hypertension", "headache"],
        ),
        (
            "Patient has diabetes",
	    ["diabetes mellitus"],
        ),
        (
            "Patient reports dizziness for two weeks",
            ["dizziness"],
        ),
        (
            "No fever or cough",
            ["fever", "cough"],
        ),
        (
            "Patient has abdominal pain and nausea",
            ["abdominal pain", "nausea"],
        ),
        (
            "Patient reports fatigue for 5 days",
            ["fatigue"],
        ),
    ],
)
def test_parse_query(query, expected):
    result = parse_query(query)

    concepts = [
        finding.concept.lower()
        for finding in result.findings
    ]

    for concept in expected:
        assert concept in concepts


def test_duration_extraction():
    result = parse_query("Patient reports fever for 3 days")

    assert result.duration == "3 days"


def test_word_duration_extraction():
    result = parse_query("Patient reports dizziness for two weeks")

    assert result.duration == "2 weeks"


def test_negation():
    result = parse_query("No cough but reports fatigue")

    findings = {
        finding.concept.lower(): finding.excluded
        for finding in result.findings
    }

    assert findings["cough"] is True
    assert findings["fatigue"] is False


def test_denies_multiple_findings():
    result = parse_query("Denies nausea and vomiting")

    findings = {
        finding.concept.lower(): finding.excluded
        for finding in result.findings
    }

    assert findings["nausea"] is True
    assert findings["vomiting"] is True
