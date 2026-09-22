from src.actions.db_service import get_db_service
import sys
db = get_db_service()
appts = db.get_all_appointments()
meera_appts = [a for a in appts if "Meera" in a.doctor_name]
print(f"Found {len(meera_appts)} appointments for Dr. Meera Nambiar.")
for a in meera_appts[-5:]:
    print(f"Appt: {a.id} | Pat: {a.patient_id} | DocID: {a.doctor_id} | DocName: {a.doctor_name} | Date: {a.appointment_date} | Time: {a.appointment_time} | Status: {a.status}")
