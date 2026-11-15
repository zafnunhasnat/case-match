"""Tighten application and reviewer database permissions.

Revision ID: a91f6c2d4e80
Revises: 88359db9860b
"""

from alembic import op

revision = "a91f6c2d4e80"
down_revision = "88359db9860b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the broad permissions granted by the previous migration.
    op.execute("""
        REVOKE ALL PRIVILEGES ON
            doctors,
            clinical_documents,
            screened_documents,
            document_embeddings,
            clinical_terms,
            search_audit_logs,
            original_documents
        FROM app_user, review_user
    """)

    # Both roles can look up users, but cannot modify accounts or roles.
    op.execute("""
        GRANT SELECT ON doctors TO app_user, review_user
    """)

    # Application account: submit documents and read screened data.
    op.execute("""
        GRANT SELECT, INSERT ON clinical_documents TO app_user
    """)
    op.execute("""
        GRANT SELECT, INSERT ON screened_documents TO app_user
    """)
    op.execute("""
        GRANT INSERT ON original_documents TO app_user
    """)
    op.execute("""
        GRANT SELECT, INSERT ON document_embeddings TO app_user
    """)
    op.execute("""
        GRANT SELECT ON clinical_terms TO app_user
    """)

    # Reviewer account: read documents and update review decisions.
    op.execute("""
        GRANT SELECT ON clinical_documents TO review_user
    """)
    op.execute("""
        GRANT SELECT, UPDATE ON screened_documents TO review_user
    """)
    op.execute("""
        GRANT SELECT ON original_documents TO review_user
    """)
    op.execute("""
        GRANT SELECT ON document_embeddings, clinical_terms
        TO review_user
    """)

    # Both accounts may record audit events, but neither can alter or
    # delete existing audit records.
    op.execute("""
        GRANT INSERT ON search_audit_logs TO app_user, review_user
    """)


def downgrade() -> None:
    # Restore the permissions from the previous migration.
    op.execute("""
        REVOKE ALL PRIVILEGES ON
            doctors,
            clinical_documents,
            screened_documents,
            document_embeddings,
            clinical_terms,
            search_audit_logs,
            original_documents
        FROM app_user, review_user
    """)

    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON
            doctors, clinical_documents, screened_documents,
            document_embeddings, clinical_terms
        TO app_user, review_user
    """)

    op.execute("""
        GRANT SELECT, INSERT ON search_audit_logs
        TO app_user, review_user
    """)

    op.execute("""
        GRANT INSERT ON original_documents TO app_user
    """)

    op.execute("""
        GRANT SELECT, INSERT ON original_documents TO review_user
    """)
