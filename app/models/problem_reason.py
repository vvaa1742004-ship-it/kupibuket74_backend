from __future__ import annotations

from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import ReasonType
from app.models.base import Base


class ProblemReason(Base):
    __tablename__ = "problem_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ReasonType] = mapped_column(Enum(ReasonType, name="reason_type"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

