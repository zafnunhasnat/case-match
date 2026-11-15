import csv
from pathlib import Path

from backend.app.database.connection import SessionLocal
from backend.app.models import ClinicalTerm

CSV_PATH = Path("data/terminology/terms.csv")


def seed_database():
    db = SessionLocal()

    try:
        with open(CSV_PATH, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            inserted = 0
            skipped = 0

            for row in reader:
                synonym = row["synonym"].strip()

                if not synonym:
                    skipped += 1
                    continue

                existing = db.query(ClinicalTerm).filter_by(
                    synonym=synonym
                ).first()

                if existing:
                    skipped += 1
                    continue

                term = ClinicalTerm(
                    preferred_term=row["preferred_term"].strip(),
                    synonym=synonym,
                    abbreviation=row["abbreviation"].strip() or None,
                    terminology_code=row["terminology_code"].strip() or None,
                )

                db.add(term)
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
