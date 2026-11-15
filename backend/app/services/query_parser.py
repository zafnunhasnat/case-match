"""Turn a free-text clinical query into structured findings.

Split on commas / and / but / with, extract noun chunks (spaCy), drop filler
words, detect negation (medspaCy ConText), extract duration (DATE + regex).
"""
from __future__ import annotations

import re
from functools import lru_cache

from pydantic import BaseModel, Field

from backend.app.services.terminology import MIN_FUZZY_LEN, lookup_exact, normalize

SPLIT_RE = re.compile(r",|;|\b(?:and|but|with)\b", re.I)
NEG_RE = re.compile(
    r"\b(no|not|denies|denied|denying|without|never|negative for|absence of|free of)\b",
    re.I,
)
NUMBER = r"\d+(?:\.\d+)?|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|several|few"
DURATION_RE = re.compile(
    rf"\b(?:for\s+|over\s+|since\s+)?(?:the\s+(?:last|past)\s+)?({NUMBER})\s+"
    r"(hours?|days?|weeks?|months?|years?)\b",
    re.I,
)
DROP_WORDS = {
    "patient", "patients", "pt", "has", "have", "had", "reports", "report",
    "reported", "reporting", "complains", "complaining", "complaint", "presents",
    "presenting", "the", "a", "an", "no", "any", "some", "his", "her", "their",
    "she", "he", "they", "for", "since", "over", "about", "last", "past", "of",
    "is", "are", "was", "were",
}
MAX_NGRAM = 6


class Finding(BaseModel):
    text: str
    concept: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    excluded: bool = False


class ParsedQuery(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    duration: str | None = None


@lru_cache(maxsize=1)
def _get_nlps():
    import spacy

    base = spacy.load("en_core_web_sm")
    try:
        import medspacy

        ctx = medspacy.load()
        if not ctx.has_pipe("medspacy_context"):
            ctx = None
    except Exception:
        ctx = None
    return base, ctx


def split_clauses(text: str) -> list[str]:
    return [p.strip() for p in SPLIT_RE.split(text) if p and p.strip()]


def extract_duration(text: str, doc=None) -> str | None:
    m = DURATION_RE.search(text)
    if m:
        return f"{m.group(1)} {m.group(2)}".lower()
    if doc is not None:
        for ent in doc.ents:
            if ent.label_ == "DATE":
                return ent.text
    return None


def _usable(tok) -> bool:
    return not (tok.is_punct or tok.is_space)


def _trim(span):
    doc, start, end = span.doc, span.start, span.end
    while start < end and (
        doc[start].lower_ in DROP_WORDS or not _usable(doc[start]) or doc[start].pos_ in {"DET", "PRON"}
    ):
        start += 1
    while end > start and (doc[end - 1].lower_ in DROP_WORDS or not _usable(doc[end - 1])):
        end -= 1
    return doc[start:end] if end > start else None


def _merge_of(doc, spans):
    out = []
    for sp in sorted(spans, key=lambda s: s.start):
        if out and sp.start == out[-1].end + 1 and doc[out[-1].end].lower_ == "of":
            out[-1] = doc[out[-1].start : sp.end]
        else:
            out.append(sp)
    return out


def _candidate_spans(doc):
    taken: set[int] = set()
    spans: list = []

    def add(span):
        spans.append(span)
        taken.update(range(span.start, span.end))

    n = len(doc)
    for size in range(min(MAX_NGRAM, n), 0, -1):
        for i in range(n - size + 1):
            if taken.intersection(range(i, i + size)):
                continue
            span = doc[i : i + size]
            if not (_usable(span[0]) and _usable(span[-1])):
                continue
            if span[0].lower_ in DROP_WORDS:
                continue
            if lookup_exact(span.text):
                add(span)

    for tok in doc:
        if tok.i in taken or tok.is_stop or not _usable(tok):
            continue
        if tok.lower_ in DROP_WORDS or len(tok.text) < MIN_FUZZY_LEN:
            continue
        if normalize(tok.text):
            add(doc[tok.i : tok.i + 1])

    try:
        chunks = list(doc.noun_chunks)
    except ValueError:
        chunks = []
    extras = []
    for chunk in chunks:
        span = _trim(chunk)
        if span is None or taken.intersection(range(span.start, span.end)):
            continue
        extras.append(span)
    for span in _merge_of(doc, extras):
        add(span)
    return sorted(spans, key=lambda s: s.start)


def _negation(clause: str, spans, ctx) -> list[bool]:
    """medspaCy ConText when available, regex fallback otherwise."""
    if ctx is not None:
        try:
            cdoc = ctx(clause)
            ents = [
                cdoc.char_span(s.start_char, s.end_char, label="FINDING", alignment_mode="expand")
                for s in spans
            ]
            if all(e is not None for e in ents):
                cdoc.ents = ents
                ctx.get_pipe("medspacy_context")(cdoc)
                return [bool(e._.is_negated) for e in cdoc.ents]
        except Exception:
            pass
    return [bool(NEG_RE.search(clause[: s.start_char])) for s in spans]


def _parse_clause(clause: str, base, ctx) -> list[Finding]:
    doc = base(clause)
    spans = _candidate_spans(doc)
    if not spans:
        return []
    out = []
    for span, neg in zip(spans, _negation(clause, spans, ctx)):
        concept = normalize(span.text)
        out.append(
            Finding(
                text=span.text,
                concept=concept.preferred_term if concept else None,
                synonyms=(concept.synonyms + concept.abbreviations) if concept else [],
                excluded=neg,
            )
        )
    return out


def parse_query(query: str) -> ParsedQuery:
    base, ctx = _get_nlps()
    full = base(query)
    duration = extract_duration(query, full)

    clean = DURATION_RE.sub(" ", query)
    for ent in full.ents:
        if ent.label_ == "DATE":
            clean = clean.replace(ent.text, " ")

    findings: list[Finding] = []
    seen: set = set()
    for clause in split_clauses(clean):
        for f in _parse_clause(clause, base, ctx):
            key = (f.concept or f.text.lower(), f.excluded)
            if key not in seen:
                seen.add(key)
                findings.append(f)
    return ParsedQuery(findings=findings, duration=duration)
