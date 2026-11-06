from app.services.question_service import (
    get_departments,
    get_questions_by_department
)

print("\nAvailable departments:")

departments = get_departments()

for department in departments:
    print("-", department)

print("\nTesting Credit department:")

questions = get_questions_by_department("Credit")

print("Total Credit questions:", len(questions))

for question in questions[:3]:
    print("\nQuestion ID:", question.question_id)
    print("Type:", question.question_type)
    print("Question:", question.question_text)