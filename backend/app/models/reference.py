"""Reference data: CEFR levels and skills. Adding C1 content or a new skill is a row, not DDL."""

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CefrLevel(Base):
    __tablename__ = "cefr_levels"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)  # PRE_A1 … C1
    rank: Mapped[int] = mapped_column(SmallInteger, unique=True)  # 0 … 5, for comparisons
    label: Mapped[str] = mapped_column(String(16))  # "Pre-A1", "A1", …


class Skill(Base):
    __tablename__ = "skills"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)  # grammar, listening, …
    label: Mapped[str] = mapped_column(String(32))
