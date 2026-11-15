
import os

from alembic import op


# revision identifiers
revision = '88359db9860b'
down_revision = 'be7d3bbb977b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    app_pw = os.getenv("APP_DB_PASSWORD", "app-pw-change-me").replace("'", "''")
    review_pw = os.getenv("REVIEW_DB_PASSWORD", "review-pw-change-me").replace("'", "''")

    op.execute(f"""
    DO $$ BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD '{app_pw}';
      END IF;
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'review_user') THEN
        CREATE ROLE review_user LOGIN PASSWORD '{review_pw}';
      END IF;
    END $$;
    """)

    op.execute("GRANT USAGE ON SCHEMA public TO app_user, review_user")

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

    op.execute("GRANT INSERT ON original_documents TO app_user")

    op.execute("""
        GRANT SELECT, INSERT ON original_documents
        TO review_user
    """)


def downgrade() -> None:
    op.execute("""
        REVOKE ALL ON ALL TABLES IN SCHEMA public
        FROM app_user, review_user
    """)
