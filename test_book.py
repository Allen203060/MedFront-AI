from src.actions.db_service import get_db_service
db = get_db_service()
try:
    res = db.book_appointment("P-30406", "Dr. Meera Nambiar", "2026-09-22", "11:30 AM", "test")
    print(res)
except Exception as e:
    print(f"EXCEPTION: {type(e).__name__} - {str(e)}")
