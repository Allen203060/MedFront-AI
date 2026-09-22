from src.actions.db_service import get_db_service
db = get_db_service()
appts = db.get_all_appointments()
fixed = 0
for a in appts:
    if a.doctor_id == "DOC-AZ":
        # Find real doctor id
        if "Ananya" in a.doctor_name:
            a.doctor_id = "DOC-01"
        elif "Rajesh" in a.doctor_name:
            a.doctor_id = "DOC-02"
        elif "Sunita" in a.doctor_name:
            a.doctor_id = "DOC-03"
        elif "Vikram" in a.doctor_name:
            a.doctor_id = "DOC-04"
        elif "Meera" in a.doctor_name:
            a.doctor_id = "DOC-05"
        
        db.appointments_container.upsert_item(body=a.model_dump())
        fixed += 1
print(f"Fixed {fixed} orphaned appointments!")
