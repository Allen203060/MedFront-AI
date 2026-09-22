from src.actions.db_service import get_db_service
db = get_db_service()
patients = db.get_all_patients()
for p in patients:
    if "test" in p.first_name.lower() or "test" in p.last_name.lower() or "dummy" in p.first_name.lower():
        print(f"Found dummy patient: {p.id} - {p.first_name} {p.last_name}")
