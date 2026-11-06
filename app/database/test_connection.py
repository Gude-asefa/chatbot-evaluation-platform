
from sqlalchemy import text

from app.database.connection import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database();")
        )
        print("Connected database:", result.scalar())

    print("Database connection successful!")

except Exception as error:
    print("Database connection failed:")
    print(error)
