
from app.database.connection import engine
from app.database.models import Base

# Create all tables defined in models.py
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
