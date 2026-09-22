import re

file_path = "src/actions/db_service.py"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add _save_to_disk and _load_from_disk
methods_to_add = """
    def _save_to_disk(self):
        import json
        import os
        os.makedirs("data", exist_ok=True)
        try:
            data = {
                "patients": {k: v.model_dump() for k, v in self._patients.items()},
                "doctors": self._doctors,
                "schedules": {f"{k[0]}|{k[1]}": v.model_dump() for k, v in self._schedules.items()},
                "appointments": {k: v.model_dump() for k, v in self._appointments.items()},
                "clinical_notes": {k: [n.model_dump() for n in v] for k, v in self._clinical_notes.items()},
                "test_reports": {k: [n.model_dump() for n in v] for k, v in self._test_reports.items()},
                "visit_summaries": {k: [n.model_dump() for n in v] for k, v in self._visit_summaries.items()},
                "notifications": self._notifications,
            }
            with open("data/mock_db.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save mock db to disk: {e}")

    def _load_from_disk(self) -> bool:
        import json
        import os
        from src.actions.models import PatientRecord, DoctorSchedule, Appointment, ClinicalNote, TestReport, VisitSummary
        if not os.path.exists("data/mock_db.json"):
            return False
        try:
            with open("data/mock_db.json", "r") as f:
                data = json.load(f)
            self._patients = {k: PatientRecord.model_validate(v) for k, v in data.get("patients", {}).items()}
            self._doctors = data.get("doctors", [])
            self._schedules = {}
            for k, v in data.get("schedules", {}).items():
                parts = k.split("|")
                self._schedules[(parts[0], parts[1])] = DoctorSchedule.model_validate(v)
            self._appointments = {k: Appointment.model_validate(v) for k, v in data.get("appointments", {}).items()}
            self._clinical_notes = {k: [ClinicalNote.model_validate(n) for n in v] for k, v in data.get("clinical_notes", {}).items()}
            self._test_reports = {k: [TestReport.model_validate(n) for n in v] for k, v in data.get("test_reports", {}).items()}
            self._visit_summaries = {k: [VisitSummary.model_validate(n) for n in v] for k, v in data.get("visit_summaries", {}).items()}
            self._notifications = data.get("notifications", [])
            return True
        except Exception as e:
            logger.error(f"Failed to load mock db from disk: {e}")
            return False
"""

# Inject before _seed_default_data
content = content.replace("    def _seed_default_data(self):", methods_to_add + "\n    def _seed_default_data(self):")


# 2. Modify __init__
init_old = """        self._notifications: List[Dict[str, Any]] = []
        self._seed_default_data()"""
init_new = """        self._notifications: List[Dict[str, Any]] = []
        if not self._load_from_disk():
            self._seed_default_data()
            self._save_to_disk()"""
content = content.replace(init_old, init_new)

# 3. Add self._save_to_disk() to mutating methods
mutating_replacements = [
    (
        '        return True, "Appointment booked successfully.", new_appointment',
        '        self._save_to_disk()\n        return True, "Appointment booked successfully.", new_appointment'
    ),
    (
        '        return True, f"Appointment \'{appointment_id}\' has been cancelled successfully."',
        '        self._save_to_disk()\n        return True, f"Appointment \'{appointment_id}\' has been cancelled successfully."'
    ),
    (
        '        self._patients[patient.id] = patient\n        return patient',
        '        self._patients[patient.id] = patient\n        self._save_to_disk()\n        return patient'
    ),
    (
        '        self._clinical_notes[note.patient_id].insert(0, note)\n        return note',
        '        self._clinical_notes[note.patient_id].insert(0, note)\n        self._save_to_disk()\n        return note'
    ),
    (
        '        self._schedules[(doc_id, curr_date)] = sched\n        return new_doc',
        '        self._schedules[(doc_id, curr_date)] = sched\n        self._save_to_disk()\n        return new_doc'
    ),
    (
        '        self._notifications.append(record)\n        return record',
        '        self._notifications.append(record)\n        self._save_to_disk()\n        return record'
    )
]

for old, new in mutating_replacements:
    content = content.replace(old, new)

with open(file_path, "w") as f:
    f.write(content)
print("Patch applied successfully.")
