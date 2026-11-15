import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.connection import get_db
from app.models.audit_log import SearchAuditLog
from app.models.document import (
    ClinicalDocument,
    OriginalDocument,
    ScreenedDocument,
)
from app.models.doctor import Doctor
from app.services.privacy import screen_text
from app.services.rate_limit import limiter

router = APIRouter()


class DocumentIngestionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100000)
    document_type: str = Field(min_length=1, max_length=60)
    created_at: datetime | None = None
    source_reference: str | None = Field(default=None, max_length=200)


class DocumentIngestionResponse(BaseModel):
    document_id: uuid.UUID
    screening_status: Literal["pending_review"]
    redactions_applied: bool
    redaction_count: int


@router.post(
    "/",
    response_model=DocumentIngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def ingest_document(
    request: Request,
    payload: DocumentIngestionRequest,
    db: Session = Depends(get_db),
    current_user: Doctor = Depends(get_current_user),
):
    original_text = payload.text.strip()

    if not original_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document text cannot be empty",
        )

    document_type = payload.document_type.strip()
    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document type cannot be empty",
        )

    # Fail closed: never store a document if screening is unavailable.
    try:
        screening = screen_text(original_text)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document screening is temporarily unavailable",
        )

    clinical_document = ClinicalDocument(
        original_author_id=current_user.id,
        original_author_name=current_user.name,
        department=current_user.department,
        document_type=document_type,
        created_at=payload.created_at,
        source_reference=(
            payload.source_reference.strip() or None
            if payload.source_reference is not None
            else None
        ),
    )

    try:
        db.add(clinical_document)
        db.flush()

        # The original text is stored separately in the restricted table.
        db.add(
            OriginalDocument(
                clinical_document_id=clinical_document.id,
                original_text=original_text,
            )
        )

        # Only screened text is available in the normal document table.
        db.add(
            ScreenedDocument(
                clinical_document_id=clinical_document.id,
                screened_text=screening.screened_text,
                screening_status="pending_review",
                redactions_applied=screening.redactions_applied,
                redaction_count=screening.redaction_count,
                screening_method=screening.screening_method,
            )
        )

        # Never put the original document text in the audit log.
        db.add(
            SearchAuditLog(
                doctor_id=current_user.id,
                document_id=clinical_document.id,
                action="document_submitted",
                query=None,
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document could not be submitted",
        )

    return DocumentIngestionResponse(
        document_id=clinical_document.id,
        screening_status="pending_review",
        redactions_applied=screening.redactions_applied,
        redaction_count=screening.redaction_count,
    )