
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Base class for all database models
class Base(DeclarativeBase):
    pass


# ---------------------------------
# QUESTIONS TABLE
# ---------------------------------
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    department: Mapped[str] = mapped_column(String(100), nullable=False)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(150), nullable=False)

    question_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )

    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


# ---------------------------------
# EVALUATIONS TABLE
# ---------------------------------
class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"), nullable=False
    )

    actual_answer: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
)

    status: Mapped[str] = mapped_column(String(50), nullable=False)

    comments: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Identifies an anonymous testing session
    session_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# ---------------------------------
# SUBMISSIONS TABLE
# One submission per device, department, section and language
# ---------------------------------
class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "department",
            "section",
            "language",
            name="uq_submission_device_section_language",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    # Anonymous identifier stored in the tester's browser
    device_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    department: Mapped[str] = mapped_column(String(100), nullable=False)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
