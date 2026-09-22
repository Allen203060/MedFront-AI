from src.actions.db_service import get_db_service
import sys
db = get_db_service()
patients = db.get_all_patients()
print(f"Total patients: {len(patients)}")
for p in patients[-5:]:
    print(f"Pat: {p.id} | Name: {p.first_name} {p.last_name} | Phone: {p.phone_number}")
