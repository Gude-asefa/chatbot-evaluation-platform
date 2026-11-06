
from sqlalchemy import select, func, case

from app.database.connection import SessionLocal
from app.database.models import Question, Evaluation


def get_dashboard_summary():
    """Return overall evaluation statistics."""

    with SessionLocal() as session:

        statement = select(
            func.count(Evaluation.id).label("total"),
            func.sum(
                case((Evaluation.status == "Passed", 1), else_=0)
            ).label("passed"),
            func.sum(
                case((Evaluation.status == "Failed", 1), else_=0)
            ).label("failed"),
            func.sum(
                case(
                    (Evaluation.status == "Not Enough Info", 1),
                    else_=0,
                )
            ).label("not_enough_info"),
        )

        result = session.execute(statement).one()

        return {
            "total": result.total or 0,
            "passed": result.passed or 0,
            "failed": result.failed or 0,
            "not_enough_info": result.not_enough_info or 0,
        }


def get_department_progress():
    """Return evaluation progress for each department."""

    with SessionLocal() as session:

        statement = (
            select(
                Question.department,
                func.count(func.distinct(Question.id)).label(
                    "total_questions"
                ),
                func.count(
                    func.distinct(Evaluation.question_id)
                ).label("evaluated_questions"),
            )
            .outerjoin(
                Evaluation,
                Evaluation.question_id == Question.id,
            )
            .where(Question.is_active == True)
            .group_by(Question.department)
            .order_by(Question.department)
        )

        results = session.execute(statement).all()

        department_data = []

        for row in results:

            total = row.total_questions or 0
            evaluated = row.evaluated_questions or 0

            progress = (
                round((evaluated / total) * 100, 2)
                if total > 0
                else 0
            )

            department_data.append({
                "department": row.department,
                "total_questions": total,
                "evaluated_questions": evaluated,
                "remaining_questions": total - evaluated,
                "progress": progress,
            })

        return department_data


def get_evaluation_records(
    department=None,
    section=None,
    language=None,
    status=None,
):
    """Retrieve evaluation records with their questions."""

    with SessionLocal() as session:

        statement = (
            select(
                Evaluation.id,
                Question.department,
                Question.section,
                Question.language,
                Question.question_id,
                Question.category,
                Question.question_text,
                Evaluation.actual_answer,
                Evaluation.status,
                Evaluation.comments,
                Evaluation.submitted_at,
            )
            .join(
                Question,
                Evaluation.question_id == Question.id,
            )
            .order_by(Evaluation.submitted_at.desc())
        )

        if department and department != "All":
            statement = statement.where(
                Question.department == department
            )

        if section and section != "All":
            statement = statement.where(
                Question.section == section
            )

        if language and language != "All":
            statement = statement.where(
                Question.language == language
            )

        if status and status != "All":
            statement = statement.where(
                Evaluation.status == status
            )

        results = session.execute(statement).mappings().all()

        return [dict(row) for row in results]
