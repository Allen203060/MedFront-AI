from src.actions.db_service import get_db_service
db = get_db_service()
patients = db.get_all_patients()
print("Total patients:", len(patients))
divyas = [p for p in patients if "divya" in p.first_name.lower() or "divya" in p.last_name.lower()]
print("Divyas found:", divyas)
