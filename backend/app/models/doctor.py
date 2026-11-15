import uuid
from sqlalchemy import String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = (CheckConstraint("role IN ('doctor','reviewer','admin')", name="ck_doctor_role"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20), default="doctor")
    password_hash: Mapped[str] = mapped_column(String(200))