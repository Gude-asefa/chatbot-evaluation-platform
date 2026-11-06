
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_department_progress,
)

print("\nOVERALL DASHBOARD SUMMARY")

summary = get_dashboard_summary()

for key, value in summary.items():
    print(f"{key}: {value}")


print("\nDEPARTMENT PROGRESS")

departments = get_department_progress()

for department in departments:
    print(department)
