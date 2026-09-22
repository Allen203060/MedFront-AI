from src.actions.db_service import get_db_service
db = get_db_service()
for p in db.get_all_patients():
    print(f"ID: {p.id}, Email: {p.email}, Password: {p.password}")
