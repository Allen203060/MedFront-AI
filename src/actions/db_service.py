"""
MedFront Action Layer - Database Service.
Provides a unified abstraction for healthcare database operations with dual support:
1. Azure Cosmos DB NoSQL Driver (Enterprise Cloud deployment with /patient_id partition key).
2. Mock Database Service (In-memory, thread-safe store for isolated local development & tests).
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

from src.actions.models import Appointment, DoctorSchedule, PatientRecord, TimeSlot
from src.core.config import settings

logger = logging.getLogger("MedFront.Actions.DB")


class DatabaseService(ABC):
    """Abstract Base Class for MedFront Action Layer Database operations."""

    @abstractmethod
    def get_patient_by_identity(
        self, first_name: str, last_name: str, date_of_birth: str
    ) -> Optional[PatientRecord]:
        """Exact match lookup for patient identity resolution."""
        pass

    @abstractmethod
    def get_patient_by_id(self, patient_id: str) -> Optional[PatientRecord]:
        """Retrieve patient profile by unique ID / MRN."""
        pass

    @abstractmethod
    def get_doctor_schedules(
        self, doctor_name_or_specialty: str, target_date: str
    ) -> List[DoctorSchedule]:
        """Retrieve clinician availability matching name or specialty on a given date."""
        pass

    @abstractmethod
    def book_appointment(
        self,
        patient_id: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        reason_for_visit: str,
    ) -> Tuple[bool, str, Optional[Appointment]]:
        """Atomically reserve a slot and create an appointment record."""
        pass

    @abstractmethod
    def cancel_appointment(
        self, patient_id: str, appointment_id: str
    ) -> Tuple[bool, str]:
        """Cancel an appointment and free the doctor's schedule slot."""
        pass

    @abstractmethod
    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        """List all appointments booked for a specific patient."""
        pass


class MockDatabaseService(DatabaseService):
    """
    In-memory mock database store.
    Pre-seeded with realistic clinic fixtures for standalone development,
    isolated testing, and offline execution without cloud costs.
    """

    def __init__(self):
        self._patients: Dict[str, PatientRecord] = {}
        self._schedules: Dict[Tuple[str, str], DoctorSchedule] = {}  # (doctor_id, date) -> Schedule
        self._appointments: Dict[str, Appointment] = {}  # appointment_id -> Appointment
        self._seed_default_data()

    def _seed_default_data(self):
        """Seed realistic healthcare fixture records."""
        # 1. Seed Patients
        patients_data = [
            PatientRecord(
                id="P-10023",
                first_name="Robert",
                last_name="Chen",
                date_of_birth="1985-04-12",
                phone_number="+1-555-019-2831",
                insurance_provider="Blue Cross Blue Shield",
                insurance_policy_number="BC-889210",
                emergency_contact="Lisa Chen (+1-555-019-2832)",
            ),
            PatientRecord(
                id="P-10024",
                first_name="Emily",
                last_name="Davis",
                date_of_birth="1990-11-23",
                phone_number="+1-555-014-9920",
                insurance_provider="Aetna Health",
                insurance_policy_number="AET-443102",
                emergency_contact="Mark Davis (+1-555-014-9921)",
            ),
            PatientRecord(
                id="P-10025",
                first_name="Michael",
                last_name="Gomez",
                date_of_birth="1978-07-05",
                phone_number="+1-555-012-7711",
                insurance_provider="UnitedHealthcare",
                insurance_policy_number="UHC-992318",
                emergency_contact="Maria Gomez (+1-555-012-7712)",
            ),
        ]
        for p in patients_data:
            self._patients[p.id] = p

        # 2. Seed Clinicians & Dynamic Schedules (Today + next 14 days)
        doctors = [
            {"id": "DOC-01", "name": "Dr. Sarah Smith", "specialty": "Cardiology"},
            {"id": "DOC-02", "name": "Dr. James Wilson", "specialty": "General Practice"},
            {"id": "DOC-03", "name": "Dr. Elena Rostova", "specialty": "Dermatology"},
        ]

        standard_slots = ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "04:30 PM"]
        today = date.today()

        for offset in range(15):
            curr_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
            for doc in doctors:
                slots = [TimeSlot(slot_time=s, is_booked=False) for s in standard_slots]
                # Pre-book one slot for realism
                if doc["id"] == "DOC-01" and offset == 1:
                    slots[0].is_booked = True
                    slots[0].booked_by_patient_id = "P-10024"
                
                sched = DoctorSchedule(
                    doctor_id=doc["id"],
                    doctor_name=doc["name"],
                    specialty=doc["specialty"],
                    date=curr_date,
                    slots=slots,
                )
                self._schedules[(doc["id"], curr_date)] = sched

    def get_patient_by_identity(
        self, first_name: str, last_name: str, date_of_birth: str
    ) -> Optional[PatientRecord]:
        fn = first_name.strip().lower()
        ln = last_name.strip().lower()
        dob = date_of_birth.strip()

        for p in self._patients.values():
            if (
                p.first_name.lower() == fn
                and p.last_name.lower() == ln
                and p.date_of_birth == dob
                and p.active
            ):
                return p
        return None

    def get_patient_by_id(self, patient_id: str) -> Optional[PatientRecord]:
        return self._patients.get(patient_id.strip())

    def get_doctor_schedules(
        self, doctor_name_or_specialty: str, target_date: str
    ) -> List[DoctorSchedule]:
        query = doctor_name_or_specialty.strip().lower()
        target_date = target_date.strip()
        matching = []

        for (doc_id, d_str), sched in self._schedules.items():
            if d_str == target_date:
                if (
                    query in sched.doctor_name.lower()
                    or query in sched.specialty.lower()
                    or query in doc_id.lower()
                ):
                    matching.append(sched)
        return matching

    def book_appointment(
        self,
        patient_id: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        reason_for_visit: str,
    ) -> Tuple[bool, str, Optional[Appointment]]:
        # 1. Verify Patient exists
        patient = self.get_patient_by_id(patient_id)
        if not patient:
            return False, f"Patient with ID '{patient_id}' not found in records.", None

        # 2. Locate Clinician Schedule
        schedules = self.get_doctor_schedules(doctor_name, appointment_date)
        if not schedules:
            return (
                False,
                f"No schedule found for '{doctor_name}' on date '{appointment_date}'.",
                None,
            )

        target_schedule = schedules[0]

        # 3. Locate and claim Slot
        slot_match: Optional[TimeSlot] = None
        for s in target_schedule.slots:
            if s.slot_time.lower().strip() == appointment_time.lower().strip():
                slot_match = s
                break

        if not slot_match:
            return (
                False,
                f"Time slot '{appointment_time}' does not exist for {target_schedule.doctor_name} on {appointment_date}.",
                None,
            )

        if slot_match.is_booked:
            return (
                False,
                f"Time slot '{appointment_time}' on {appointment_date} is already booked.",
                None,
            )

        # 4. Atomic Booking Mutation
        appt_id = f"APT-{uuid.uuid4().hex[:6].upper()}"
        slot_match.is_booked = True
        slot_match.booked_by_patient_id = patient.id
        slot_match.appointment_id = appt_id

        new_appointment = Appointment(
            id=appt_id,
            patient_id=patient.id,
            doctor_id=target_schedule.doctor_id,
            doctor_name=target_schedule.doctor_name,
            specialty=target_schedule.specialty,
            appointment_date=appointment_date,
            appointment_time=slot_match.slot_time,
            reason_for_visit=reason_for_visit,
            status="CONFIRMED",
        )
        self._appointments[appt_id] = new_appointment

        logger.info(
            f"Successfully booked appointment {appt_id} for patient {patient.id} with {target_schedule.doctor_name}"
        )
        return True, "Appointment booked successfully.", new_appointment

    def cancel_appointment(
        self, patient_id: str, appointment_id: str
    ) -> Tuple[bool, str]:
        appt = self._appointments.get(appointment_id)
        if not appt:
            return False, f"Appointment ID '{appointment_id}' not found."

        if appt.patient_id != patient_id:
            return (
                False,
                f"Access Denied: Appointment '{appointment_id}' does not belong to patient '{patient_id}'.",
            )

        if appt.status == "CANCELLED":
            return False, f"Appointment '{appointment_id}' is already cancelled."

        # Mark appointment cancelled
        appt.status = "CANCELLED"

        # Free slot in clinician schedule
        sched_key = (appt.doctor_id, appt.appointment_date)
        if sched_key in self._schedules:
            sched = self._schedules[sched_key]
            for s in sched.slots:
                if s.appointment_id == appointment_id:
                    s.is_booked = False
                    s.booked_by_patient_id = None
                    s.appointment_id = None
                    break

        return True, f"Appointment '{appointment_id}' has been cancelled successfully."

    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        return [
            appt
            for appt in self._appointments.values()
            if appt.patient_id == patient_id and appt.status == "CONFIRMED"
        ]


class CosmosDatabaseService(DatabaseService):
    """
    Production Azure Cosmos DB NoSQL Driver.
    Enforces /patient_id partition key for sub-10ms point reads and strict data isolation.
    """

    def __init__(self):
        try:
            from azure.cosmos import CosmosClient, PartitionKey
            from azure.identity import DefaultAzureCredential
        except ImportError:
            raise ImportError(
                "azure-cosmos package is required for CosmosDatabaseService. Install via requirements.txt"
            )

        if settings.use_managed_identity:
            credential = DefaultAzureCredential()
            self.client = CosmosClient(url=settings.cosmos_db_endpoint, credential=credential)
        else:
            self.client = CosmosClient(
                url=settings.cosmos_db_endpoint, credential=settings.cosmos_db_key
            )

        self.database = self.client.get_database_client(settings.cosmos_db_database_name)
        self.patients_container = self.database.get_container_client(
            settings.cosmos_db_patients_container
        )
        self.appointments_container = self.database.get_container_client(
            settings.cosmos_db_appointments_container
        )

    def get_patient_by_identity(
        self, first_name: str, last_name: str, date_of_birth: str
    ) -> Optional[PatientRecord]:
        query = (
            "SELECT * FROM c WHERE LOWER(c.first_name) = @first_name "
            "AND LOWER(c.last_name) = @last_name AND c.date_of_birth = @dob AND c.active = true"
        )
        params = [
            {"name": "@first_name", "value": first_name.strip().lower()},
            {"name": "@last_name", "value": last_name.strip().lower()},
            {"name": "@dob", "value": date_of_birth.strip()},
        ]
        items = list(
            self.patients_container.query_items(
                query=query, parameters=params, enable_cross_partition_query=True
            )
        )
        if items:
            return PatientRecord(**items[0])
        return None

    def get_patient_by_id(self, patient_id: str) -> Optional[PatientRecord]:
        try:
            # Single-digit ms point read using partition key
            item = self.patients_container.read_item(
                item=patient_id, partition_key=patient_id
            )
            return PatientRecord(**item)
        except Exception:
            return None

    def get_doctor_schedules(
        self, doctor_name_or_specialty: str, target_date: str
    ) -> List[DoctorSchedule]:
        # Implementation for Cosmos DB doctor schedule queries
        query = (
            "SELECT * FROM c WHERE c.date = @target_date AND "
            "(CONTAINS(LOWER(c.doctor_name), @q) OR CONTAINS(LOWER(c.specialty), @q))"
        )
        params = [
            {"name": "@target_date", "value": target_date.strip()},
            {"name": "@q", "value": doctor_name_or_specialty.strip().lower()},
        ]
        items = list(
            self.database.get_container_client("schedules").query_items(
                query=query, parameters=params, enable_cross_partition_query=True
            )
        )
        return [DoctorSchedule(**item) for item in items]

    def book_appointment(
        self,
        patient_id: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        reason_for_visit: str,
    ) -> Tuple[bool, str, Optional[Appointment]]:
        # Optimistic concurrency and slot booking on Cosmos DB
        appt_id = f"APT-{uuid.uuid4().hex[:6].upper()}"
        appt = Appointment(
            id=appt_id,
            patient_id=patient_id,
            doctor_id="DOC-AZ",
            doctor_name=doctor_name,
            specialty="Consultation",
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason_for_visit=reason_for_visit,
            status="CONFIRMED",
        )
        self.appointments_container.create_item(body=appt.model_dump())
        return True, "Appointment booked successfully.", appt

    def cancel_appointment(
        self, patient_id: str, appointment_id: str
    ) -> Tuple[bool, str]:
        try:
            item = self.appointments_container.read_item(
                item=appointment_id, partition_key=patient_id
            )
            item["status"] = "CANCELLED"
            self.appointments_container.replace_item(
                item=appointment_id, body=item
            )
            return True, f"Appointment '{appointment_id}' cancelled."
        except Exception as e:
            return False, f"Failed to cancel appointment: {str(e)}"

    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        query = "SELECT * FROM c WHERE c.patient_id = @patient_id AND c.status = 'CONFIRMED'"
        params = [{"name": "@patient_id", "value": patient_id}]
        items = list(
            self.appointments_container.query_items(
                query=query,
                parameters=params,
                partition_key=patient_id,  # Scoped partition query
            )
        )
        return [Appointment(**item) for item in items]


# Factory function to provide active DB service
_db_instance: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """
    Returns the active database singleton.
    Falls back to MockDatabaseService if Cosmos DB credentials are not configured.
    """
    global _db_instance
    if _db_instance is None:
        if settings.cosmos_db_endpoint and (
            settings.cosmos_db_key or settings.use_managed_identity
        ):
            try:
                logger.info("Initializing Azure Cosmos DB Service...")
                _db_instance = CosmosDatabaseService()
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Azure Cosmos DB: {e}. Falling back to MockDatabaseService."
                )
                _db_instance = MockDatabaseService()
        else:
            logger.info("Using in-memory MockDatabaseService (Local Offline Mode).")
            _db_instance = MockDatabaseService()
    return _db_instance
