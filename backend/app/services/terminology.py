"""Map free-text phrases to a clinical concept.

Starter vocabulary: data/terminology/terms.csv (small, local, no license needed).
Future upgrade: SNOMED CT / UMLS (both require a license).
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process

CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "terminology" / "terms.csv"
FUZZY_THRESHOLD = 90
MIN_FUZZY_LEN = 5


class Concept(BaseModel):
    preferred_term: str
    terminology_code: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    abbreviations: list[str] = Field(default_factory=list)
    matched: str
    method: Literal["exact", "fuzzy"]
    score: float = 100.0


@lru_cache(maxsize=1)
def _get_nlp():
    try:
        import spacy

        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception:
        return None


@lru_cache(maxsize=4096)
def lemmatize(text: str) -> str:
    """Lowercase, strip punctuation, lemmatize each word."""
    text = re.sub(r"[^\w\s/&-]", " ", text.lower())
    text = " ".join(text.split())
    nlp = _get_nlp()
    if nlp is None or not text:
        return text
    return " ".join(t.lemma_.lower() for t in nlp(text) if not t.is_space)


def load_rows(path: Path = CSV_PATH) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def _build_index():
    concepts: dict[str, dict] = {}
    index: dict[str, str] = {}
    for row in load_rows():
        pref = row["preferred_term"].strip().lower()
        syn = row["synonym"].strip().lower()
        abbr = (row.get("abbreviation") or "").strip()
        code = (row.get("terminology_code") or "").strip() or None
        c = concepts.setdefault(pref, {"code": code, "synonyms": [], "abbreviations": []})
        if code and not c["code"]:
            c["code"] = code
        if syn and syn not in c["synonyms"]:
            c["synonyms"].append(syn)
        if abbr and abbr not in c["abbreviations"]:
            c["abbreviations"].append(abbr)
        for term in (pref, syn, abbr):
            if term:
                index.setdefault(lemmatize(term), pref)
    return concepts, index, list(index)


def _make(pref: str, matched: str, method: str, score: float) -> Concept:
    concepts, _, _ = _build_index()
    c = concepts[pref]
    return Concept(
        preferred_term=pref,
        terminology_code=c["code"],
        synonyms=list(c["synonyms"]),
        abbreviations=list(c["abbreviations"]),
        matched=matched,
        method=method,
        score=score,
    )


def lookup_exact(phrase: str) -> Concept | None:
    _, index, _ = _build_index()
    pref = index.get(lemmatize(phrase))
    return _make(pref, phrase, "exact", 100.0) if pref else None


def normalize(phrase: str) -> Concept | None:
    """lowercase -> lemma -> exact lookup -> rapidfuzz fallback (threshold 90)."""
    concept = lookup_exact(phrase)
    if concept:
        return concept
    key = lemmatize(phrase)
    if len(key) < MIN_FUZZY_LEN:
        return None
    _, index, keys = _build_index()
    hit = process.extractOne(key, keys, scorer=fuzz.ratio, score_cutoff=FUZZY_THRESHOLD)
    if hit is None:
        return None
    match, score, _ = hit
    return _make(index[match], phrase, "fuzzy", float(score))
