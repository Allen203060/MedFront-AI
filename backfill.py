import sys
from src.actions.db_service import get_db_service

db = get_db_service()
patients = db.get_all_patients()
count = 0
for p in patients:
    if not getattr(p, 'email', None) or not getattr(p, 'password', None):
        p.email = f"{p.first_name.lower()}.{p.last_name.lower()}@example.com"
        p.password = p.first_name.lower()
        
        # update in Cosmos
        try:
            db.register_patient(p)  # register_patient does upsert in CosmosDatabaseService
            count += 1
            print(f"Updated {p.id}")
        except Exception as e:
            print(f"Failed to update {p.id}: {e}")

print(f"Successfully backfilled {count} patients.")
