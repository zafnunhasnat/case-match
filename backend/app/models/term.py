import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class ClinicalTerm(Base):
    __tablename__ = "clinical_terms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    preferred_term: Mapped[str] = mapped_column(String(200), index=True)
    synonym: Mapped[str] = mapped_column(String(200), index=True)
    abbreviation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terminology_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    terminology_system: Mapped[str | None] = mapped_column(String(40), nullable=True)
