from src.actions.db_service import get_db_service
db = get_db_service()
schedules = list(db.schedules_container.query_items(query="SELECT * FROM c WHERE c.doctor_id = 'DOC-05'", enable_cross_partition_query=True))
print(f"Meera schedules: {len(schedules)}")
for s in schedules:
    print(s['date'], s['doctor_name'])
