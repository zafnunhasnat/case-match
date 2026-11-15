
import re

import spacy
from pydantic import BaseModel, Field

from backend.app.services.terminology import normalize


# Load spaCy
nlp = spacy.load("en_core_web_sm")


# Words that should not be treated as clinical findings
FILLER_WORDS = {
    "patient", "patients",
    "has", "have", "had",
    "reports", "report", "reported",
    "experiences", "experiencing",
    "with", "the", "a", "an",
    "is", "was", "were",
    "of", "for", "and", "or", "but",
    "no", "not", "denies", "denied",
    "without", "negative"
}


NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12",
    "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "twenty": "20",
    "thirty": "30"
}


DURATION_PATTERN = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty)"
    r"\s+(hours?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE
)


NEGATION_PATTERN = re.compile(
    r"\b(no|not|denies|denied|without|negative\s+for)\b",
    re.IGNORECASE
)


class Finding(BaseModel):
    text: str
    concept: str | None
    synonyms: list[str] = Field(default_factory=list)
    excluded: bool = False


class ParsedQuery(BaseModel):
    findings: list[Finding]
    duration: str | None = None



def extract_duration(text: str):
    # First, check for numeric or written durations.
    match = DURATION_PATTERN.search(text)

    if match:
        amount = match.group(1).lower()
        amount = NUMBER_WORDS.get(amount, amount)

        return f"{amount} {match.group(2).lower()}"

    # If regex finds nothing, check spaCy DATE entities.
    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "DATE":
            return ent.text.strip().lower()

    return None



def extract_candidates(text: str):
    """
    Find clinical terms directly in the sentence.

    Checks longer phrases first so that terms such as
    'shortness of breath' are not split into separate words.
    """

    cleaned = DURATION_PATTERN.sub("", text)

    doc = nlp(cleaned)
    tokens = [
        token for token in doc
        if not token.is_punct and not token.is_space
    ]

    candidates = []
    occupied = set()

    # Check phrases containing up to five words.
    for size in range(5, 0, -1):
        for start in range(len(tokens) - size + 1):
            positions = set(range(start, start + size))

            if positions & occupied:
                continue

            phrase = doc[tokens[start].i:tokens[start + size - 1].i + 1].text.strip()

            # Skip grammatical filler words as standalone findings.
            if phrase.lower() in FILLER_WORDS:
                continue

            concept = normalize(phrase)

            if concept is not None:
                candidates.append(phrase)
                occupied.update(positions)

    return candidates


def is_negated(text: str, finding: str):
    """
    Determine whether a finding is negated.

    Examples:
    No cough -> True
    No cough but reports fatigue -> cough=True
    Denies nausea and vomiting -> both=True
    """

    finding_match = re.search(
        re.escape(finding),
        text,
        re.IGNORECASE
    )

    if not finding_match:
        return False

    prefix = text[:finding_match.start()]

    # Find the most recent negation.
    negations = list(NEGATION_PATTERN.finditer(prefix))

    if not negations:
        return False

    last_negation = negations[-1]

    # A contrast word ends the negation scope.
    after_negation = prefix[last_negation.end():]

    if re.search(r"\bbut\b", after_negation, re.IGNORECASE):
        return False

    return True


def parse_query(text: str) -> ParsedQuery:

    duration = extract_duration(text)

    candidates = extract_candidates(text)

    findings = []
    seen = set()

    for candidate in candidates:

        candidate_doc = nlp(candidate)

        words = [
            token.text
            for token in candidate_doc
            if token.text.lower() not in FILLER_WORDS
            and not token.is_punct
            and not token.is_space
        ]

        phrase = " ".join(words).strip()

        if not phrase or len(phrase) < 3:
            continue

        concept = normalize(phrase)

        if concept is None:
            continue

        key = concept.lower()

        if key in seen:
            continue

        seen.add(key)

        findings.append(
            Finding(
                text=phrase,
                concept=concept,
                synonyms=[phrase],
                excluded=is_negated(text, phrase)
            )
        )

    return ParsedQuery(
        findings=findings,
        duration=duration
    )


# Compatibility alias
parse_clinical_query = parse_query
