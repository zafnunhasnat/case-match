import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from .base import Base

class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"
    __table_args__ = (
        Index("ix_embedding_hnsw", "embedding", postgresql_using="hnsw",
              postgresql_with={"m": 16, "ef_construction": 64},
              postgresql_ops={"embedding": "vector_cosine_ops"}),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    screened_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("screened_documents.id", ondelete="CASCADE"))
    section_index: Mapped[int] = mapped_column(Integer, default=0)
    section_text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(384))  # all-MiniLM-L6-v2 = 384 dims
    model_name: Mapped[str] = mapped_column(String(100))