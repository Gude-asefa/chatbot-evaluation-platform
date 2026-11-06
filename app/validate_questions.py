
import pandas as pd
from pathlib import Path

# 1. Define the Excel file location
file_path = Path("data/Chatbot_Pilot_Test_Cases_Standardized.xlsx")

# 2. Check whether the file exists
if not file_path.exists():
    raise FileNotFoundError(f"Excel file not found: {file_path}")

# 3. Read the Excel worksheet
df = pd.read_excel(file_path, sheet_name="Questions")

print("\n========== WORKBOOK VALIDATION ==========")

# 4. Display basic information
print("\nTotal questions:", len(df))
print("Total columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())

# 5. Check department distribution
print("\nQuestions per department:")
print(df["Department"].value_counts().sort_index())

# 6. Check question types
print("\nQuestions per type:")
print(df["Question Type"].value_counts())

# 7. Check missing values
print("\nMissing values per column:")
print(df.isnull().sum())

# 8. Check duplicate question IDs
print("\nDuplicate question IDs:", df["Question ID"].duplicated().sum())

# 9. Check unique departments
print("\nDepartments:", sorted(df["Department"].unique()))

# 10. Display sample questions
print("\nFirst 5 questions:")
print(
    df[["Department", "Question ID", "Question Type"]]
    .head()
    .to_string(index=False)
)

print("\n========== VALIDATION COMPLETED ==========")
