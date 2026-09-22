from src.actions.db_service import get_db_service
import sys

db = get_db_service()

patients = db.get_all_patients()
deleted = 0
for p in patients:
    if "test" in p.first_name.lower() or "test" in p.last_name.lower():
        print(f"Deleting dummy patient: {p.id} - {p.first_name} {p.last_name}")
        # Cosmos DB deletion requires partition key, which is id
        db.patients_container.delete_item(item=p.id, partition_key=p.id)
        deleted += 1

print(f"\nDeleted {deleted} dummy test patients from Cosmos DB.")
