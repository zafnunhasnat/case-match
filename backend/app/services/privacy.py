
import re
from dataclasses import dataclass

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine


# Configure Presidio to use the smaller English spaCy model.
NLP_CONFIGURATION = {
    "nlp_engine_name": "spacy",
    "models": [
        {
            "lang_code": "en",
            "model_name": "en_core_web_sm",
        }
    ],
}

nlp_provider = NlpEngineProvider(
    nlp_configuration=NLP_CONFIGURATION
)
nlp_engine = nlp_provider.create_engine()

analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["en"],
)

anonymizer = AnonymizerEngine()


# Custom recognizer for medical record and patient identifiers.
mrn_recognizer = PatternRecognizer(
    supported_entity="MEDICAL_RECORD_NUMBER",
    patterns=[
        Pattern(
            name="medical_record_number",
            regex=(
                r"\b(?:MRN|Medical Record(?: Number)?|Patient ID)"
                r"\s*[:#-]?\s*[A-Z0-9-]{5,20}\b"
            ),
            score=0.90,
        )
    ],
    context=["medical", "patient", "record", "hospital"],
)

analyzer.registry.add_recognizer(mrn_recognizer)
ssn_recognizer = PatternRecognizer(
    supported_entity="US_SSN",
    patterns=[
        Pattern(
            name="ssn_with_dashes",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.95,
        )
    ],
    context=["SSN", "Social Security", "social security number"],
)
analyzer.registry.add_recognizer(ssn_recognizer)


# Entity types that should be screened.
ENTITIES_TO_REDACT = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "LOCATION",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
    "CREDIT_CARD",
    "US_DRIVER_LICENSE",
    "MEDICAL_RECORD_NUMBER",
]


@dataclass
class ScreeningResult:
    screened_text: str
    redaction_count: int
    redactions_applied: bool
    screening_method: str
    detected_entity_types: list[str]


def screen_text(text: str, language: str = "en") -> ScreeningResult:
    """
    Detect and redact identifying information from text.

    Returns screened text and metadata about the redactions.
    Original text is never stored or returned by this function.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return ScreeningResult(
            screened_text=text,
            redaction_count=0,
            redactions_applied=False,
            screening_method="presidio_and_regex",
            detected_entity_types=[],
        )

    if language != "en":
        raise ValueError("Only English screening is currently supported")

    results = analyzer.analyze(
        text=text,
        language=language,
        entities=ENTITIES_TO_REDACT,
        score_threshold=0.35,
    )
    # Prevent an email address from also being counted as a URL.
    results = [
        result
        for result in results
        if not (
            result.entity_type == "URL"
            and any(
                other.entity_type == "EMAIL_ADDRESS"
                and other.start < result.end
                and result.start < other.end
                for other in results
            )
        )
    ]

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
    )

    detected_types = sorted({
        result.entity_type for result in results
    })

    return ScreeningResult(
        screened_text=anonymized.text,
        redaction_count=len(results),
        redactions_applied=len(results) > 0,
        screening_method="presidio_and_regex",
        detected_entity_types=detected_types,
    )
