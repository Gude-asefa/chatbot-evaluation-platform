
from sqlalchemy import text

from app.database.connection import engine

with engine.begin() as connection:
    connection.execute(
        text("""
            ALTER TABLE evaluations
            ALTER COLUMN actual_answer DROP NOT NULL;
        """)
    )

print("Database schema updated successfully!")
