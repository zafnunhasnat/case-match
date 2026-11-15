import csv
import os
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://zahra@localhost:5432/casematch"
)
CSV_PATH = Path("data/terminology/terms.csv")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS clinical_terms (
    id SERIAL PRIMARY KEY,
    preferred_term VARCHAR(255) NOT NULL,
    synonym VARCHAR(255) NOT NULL UNIQUE,
    abbreviation VARCHAR(100),
    terminology_code VARCHAR(100)
)
"""

INSERT_SQL = text(
    "INSERT INTO clinical_terms (preferred_term, synonym, abbreviation, terminology_code) "
    "VALUES (:p, :s, :a, :c) ON CONFLICT (synonym) DO NOTHING"
)


def seed_database():
    engine = create_engine(DATABASE_URL)
    inserted = skipped = 0
    with engine.begin() as conn:
        conn.execute(text(CREATE_SQL))
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                synonym = row["synonym"].strip()
                if not synonym:
                    skipped += 1
                    continue
                result = conn.execute(
                    INSERT_SQL,
                    {
                        "p": row["preferred_term"].strip(),
                        "s": synonym,
                        "a": row["abbreviation"].strip() or None,
                        "c": row["terminology_code"].strip() or None,
                    },
                )
                if result.rowcount:
                    inserted += 1
                else:
                    skipped += 1
    print(f"Inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    seed_database()
