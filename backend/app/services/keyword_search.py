import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import text
from backend.app.database.connection import SessionLocal


class Candidate(BaseModel):
    document_id: int
    matched_findings: List[str]
    total_findings: int
    matched_via: str  # "exact" or "synonym"
    snippets: List[str]


def get_searchable_documents() -> str:
    """Base SQL restricting all searches to approved clinical documents only."""
    return (
        "SELECT id, screened_text, department, doc_type, created_at, status, search_vector "
        "FROM clinical_documents WHERE status = 'approved'"
    )


def _format_ts_term(term: str) -> str:
    """Sanitizes a clinical phrase into a safe tsquery token or AND-group."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", term).strip().lower()
    words = cleaned.split()
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    return f"({' & '.join(words)})"


def _build_finding_tsquery(finding: Any) -> tuple[str, str]:
    """
    Builds one OR-ed tsquery per finding (e.g. 'dyspnea | (shortness & breath) | sob')
    and a separate tsquery for the exact user phrase to distinguish 'exact' vs 'synonym'.
    """
    exact_text = getattr(finding, "text", "") or ""
    concept = getattr(finding, "concept", "") or ""
    synonyms = getattr(finding, "synonyms", []) or []

    exact_ts = _format_ts_term(exact_text) or _format_ts_term(concept)

    seen = set()
    parts = []
    for raw_term in [concept, exact_text, *synonyms]:
        formatted = _format_ts_term(raw_term)
        if formatted and formatted not in seen:
            seen.add(formatted)
            parts.append(formatted)

    return " | ".join(parts), exact_ts


def keyword_search(
    parsed: Any, filters: Optional[Dict[str, Any]] = None
) -> List[Candidate]:
    """
    Searches approved clinical documents using PostgreSQL full-text search.
    Counts each finding once regardless of how many synonyms match, uses bound
    parameters only, applies optional filters, and imposes no LIMIT.
    """
    if not parsed or not getattr(parsed, "findings", None):
        return []

    active_findings = [
        f for f in parsed.findings if not getattr(f, "excluded", False)
    ]
    if not active_findings:
        return []

    filters = filters or {}
    params: Dict[str, Any] = {}
    finding_queries: List[tuple[str, str, str]] = []

    for idx, finding in enumerate(active_findings):
        syn_q, exact_q = _build_finding_tsquery(finding)
        if syn_q:
            q_param = f"q_{idx}"
            e_param = f"exact_{idx}"
            params[q_param] = syn_q
            params[e_param] = exact_q or syn_q
            label = getattr(finding, "concept", None) or getattr(finding, "text", "")
            finding_queries.append((label, q_param, e_param))

    if not finding_queries:
        return []

    total_findings = len(finding_queries)
    combined_q = " | ".join(f"({params[q_p]})" for _, q_p, _ in finding_queries)
    params["combined_q"] = combined_q

    # Per-finding match flags (each finding counts at most once) and rank sum
    match_cols = []
    exact_cols = []
    rank_terms = []
    match_conditions = []

    for idx, (_, q_p, e_p) in enumerate(finding_queries):
        match_cols.append(
            f"(search_vector @@ to_tsquery('english', :{q_p})) AS matched_{idx}"
        )
        exact_cols.append(
            f"(search_vector @@ to_tsquery('english', :{e_p})) AS exact_{idx}"
        )
        rank_terms.append(
            f"ts_rank(search_vector, to_tsquery('english', :{q_p}))"
        )
        match_conditions.append(
            f"search_vector @@ to_tsquery('english', :{q_p})"
        )

    where_clauses = [f"({' OR '.join(match_conditions)})"]

    if filters.get("department"):
        where_clauses.append("department = :department")
        params["department"] = filters["department"]
    if filters.get("document_type"):
        where_clauses.append("doc_type = :document_type")
        params["document_type"] = filters["document_type"]
    if filters.get("date_from"):
        where_clauses.append("created_at >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where_clauses.append("created_at <= :date_to")
        params["date_to"] = filters["date_to"]

    # No LIMIT on final result so every relevant approved case is returned
    sql = f"""
        WITH approved_docs AS (
            {get_searchable_documents()}
        )
        SELECT
            id,
            ({ ' + '.join(rank_terms) }) AS rank,
            ts_headline('english', screened_text, to_tsquery('english', :combined_q), 'MaxFragments=2') AS snippet,
            {', '.join(match_cols)},
            {', '.join(exact_cols)}
        FROM approved_docs
        WHERE {' AND '.join(where_clauses)}
        ORDER BY rank DESC;
    """

    db = SessionLocal()
    try:
        rows = db.execute(text(sql), params).fetchall()
    finally:
        db.close()

    candidates: List[Candidate] = []
    num_f = len(finding_queries)

    for row in rows:
        doc_id = row[0]
        snippet = row[2]
        matched_flags = row[3 : 3 + num_f]
        exact_flags = row[3 + num_f : 3 + 2 * num_f]

        matched_findings = [
            finding_queries[i][0]
            for i, is_match in enumerate(matched_flags)
            if is_match
        ]
        any_exact = any(
            exact_flags[i] for i, is_match in enumerate(matched_flags) if is_match
        )
        matched_via = "exact" if any_exact else "synonym"

        candidates.append(
            Candidate(
                document_id=doc_id,
                matched_findings=matched_findings,
                total_findings=total_findings,
                matched_via=matched_via,
                snippets=[snippet] if snippet else [],
            )
        )

    return candidates
