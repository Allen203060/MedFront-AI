from src.actions.db_service import get_db_service
import sys
db = get_db_service()
appts = db.get_all_appointments()
for a in appts:
    if a.patient_id == "P-30406":
        print(f"Appt: {a.id} | Pat: {a.patient_id} | DocID: {a.doctor_id} | DocName: {a.doctor_name} | Date: {a.appointment_date} | Time: {a.appointment_time} | Status: {a.status}")
