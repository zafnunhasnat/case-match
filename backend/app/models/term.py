from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.connection import Base


class ClinicalTerm(Base):
    __tablename__ = "clinical_terms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    preferred_term: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    synonym: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    abbreviation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terminology_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
