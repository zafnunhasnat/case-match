
import pytest

from app.services.privacy import screen_text


def test_email_is_redacted():
    original = "Contact the patient at test@example.com"

    result = screen_text(original)

    assert "test@example.com" not in result.screened_text
    assert "<EMAIL_ADDRESS>" in result.screened_text
    assert result.redactions_applied is True


def test_person_name_is_redacted():
    original = "Patient John Smith needs a follow-up appointment."

    result = screen_text(original)

    assert "John Smith" not in result.screened_text
    assert result.redactions_applied is True


def test_phone_number_is_redacted():
    original = "Call the patient at +1 415-555-0132."

    result = screen_text(original)

    assert "415-555-0132" not in result.screened_text
    assert result.redactions_applied is True


def test_ssn_is_redacted():
    original = "Patient SSN: 123-45-6789"

    result = screen_text(original)

    assert "123-45-6789" not in result.screened_text
    assert result.redactions_applied is True


def test_medical_record_number_is_redacted():
    original = "Patient record MRN: ABC123456"

    result = screen_text(original)

    assert "ABC123456" not in result.screened_text
    assert "MEDICAL_RECORD_NUMBER" in result.detected_entity_types


def test_multiple_identifiers_are_redacted():
    original = (
        "Patient John Smith, email test@example.com, "
        "MRN: ABC123456"
    )

    result = screen_text(original)

    assert "John Smith" not in result.screened_text
    assert "test@example.com" not in result.screened_text
    assert "ABC123456" not in result.screened_text
    assert result.redaction_count >= 3


def test_clean_text_is_not_changed():
    original = (
        "The patient was given instructions "
        "to rest and drink water."
    )

    result = screen_text(original)

    assert result.screened_text == original
    assert result.redaction_count == 0
    assert result.redactions_applied is False


def test_empty_text_is_handled():
    result = screen_text("")

    assert result.screened_text == ""
    assert result.redaction_count == 0
    assert result.redactions_applied is False


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError):
        screen_text(None)


def test_unsupported_language_is_rejected():
    with pytest.raises(ValueError):
        screen_text("Hello", language="fr")
