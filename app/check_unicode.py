import pandas as pd

from app.database.connection import SessionLocal
from app.database.models import Question

# Read the original Excel file
df = pd.read_excel(
    "data/Chatbot_Pilot_Test_Cases_Standardized.xlsx",
    sheet_name="Questions"
)

# Connect to the database
session = SessionLocal()

try:
    for question_id in ["CRD-INFO-004", "CRD-INFO-006"]:

        excel_row = df.loc[df["Question ID"] == question_id].iloc[0]

        excel_text = str(excel_row["Question / Test Instructions"])

        db_question = (
            session.query(Question)
            .filter_by(question_id=question_id)
            .one()
        )

        db_text = db_question.question_text

        print(f"\nQuestion ID: {question_id}")
        print("Excel text:", ascii(excel_text))
        print("Database text:", ascii(db_text))
        print("Texts match:", excel_text == db_text)

finally:
    session.close()