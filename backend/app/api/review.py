import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_reviewer
from app.database.connection import get_review_db
from app.models.audit_log import SearchAuditLog
from app.models.document import ClinicalDocument, OriginalDocument, ScreenedDocument
from app.models.doctor import Doctor

router = APIRouter()


class PendingReviewItem(BaseModel):
    document_id: uuid.UUID
    original_author_name: str
    department: str
    document_type: str
    ingested_at: datetime
    screened_text: str
    redactions_applied: bool
    redaction_count: int


class ReviewDocumentDetail(PendingReviewItem):
    original_text: str


class ReviewDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    review_note: str | None = Field(default=None, max_length=2000)


class ReviewDecisionResponse(BaseModel):
    document_id: uuid.UUID
    screening_status: Literal["approved", "rejected"]
    reviewed_by_id: uuid.UUID
    reviewed_at: datetime


@router.get("/pending", response_model=list[PendingReviewItem])
def get_pending_documents(
    current_user: Doctor = Depends(require_reviewer),
    db: Session = Depends(get_review_db),
):
    statement = (
        select(ScreenedDocument, ClinicalDocument)
        .join(
            ClinicalDocument,
            ScreenedDocument.clinical_document_id == ClinicalDocument.id,
        )
        .where(
            ScreenedDocument.screening_status == "pending_review",
            ClinicalDocument.original_author_id != current_user.id,
        )
        .order_by(ClinicalDocument.ingested_at.asc())
        .limit(100)
    )

    rows = db.execute(statement).all()

    return [
        PendingReviewItem(
            document_id=clinical.id,
            original_author_name=clinical.original_author_name,
            department=clinical.department,
            document_type=clinical.document_type,
            ingested_at=clinical.ingested_at,
            screened_text=screened.screened_text,
            redactions_applied=screened.redactions_applied,
            redaction_count=screened.redaction_count,
        )
        for screened, clinical in rows
    ]


@router.get("/{document_id}", response_model=ReviewDocumentDetail)
def get_document_for_review(
    document_id: uuid.UUID,
    current_user: Doctor = Depends(require_reviewer),
    db: Session = Depends(get_review_db),
):
    statement = (
        select(ScreenedDocument, ClinicalDocument, OriginalDocument)
        .join(
            ClinicalDocument,
            ScreenedDocument.clinical_document_id == ClinicalDocument.id,
        )
        .join(
            OriginalDocument,
            OriginalDocument.clinical_document_id == ClinicalDocument.id,
        )
        .where(ClinicalDocument.id == document_id)
    )

    row = db.execute(statement).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    screened, clinical, original = row

    if clinical.original_author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot review your own submission",
        )

    if screened.screening_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is no longer awaiting review",
        )

    return ReviewDocumentDetail(
        document_id=clinical.id,
        original_author_name=clinical.original_author_name,
        department=clinical.department,
        document_type=clinical.document_type,
        ingested_at=clinical.ingested_at,
        screened_text=screened.screened_text,
        redactions_applied=screened.redactions_applied,
        redaction_count=screened.redaction_count,
        original_text=original.original_text,
    )


@router.post(
    "/{document_id}/decision",
    response_model=ReviewDecisionResponse,
)
def decide_document(
    document_id: uuid.UUID,
    payload: ReviewDecisionRequest,
    current_user: Doctor = Depends(require_reviewer),
    db: Session = Depends(get_review_db),
):
    statement = (
        select(ScreenedDocument, ClinicalDocument)
        .join(
            ClinicalDocument,
            ScreenedDocument.clinical_document_id == ClinicalDocument.id,
        )
        .where(ClinicalDocument.id == document_id)
        .with_for_update()
    )

    row = db.execute(statement).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    screened, clinical = row

    if clinical.original_author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot review your own submission",
        )

    if screened.screening_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document has already been reviewed",
        )

    reviewed_at = datetime.now(timezone.utc)

    screened.screening_status = payload.decision
    screened.reviewed_by_id = current_user.id
    screened.reviewed_at = reviewed_at
    screened.review_note = (
        payload.review_note.strip()
        if payload.review_note
        else None
    )

    db.add(
        SearchAuditLog(
            doctor_id=current_user.id,
            document_id=clinical.id,
            action=f"document_{payload.decision}",
            query=None,
        )
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Review decision could not be saved",
        )

    return ReviewDecisionResponse(
        document_id=clinical.id,
        screening_status=payload.decision,
        reviewed_by_id=current_user.id,
        reviewed_at=reviewed_at,
    )