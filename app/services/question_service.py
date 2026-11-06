from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import Question


def get_departments():
    """Return all departments that have active questions."""

    with SessionLocal() as session:
        statement = (
            select(Question.department)
            .where(Question.is_active == True)
            .distinct()
            .order_by(Question.department)
        )

        return session.execute(statement).scalars().all()


def get_questions_by_department(department):
    """Return active questions assigned to a department."""

    with SessionLocal() as session:
        statement = (
            select(Question)
            .where(
                Question.department == department,
                Question.is_active == True
            )
            .order_by(Question.id)
        )

        return session.execute(statement).scalars().all()