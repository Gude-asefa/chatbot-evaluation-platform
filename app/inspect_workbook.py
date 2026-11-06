
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCEL_FILE = (
    PROJECT_ROOT
    / "data"
    / "Pilot_test_for_customer_chatbot.xlsx"
)

df = pd.read_excel(
    EXCEL_FILE,
    sheet_name="Credit",
    header=None
)

print("ROWS 20 TO 30:\n")

for index in range(20, 31):
    print(f"Row {index}: {df.iloc[index].tolist()}")
