import csv
from pathlib import Path

import spacy
from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session

from backend.app.models.term import ClinicalTerm

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")

CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "terminology" / "terms.csv"


def clean_phrase(phrase: str) -> str:
    doc = nlp(phrase.lower().strip())
    words = [
        token.lemma_.lower() if token.lemma_ else token.text.lower()
        for token in doc
        if not token.is_punct and not token.is_space
    ]
    return " ".join(words)


def load_csv_terms():
    with CSV_PATH.open("r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def normalize(phrase: str, db: Session | None = None):
    cleaned = clean_phrase(phrase)

    if db is not None:
        terms = db.query(ClinicalTerm).all()
        records = [
            {
                "preferred_term": term.preferred_term,
                "synonym": term.synonym,
                "abbreviation": term.abbreviation or "",
                "terminology_code": term.terminology_code or "",
            }
            for term in terms
        ]
    else:
        records = load_csv_terms()

    for record in records:
        candidates = [
            record["preferred_term"].lower(),
            record["synonym"].lower(),
        ]
        if record.get("abbreviation"):
            candidates.append(record["abbreviation"].lower())

        if cleaned in candidates or phrase.lower().strip() in candidates:
            return record["preferred_term"]

    choices = {}
    for record in records:
        for candidate in (
            record["preferred_term"],
            record["synonym"],
            record.get("abbreviation", ""),
        ):
            if candidate:
                choices[candidate.lower()] = record["preferred_term"]

    match = process.extractOne(cleaned, choices.keys(), scorer=fuzz.ratio)

    if match and match[1] >= 90:
        return choices[match[0]]

    return None
