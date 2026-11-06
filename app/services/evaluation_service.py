
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.connection import SessionLocal
from app.database.models import Evaluation, Question, Submission


class AlreadySubmittedError(Exception):
    """Raised when a device re-submits the same section and language."""


def get_submitted_sections(device_id, department):
    """Return {(section, language)} this device already submitted."""
    if not device_id:
        return set()

    session = SessionLocal()

    try:
        rows = session.execute(
            select(Submission.section, Submission.language).where(
                Submission.device_id == device_id,
                Submission.department == department,
            )
        ).all()
        return {(row.section, row.language) for row in rows}

    finally:
        session.close()


def save_evaluations(
    evaluations,
    *,
    device_id=None,
    department=None,
    section=None,
    language=None,
):
    """Save evaluations.

    When device_id is given, a submission lock is recorded in the same
    transaction so each device can submit a department/section/language
    combination only once (enforced by a unique constraint).
    """
    session = SessionLocal()

    try:
        records = []

        if device_id:
            session.add(
                Submission(
                    device_id=device_id,
                    department=department,
                    section=section,
                    language=language,
                )
            )
            try:
                session.flush()
            except IntegrityError as error:
                raise AlreadySubmittedError(
                    f"You have already submitted an evaluation for "
                    f"{section} ({language})."
                ) from error

        for item in evaluations:

            question = session.get(Question, item["question_id"])

            if not question:
                raise ValueError(
                    f"Question not found: {item['question_id']}"
                )

            status = item["status"]
            actual_answer = item.get("actual_answer")
            comments = item.get("comments")

            if question.section.lower() == "information":
                allowed_statuses = [
                    "Passed",
                    "Failed",
                    "Not Enough Info",
                ]
            elif question.section.lower() == "action":
                allowed_statuses = [
                    "Passed",
                    "Failed",
                ]
            else:
                raise ValueError(
                    f"Unknown question section: {question.section}"
                )

            if status not in allowed_statuses:
                raise ValueError(
                    f"Invalid status '{status}' for {question.question_id}."
                )

            # Actual response is required for Failed and Not Enough Info
            if status in ["Failed", "Not Enough Info"]:
                if not str(actual_answer or "").strip():
                    raise ValueError(
                        f"Actual chatbot response is required for "
                        f"{status}: {question.question_id}."
                    )

            # Comment is required for Not Enough Info
            if status == "Not Enough Info":
                if not str(comments or "").strip():
                    raise ValueError(
                        f"Please explain what should be improved for "
                        f"{question.question_id}."
                    )

            records.append(
                Evaluation(
                    question_id=question.id,
                    actual_answer=str(actual_answer).strip()
                    if actual_answer else None,
                    status=status,
                    comments=str(comments).strip()
                    if comments else None,
                    session_id=device_id,
                )
            )

        session.add_all(records)
        session.commit()

        return len(records)

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
