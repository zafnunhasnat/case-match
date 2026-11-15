CREATE TABLE IF NOT EXISTS clinical_documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    screened_text TEXT NOT NULL DEFAULT '',
    department TEXT,
    document_type TEXT,
    document_date DATE,
    status TEXT NOT NULL DEFAULT 'draft',
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(screened_text, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_clinical_documents_search
ON clinical_documents USING GIN (search_vector);

CREATE OR REPLACE FUNCTION get_searchable_documents()
RETURNS SETOF clinical_documents
LANGUAGE sql
STABLE
AS $$
    SELECT *
    FROM clinical_documents
    WHERE status = 'approved';
$$;
