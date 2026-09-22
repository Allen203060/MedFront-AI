from src.actions.db_service import get_db_service
db = get_db_service()
appts = db.get_all_appointments()
print(f"Total appointments: {len(appts)}")
for a in appts[-5:]:
    print(f"Appt: {a.id} | DocID: {a.doctor_id} | DocName: {a.doctor_name} | Pat: {a.patient_id}")
