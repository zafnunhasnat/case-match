"""Keyword search over approved documents (Postgres full-text search).

One tsquery per finding, built by OR-ing its synonyms, so a finding counts once
however many synonyms match. All user text goes in as bound parameters.
No LIMIT: the promise is every relevant case.

Runs on the restricted application connection (SessionLocal), never the admin
one, and reads only approved, privacy-screened text.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.connection import SessionLocal
from backend.app.services.query_parser import ParsedQuery

HEADLINE_OPTIONS = "MaxFragments=2"

# The ONE place that decides what is searchable. Approved, screened text only.
# If your column or table names differ, change them here and nowhere else.
SEARCHABLE_SQL = """
SELECT
    sd.id               AS id,
    sd.screened_text    AS screened_text,
    sd.search_vector    AS search_vector,
    cd.department       AS department,
    cd.document_type    AS document_type,
    cd.created_at       AS document_date
FROM screened_documents sd
JOIN clinical_documents cd ON cd.id = sd.clinical_document_id
WHERE sd.screening_status = 'approved'
"""


def get_searchable_documents() -> str:
    """SQL for approved, screened documents. Every search reads through this."""
    return SEARCHABLE_SQL


class SearchFilters(BaseModel):
    department: str | None = None
    document_type: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class Candidate(BaseModel):
    document_id: str  # ids are UUIDs, so keep them as strings
    title: str | None = None
    department: str | None = None
    document_type: str | None = None
    document_date: date | None = None
    matched_findings: int
    total_findings: int
    matched_texts: list[str]
    matched_via: Literal["exact", "synonym"]
    score: float
    snippets: list[str]


def _terms(finding) -> list[str]:
    """Typed text first, then concept, synonyms and abbreviations (deduplicated)."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in [finding.text, finding.concept, *finding.synonyms]:
        if not raw:
            continue
        term = " ".join(raw.lower().split())
        if term and re.search(r"\w", term) and term not in seen:
            seen.add(term)
            out.append(term)
    return out


def _tsquery_sql(i: int, terms: list[str], params: dict) -> str:
    """plainto_tsquery per synonym, OR-ed with ||. Only bind names are interpolated."""
    parts = []
    for j, term in enumerate(terms):
        name = f"t{i}_{j}"
        params[name] = term
        parts.append(f"plainto_tsquery('english', :{name})")
    return "(" + " || ".join(parts) + ")"


def _filter_sql(filters: SearchFilters, params: dict) -> str:
    clauses = []
    if filters.department:
        params["f_department"] = filters.department
        clauses.append("d.department = :f_department")
    if filters.document_type:
        params["f_document_type"] = filters.document_type
        clauses.append("d.document_type = :f_document_type")
    if filters.date_from:
        params["f_date_from"] = filters.date_from
        clauses.append("d.document_date >= :f_date_from")
    if filters.date_to:
        params["f_date_to"] = filters.date_to
        clauses.append("d.document_date <= :f_date_to")
    return "".join(f" AND {c}" for c in clauses)


def _build_sql(active: list, filters: SearchFilters, params: dict) -> str:
    select_cols = []
    any_match = []
    for i, finding in enumerate(active):
        terms = _terms(finding)
        q = _tsquery_sql(i, terms, params)
        params[f"x{i}"] = terms[0]
        select_cols += [
            f"(d.search_vector @@ {q}) AS m{i}",
            f"(d.search_vector @@ plainto_tsquery('english', :x{i})) AS e{i}",
            f"CASE WHEN d.search_vector @@ {q} "
            f"THEN ts_rank(d.search_vector, {q}) ELSE 0 END AS r{i}",
            f"CASE WHEN d.search_vector @@ {q} "
            f"THEN ts_headline('english', d.screened_text, {q}, '{HEADLINE_OPTIONS}') "
            f"END AS h{i}",
        ]
        any_match.append(f"d.search_vector @@ {q}")
    return (
        "SELECT d.id AS document_id, d.department, d.document_type, "
        "d.document_date, " + ", ".join(select_cols) + " "
        f"FROM ({get_searchable_documents()}) d "
        "WHERE (" + " OR ".join(any_match) + ")" + _filter_sql(filters, params)
    )


def keyword_search(
    parsed: ParsedQuery,
    filters: SearchFilters | dict | None = None,
    db: Session | None = None,
) -> list[Candidate]:
    """Return every approved document matching at least one non-excluded finding."""
    if isinstance(filters, dict):
        filters = SearchFilters(**filters)
    filters = filters or SearchFilters()

    active = [f for f in parsed.findings if not f.excluded and _terms(f)]
    if not active:
        return []

    params: dict = {}
    sql = _build_sql(active, filters, params)

    own_session = db is None
    session = db or SessionLocal()
    try:
        rows = session.execute(text(sql), params).mappings().all()
    finally:
        if own_session:
            session.close()

    results: list[Candidate] = []
    for r in rows:
        hit = [i for i in range(len(active)) if r[f"m{i}"]]
        results.append(
            Candidate(
                document_id=str(r["document_id"]),
                department=r["department"],
                document_type=r["document_type"],
                document_date=r["document_date"],
                matched_findings=len(hit),
                total_findings=len(active),
                matched_texts=[active[i].text for i in hit],
                matched_via="exact" if any(r[f"e{i}"] for i in hit) else "synonym",
                score=sum(float(r[f"r{i}"]) for i in hit),
                snippets=[r[f"h{i}"] for i in hit if r[f"h{i}"]],
            )
        )
    results.sort(key=lambda c: (-c.matched_findings, -c.score, c.document_id))
    return results
