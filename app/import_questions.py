
from pathlib import Path

import pandas as pd

from app.database.connection import SessionLocal
from app.database.models import Question

# Locate the Excel workbook
BASE_DIR = Path(__file__).resolve().parents[1]
EXCEL_FILE = BASE_DIR / "data" / "Chatbot_Pilot_Test_Cases_Standardized.xlsx"

# Read Excel data
df = pd.read_excel(EXCEL_FILE, sheet_name="Questions")

# Check for duplicate IDs before importing
if df["Question ID"].duplicated().any():
    raise ValueError("Duplicate question IDs found in Excel.")

# Convert Excel Yes/No values into Python Boolean values
def convert_active(value):
    if isinstance(value, bool):
        return value

    value = str(value).strip().lower()

    if value in ("yes", "true", "1"):
        return True
    if value in ("no", "false", "0"):
        return False

    raise ValueError(f"Invalid Is Active value: {value}")


session = SessionLocal()

try:
    # Find question IDs already stored in the database
    existing_ids = {
        row[0]
        for row in session.query(Question.question_id).all()
    }

    questions_to_insert = []

    for _, row in df.iterrows():
        question_id = str(row["Question ID"]).strip()

        # Skip questions that already exist
        if question_id in existing_ids:
            continue

        expected_answer = row["Expected Answer"]

        if pd.isna(expected_answer):
            expected_answer = None
        else:
            expected_answer = str(expected_answer).strip() or None

        question = Question(
            department=str(row["Department"]).strip(),
            section=str(row["Section"]).strip(),
            category=str(row["Category"]).strip(),
            question_id=question_id,
            question_type=str(row["Question Type"]).strip(),
            language=str(row["Language"]).strip(),
            question_text=str(
                row["Question / Test Instructions"]
            ).strip(),
            expected_answer=expected_answer,
            is_active=convert_active(row["Is Active"]),
        )

        questions_to_insert.append(question)

    # Insert all new questions
    session.add_all(questions_to_insert)
    session.commit()

    print("========== IMPORT RESULTS ==========")
    print("Total questions in Excel:", len(df))
    print("New questions imported:", len(questions_to_insert))
    print("Already existing questions:", len(existing_ids))
    print("Import completed successfully!")

except Exception as error:
    session.rollback()
    print("Import failed:", error)
    raise

finally:
    session.close()
