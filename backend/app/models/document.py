import uuid
from datetime import datetime
from sqlalchemy import (String, Text, Boolean, Integer, DateTime, ForeignKey, Index,
                        Computed, CheckConstraint, func)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class ClinicalDocument(Base):
    """Provenance metadata. Never changed by screening."""
    __tablename__ = "clinical_documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    original_author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("doctors.id"), nullable=True)
    original_author_name: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(80))
    document_type: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class OriginalDocument(Base):
    """Restricted: raw text with identifiers. app_user can only INSERT here."""
    __tablename__ = "original_documents"
    clinical_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_documents.id", ondelete="CASCADE"), primary_key=True)
    original_text: Mapped[str] = mapped_column(Text)

class ScreenedDocument(Base):
    __tablename__ = "screened_documents"
    __table_args__ = (
        CheckConstraint(
            "screening_status IN ('pending_review','approved','rejected','failed')",
            name="ck_screening_status"),
        Index("ix_screened_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_screened_status", "screening_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clinical_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_documents.id", ondelete="CASCADE"), unique=True)
    screened_text: Mapped[str] = mapped_column(Text)
    screening_status: Mapped[str] = mapped_column(String(20), default="pending_review")
    redactions_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    redaction_count: Mapped[int] = mapped_column(Integer, default=0)
    screening_method: Mapped[str] = mapped_column(String(60))
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("doctors.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Keyword search (Person 3) uses this generated column
    search_vector = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', screened_text)", persisted=True))