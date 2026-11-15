# De-identification: HIPAA Safe Harbor and Microsoft Presidio

## 1. Overview

CaseMatch handles healthcare-related documents that may contain
personally identifiable information (PII) and protected health
information (PHI).

Before documents are processed for matching, searching, or other
downstream operations, sensitive information should be identified
and appropriately redacted.

This document explains HIPAA Safe Harbor, Microsoft Presidio,
and how CaseMatch plans to approach de-identification.

## 2. HIPAA De-identification

The Health Insurance Portability and Accountability Act (HIPAA)
provides two methods for de-identifying protected health information:

1. Safe Harbor Method
2. Expert Determination Method

### 2.1 Safe Harbor Method

The Safe Harbor method requires removing 18 categories of identifiers
associated with an individual or their relatives, employers, or
household members.

The 18 categories are:

1. Names
2. Geographic subdivisions smaller than a state, subject to
   limited ZIP code exceptions
3. Dates directly related to an individual, except the year,
   and ages over 89
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate and license numbers
12. Vehicle identifiers and serial numbers
13. Device identifiers and serial numbers
14. Web URLs
15. IP addresses
16. Biometric identifiers, including fingerprints and voiceprints
17. Full-face photographs and comparable images
18. Other unique identifying numbers, characteristics, or codes

In addition to removing these identifiers, the covered entity must
not have actual knowledge that the remaining information could be
used alone or with other information to identify an individual.

### 2.2 Important Safe Harbor Details

- Only the year may generally remain for dates directly related
  to an individual.
- Ages over 89 must be grouped into a category of 90 or older.
- ZIP code exceptions have specific population requirements.
- Removing names alone does not make a document de-identified.
- Unique details that could identify someone must also be considered.

### 2.3 Expert Determination

Expert Determination is the second HIPAA de-identification method.

A qualified person with appropriate knowledge of statistical and
scientific methods must determine that the risk of identifying an
individual is very small.

The expert must document the methods and results supporting
that conclusion.

This method is different from Safe Harbor because it relies on
a documented risk assessment rather than simply removing the
18 categories of identifiers.

## 3. Microsoft Presidio

Microsoft Presidio is an open-source framework for identifying
and anonymizing personally identifiable information.

It provides tools for detecting sensitive information in text
and other types of data.

Presidio has two main components relevant to CaseMatch.

### 3.1 Presidio Analyzer

The Analyzer identifies potential PII in text.

It uses:
- Named Entity Recognition (NER)
- Regular expressions
- Rule-based recognition
- Context-aware detection
- Custom recognizers

Examples of information it can detect include:
- Person names
- Phone numbers
- Email addresses
- Locations
- Social Security numbers
- Other supported identifiers

The Analyzer returns detected entities, their positions in the
text, and confidence scores.

### 3.2 Presidio Anonymizer

The Anonymizer uses the Analyzer's detection results to transform
sensitive information.

Available approaches include:
- Replace: replaces detected information with a label.
- Redact: removes detected text.
- Mask: replaces characters with masking characters.
- Hash: replaces detected values with a hash.

For CaseMatch, replacing detected identifiers with labels such as
[PERSON] or [PHONE_NUMBER] may be useful when the surrounding
document content needs to remain readable.

## 4. Regular Expression Screening

Presidio supports regular-expression-based detection, but
CaseMatch will also use additional custom regex patterns.

Custom patterns can help identify information that may not be
detected reliably by the default recognizers.

Potential examples include:
- Hospital-specific patient ID formats
- Medical record number formats
- Internal account numbers
- Custom document identifiers
- Other known patterns used by participating hospitals

Regex screening should complement Presidio rather than replace it.

Patterns must be tested carefully because overly broad patterns
can produce false positives, while overly narrow patterns can
miss sensitive information.

## 5. Proposed CaseMatch De-identification Workflow

The proposed workflow is:

1. A hospital employee uploads a document.
2. The document is converted into text when necessary.
3. Presidio Analyzer scans the extracted text for sensitive
   information.
4. Custom regex patterns identify additional sensitive values.
5. Detection results are combined and reviewed by the redaction
   process.
6. Presidio Anonymizer or equivalent redaction logic transforms
   detected identifiers.
7. The resulting text is checked before being sent to downstream
   processing.
8. Only appropriately processed content is made available to
   the relevant application features.

Original documents and de-identified content should be handled
according to separate access permissions.

Access to original documents should remain restricted to
authorized users.

## 6. Limitations and Risks

Automated de-identification is not perfect.

Potential problems include:

- False positives: ordinary text is incorrectly identified as PII.
- False negatives: sensitive information is not detected.
- Unusual formats: hospital-specific identifiers may not match
  predefined recognizers.
- Contextual identifiers: information may identify someone even
  without an obvious name or number.
- OCR errors: scanned documents and images may produce inaccurate
  extracted text.

Presidio does not guarantee that all sensitive information will
be detected.

For this reason, CaseMatch should use additional validation,
custom recognizers, testing, and appropriate human review.

Using Presidio alone does not establish HIPAA compliance or
automatically satisfy the Safe Harbor requirements.

## 7. Testing and Validation

The de-identification implementation should include tests for:

- Names and phone numbers.
- Email addresses.
- Social Security numbers.
- Medical record numbers.
- Hospital-specific identifiers.
- Multiple identifiers in one document.
- Text containing no sensitive information.
- False positives and false negatives.
- Scanned documents after OCR extraction.
- Ensuring original sensitive values do not appear in
  downstream processed content.

Tests should use synthetic data rather than real patient records.

## 8. References

1. U.S. Department of Health and Human Services.
   Guidance Regarding Methods for De-identification of Protected
   Health Information in Accordance with the HIPAA Privacy Rule.

   https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html

2. Presidio Documentation - Overview.

   https://microsoft.github.io/presidio/

3. Presidio Analyzer Documentation.

   https://microsoft.github.io/presidio/analyzer/

4. Presidio Installation Documentation.

   https://microsoft.github.io/presidio/installation/
