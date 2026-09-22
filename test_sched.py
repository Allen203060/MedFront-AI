from src.actions.db_service import get_db_service
db = get_db_service()
s = db.get_doctor_schedules("Dr. Meera Nambiar", "2026-09-22")
print("Schedule length:", len(s))
