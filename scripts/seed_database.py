"""Load data/terminology/terms.csv into the clinical_terms table.

Safe to run more than once: rows that already exist (same preferred_term and
synonym) are skipped. Uses the admin connection because the restricted app role
should not be able to write vocabulary data.

Run from the repo root:
    PYTHONPATH=. python scripts/seed_terms.py
"""
import csv
from pathlib import Path

from backend.app.database.connection import AdminSessionLocal
from backend.app.models import ClinicalTerm

CSV_PATH = Path("data/terminology/terms.csv")
TERMINOLOGY_SYSTEM = "LOCAL"


def seed_database():
    db = AdminSessionLocal()
    inserted = 0
    skipped = 0

    try:
        # Existing rows, so re-running never creates duplicates.
        seen = {
            (t.preferred_term, t.synonym)
            for t in db.query(ClinicalTerm).all()
        }

        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                preferred = row["preferred_term"].strip()
                synonym = row["synonym"].strip()

                if not preferred or not synonym:
                    skipped += 1
                    continue

                key = (preferred, synonym)
                if key in seen:
                    skipped += 1
                    continue

                db.add(
                    ClinicalTerm(
                        preferred_term=preferred,
                        synonym=synonym,
                        abbreviation=(row.get("abbreviation") or "").strip() or None,
                        terminology_code=(row.get("terminology_code") or "").strip() or None,
                        terminology_system=TERMINOLOGY_SYSTEM,
                    )
                )
                seen.add(key)
                inserted += 1

        db.commit()
        print(f"Successfully inserted: {inserted}")
        print(f"Skipped: {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()