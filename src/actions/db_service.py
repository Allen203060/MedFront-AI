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
from typing import Any, Dict, List, Optional, Tuple

from src.actions.models import (
    Appointment,
    ClinicalNote,
    DoctorSchedule,
    PatientRecord,
    TimeSlot,
)
from src.core.config import settings

logger = logging.getLogger("MedFront.Actions.DB")


DEFAULT_CLINIC_DOCTORS = [
    {
        "id": "DOC-01",
        "name": "Dr. Ananya Rao",
        "specialty": "Cardiology",
        "qualification": "MD (AIIMS), FACC",
        "department": "Department of Cardiovascular Sciences",
        "badge": "Chief Cardiologist",
        "avatar": "🫀",
        "color": "#0d9488",
    },
    {
        "id": "DOC-02",
        "name": "Dr. Rajesh Iyer",
        "specialty": "General Practice",
        "qualification": "MBBS, MD (Internal Medicine)",
        "department": "Internal & Preventative Medicine",
        "badge": "Senior Consultant Physician",
        "avatar": "🩺",
        "color": "#0284c7",
    },
    {
        "id": "DOC-03",
        "name": "Dr. Sunita Kapoor",
        "specialty": "Dermatology",
        "qualification": "MD (Dermatology, Venereology & Leprosy)",
        "department": "Clinical & Aesthetic Dermatology",
        "badge": "Lead Dermatologist",
        "avatar": "🔬",
        "color": "#8b5cf6",
    },
    {
        "id": "DOC-04",
        "name": "Dr. Vikram Sen",
        "specialty": "Orthopedics",
        "qualification": "MS (Orthopedics), MCh",
        "department": "Orthopedics & Joint Reconstruction",
        "badge": "Senior Joint Specialist",
        "avatar": "🦴",
        "color": "#f59e0b",
    },
    {
        "id": "DOC-05",
        "name": "Dr. Meera Nambiar",
        "specialty": "Pediatrics",
        "qualification": "MD (Pediatrics), DCH",
        "department": "Child Health & Adolescent Medicine",
        "badge": "Consultant Pediatrician",
        "avatar": "👶",
        "color": "#10b981",
    },
]


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

    @abstractmethod
    def get_doctor_appointments(
        self, doctor_name_or_id: str, target_date: Optional[str] = None
    ) -> List[Appointment]:
        """List all appointments for a specific doctor."""
        pass

    @abstractmethod
    def get_all_patients(self) -> List[PatientRecord]:
        """List all registered patients in the database."""
        pass

    @abstractmethod
    def register_patient(self, patient: PatientRecord) -> PatientRecord:
        """Register a new patient into the database."""
        pass

    @abstractmethod
    def get_all_appointments(self) -> List[Appointment]:
        """List all appointments (confirmed and cancelled) in the database."""
        pass

    @abstractmethod
    def create_clinical_note(self, note: ClinicalNote) -> ClinicalNote:
        """Persist a confirmed clinical SOAP note."""
        pass

    @abstractmethod
    def get_patient_clinical_notes(self, patient_id: str) -> List[ClinicalNote]:
        """Retrieve all longitudinal clinical notes for a patient."""
        pass

    @abstractmethod
    def get_doctors(self) -> List[Dict[str, Any]]:
        """List active clinic doctors."""
        pass

    @abstractmethod
    def add_doctor(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new doctor and generate availability schedules."""
        pass

    @abstractmethod
    def send_appointment_notification(
        self, appointment_id: str, channel: str = "SMS"
    ) -> Dict[str, Any]:
        """Sends SMS / WhatsApp confirmation notification ticket for an appointment."""
        pass

    @abstractmethod
    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent appointment notification logs."""
        pass




class MockDatabaseService(DatabaseService):
    """
    In-memory mock database store.
    Pre-seeded with realistic clinic fixtures for standalone development,
    isolated testing, and offline execution without cloud costs.
    """

    def __init__(self):
        self._patients: Dict[str, PatientRecord] = {}
        self._doctors: List[Dict[str, Any]] = [dict(d) for d in DEFAULT_CLINIC_DOCTORS]
        self._schedules: Dict[Tuple[str, str], DoctorSchedule] = {}  # (doctor_id, date) -> Schedule
        self._appointments: Dict[str, Appointment] = {}  # appointment_id -> Appointment
        self._clinical_notes: Dict[str, List[ClinicalNote]] = {}  # patient_id -> List[ClinicalNote]
        self._notifications: List[Dict[str, Any]] = []
        self._seed_default_data()

    def _seed_default_data(self):
        """Seed realistic healthcare fixture records."""
        # 1. Seed Patients
        patients_data = [
            PatientRecord(
                id="P-10023",
                first_name="Aarav",
                last_name="Sharma",
                date_of_birth="1985-04-12",
                phone_number="+91-98765-43210",
                insurance_provider="Star Health Comprehensive",
                insurance_policy_number="SH-889210",
                emergency_contact="Neha Sharma (+91-98765-43211)",
            ),
            PatientRecord(
                id="P-10024",
                first_name="Priya",
                last_name="Patel",
                date_of_birth="1985-11-22",
                phone_number="+91-98123-45678",
                insurance_provider="HDFC ERGO Health",
                insurance_policy_number="HE-443102",
                emergency_contact="Amit Patel (+91-98123-45679)",
            ),
            PatientRecord(
                id="P-10025",
                first_name="Vikram",
                last_name="Malhotra",
                date_of_birth="1978-07-05",
                phone_number="+91-99887-76655",
                insurance_provider="Care Health Insurance",
                insurance_policy_number="CH-992318",
                emergency_contact="Pooja Malhotra (+91-99887-76656)",
            ),
            PatientRecord(
                id="P-10026",
                first_name="Sneha",
                last_name="Gupta",
                date_of_birth="1992-03-14",
                phone_number="+91-98223-34455",
                insurance_provider="Niva Bupa Health",
                insurance_policy_number="NB-332190",
                emergency_contact="Rajesh Gupta (+91-98223-34456)",
            ),
            PatientRecord(
                id="P-10027",
                first_name="Rahul",
                last_name="Verma",
                date_of_birth="1988-09-30",
                phone_number="+91-97112-23344",
                insurance_provider="ICICI Lombard",
                insurance_policy_number="IL-551029",
                emergency_contact="Sunita Verma (+91-97112-23345)",
            ),
            PatientRecord(
                id="P-10028",
                first_name="Ananya",
                last_name="Desai",
                date_of_birth="2015-05-12",
                phone_number="+91-98334-45566",
                insurance_provider="Star Health Comprehensive",
                insurance_policy_number="SH-889211",
                emergency_contact="Kavita Desai (+91-98334-45567)",
            ),
        ]
        for p in patients_data:
            self._patients[p.id] = p

        # 2. Seed Clinicians & Dynamic Schedules spanning 09:00 AM to 09:00 PM (Today + next 30 days)
        standard_slots = [
            "09:00 AM", "10:00 AM", "11:30 AM", "01:00 PM",
            "02:30 PM", "04:00 PM", "05:30 PM", "07:00 PM", "08:30 PM"
        ]
        today = date.today()

        for offset in range(30):
            curr_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
            for doc in self._doctors:
                slots = [TimeSlot(slot_time=s, is_booked=False) for s in standard_slots]
                sched = DoctorSchedule(
                    doctor_id=doc["id"],
                    doctor_name=doc["name"],
                    specialty=doc["specialty"],
                    date=curr_date,
                    slots=slots,
                )
                self._schedules[(doc["id"], curr_date)] = sched

        # 3. Seed Confirmed Appointments for Each Doctor
        today_str = str(today)
        tmrw_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        default_appts = [
            Appointment(
                id="APT-C101",
                patient_id="P-10023",
                doctor_id="DOC-01",
                doctor_name="Dr. Ananya Rao",
                specialty="Cardiology",
                appointment_date=today_str,
                appointment_time="09:00 AM",
                reason_for_visit="Hypertension 6-month checkup & BP review",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-C102",
                patient_id="P-10025",
                doctor_id="DOC-01",
                doctor_name="Dr. Ananya Rao",
                specialty="Cardiology",
                appointment_date=today_str,
                appointment_time="11:30 AM",
                reason_for_visit="Post-coronary stent routine followup",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-C103",
                patient_id="P-10027",
                doctor_id="DOC-01",
                doctor_name="Dr. Ananya Rao",
                specialty="Cardiology",
                appointment_date=tmrw_str,
                appointment_time="02:00 PM",
                reason_for_visit="Exertional palpitations & ECG evaluation",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-G201",
                patient_id="P-10024",
                doctor_id="DOC-02",
                doctor_name="Dr. Rajesh Iyer",
                specialty="General Practice",
                appointment_date=today_str,
                appointment_time="10:00 AM",
                reason_for_visit="Seasonal allergic rhinitis & throat irritation",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-G202",
                patient_id="P-10026",
                doctor_id="DOC-02",
                doctor_name="Dr. Rajesh Iyer",
                specialty="General Practice",
                appointment_date=today_str,
                appointment_time="03:30 PM",
                reason_for_visit="Annual executive physical & blood panel",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-D301",
                patient_id="P-10026",
                doctor_id="DOC-03",
                doctor_name="Dr. Sunita Kapoor",
                specialty="Dermatology",
                appointment_date=today_str,
                appointment_time="09:00 AM",
                reason_for_visit="Eczema flare-up & contact dermatitis",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-D302",
                patient_id="P-10024",
                doctor_id="DOC-03",
                doctor_name="Dr. Sunita Kapoor",
                specialty="Dermatology",
                appointment_date=today_str,
                appointment_time="02:00 PM",
                reason_for_visit="Skin allergen patch test review",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-O401",
                patient_id="P-10027",
                doctor_id="DOC-04",
                doctor_name="Dr. Vikram Sen",
                specialty="Orthopedics",
                appointment_date=today_str,
                appointment_time="10:00 AM",
                reason_for_visit="Right knee ligament strain evaluation",
                status="CONFIRMED",
            ),
            Appointment(
                id="APT-P501",
                patient_id="P-10028",
                doctor_id="DOC-05",
                doctor_name="Dr. Meera Nambiar",
                specialty="Pediatrics",
                appointment_date=today_str,
                appointment_time="11:30 AM",
                reason_for_visit="Routine pediatric growth & immunizations",
                status="CONFIRMED",
            ),
        ]
        for a in default_appts:
            self._appointments[a.id] = a
            # Mark the slot booked in schedule
            sched_key = (a.doctor_id, a.appointment_date)
            if sched_key in self._schedules:
                for s in self._schedules[sched_key].slots:
                    if s.slot_time == a.appointment_time:
                        s.is_booked = True
                        s.booked_by_patient_id = a.patient_id
                        s.appointment_id = a.id
                        break

        # 4. Seed Clinical Notes
        self._clinical_notes["P-10023"] = [
            ClinicalNote(
                id="NOTE-10023-1",
                patient_id="P-10023",
                patient_name="Aarav Sharma",
                doctor_id="DOC-01",
                doctor_name="Dr. Ananya Rao",
                date="2025-08-10",
                subjective="40-year-old male presents for 6-month hypertension follow-up. Reports mild occasional headaches after long work hours. Compliant with prescribed Lisinopril.",
                objective="BP 138/88 mmHg, HR 72 bpm, SpO2 98% on room air. BMI 26.8.",
                assessment="Essential hypertension, suboptimally controlled; Stage 1.",
                plan="Increase Lisinopril from 10mg daily to 20mg daily orally after breakfast. Advise low sodium DASH diet. Order basic metabolic panel (BMP) in 4 weeks. Review in 6 weeks.",
                status="CONFIRMED_BY_DOCTOR",
            )
        ]
        self._clinical_notes["P-10024"] = [
            ClinicalNote(
                id="NOTE-10024-1",
                patient_id="P-10024",
                patient_name="Priya Patel",
                doctor_id="DOC-02",
                doctor_name="Dr. Rajesh Iyer",
                date="2025-07-15",
                subjective="39-year-old female presents with seasonal allergic rhinitis, frequent sneezing, nasal congestion. Severe allergy to Penicillin.",
                objective="Vital signs stable, afebrile. Swollen nasal turbinates with clear watery discharge.",
                assessment="Moderate allergic rhinitis. Penicillin allergy confirmed.",
                plan="Start Fluticasone propionate nasal spray 50mcg, 2 sprays per nostril once daily. Tab Cetirizine 10mg as needed.",
                status="CONFIRMED_BY_DOCTOR",
            )
        ]

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

    def get_all_patients(self) -> List[PatientRecord]:
        return list(self._patients.values())

    def register_patient(self, patient: PatientRecord) -> PatientRecord:
        self._patients[patient.id] = patient
        return patient

    def get_all_appointments(self) -> List[Appointment]:
        return list(self._appointments.values())

    def get_doctor_appointments(
        self, doctor_name_or_id: str, target_date: Optional[str] = None
    ) -> List[Appointment]:
        q = doctor_name_or_id.strip().lower()
        res = []
        for appt in self._appointments.values():
            if q in appt.doctor_name.lower() or q == appt.doctor_id.lower():
                if target_date is None or appt.appointment_date == target_date:
                    res.append(appt)
        return sorted(res, key=lambda a: (a.appointment_date, a.appointment_time))

    def create_clinical_note(self, note: ClinicalNote) -> ClinicalNote:
        if note.patient_id not in self._clinical_notes:
            self._clinical_notes[note.patient_id] = []
        self._clinical_notes[note.patient_id].insert(0, note)
        return note

    def get_patient_clinical_notes(self, patient_id: str) -> List[ClinicalNote]:
        return self._clinical_notes.get(patient_id, [])

    def get_doctors(self) -> List[Dict[str, Any]]:
        return self._doctors

    def add_doctor(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = doc_data.get("id") or f"DOC-0{len(self._doctors) + 1}"
        new_doc = {
            "id": doc_id,
            "name": doc_data["name"].strip(),
            "specialty": doc_data.get("specialty", "General Practice").strip(),
            "qualification": doc_data.get("qualification", "MD").strip(),
            "department": doc_data.get("department", "Clinical Department").strip(),
            "badge": doc_data.get("badge", "Consultant Specialist").strip(),
            "avatar": doc_data.get("avatar", "🩺"),
            "color": doc_data.get("color", "#0d9488"),
        }
        self._doctors.append(new_doc)

        # Seed schedules for next 15 days
        standard_slots = doc_data.get("slots") or ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "04:30 PM"]
        today = date.today()
        for offset in range(15):
            curr_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
            slots = [TimeSlot(slot_time=s, is_booked=False) for s in standard_slots]
            sched = DoctorSchedule(
                doctor_id=doc_id,
                doctor_name=new_doc["name"],
                specialty=new_doc["specialty"],
                date=curr_date,
                slots=slots,
            )
            self._schedules[(doc_id, curr_date)] = sched
        return new_doc

    def send_appointment_notification(
        self, appointment_id: str, channel: str = "SMS"
    ) -> Dict[str, Any]:
        appt = self._appointments.get(appointment_id)
        if not appt:
            return {"success": False, "message": f"Appointment {appointment_id} not found."}
        pat = self._patients.get(appt.patient_id)
        pat_phone = pat.phone_number if pat else "+91-98765-43210"
        pat_name = f"{pat.first_name} {pat.last_name}" if pat else f"Patient {appt.patient_id}"

        msg_body = (
            f"Dear {pat_name}, your appointment with {appt.doctor_name} is confirmed for "
            f"{appt.appointment_date} at {appt.appointment_time} (Booking Ticket: {appt.id}) at MedFront Health Clinic. "
            f"Please arrive 10 minutes prior."
        )
        logger.info(f"[{channel} NOTIFICATION SENT] To {pat_phone}: '{msg_body}'")
        appt.notification_sent = True
        appt.notification_channel = channel
        appt.notification_recipient = pat_phone
        appt.notification_ticket_id = appt.id

        record = {
            "success": True,
            "channel": channel,
            "recipient_phone": pat_phone,
            "patient_name": pat_name,
            "patient_id": appt.patient_id,
            "doctor_name": appt.doctor_name,
            "appointment_id": appt.id,
            "ticket_number": appt.id,
            "appointment_date": appt.appointment_date,
            "appointment_time": appt.appointment_time,
            "message": msg_body,
            "status": "DELIVERED",
            "timestamp": datetime.now().isoformat(),
        }
        self._notifications.append(record)
        return record

    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._notifications[-limit:]))




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

        # Auto-provision database and containers with partition keys if they do not exist
        self.database = self.client.create_database_if_not_exists(settings.cosmos_db_database_name)
        self.patients_container = self.database.create_container_if_not_exists(
            id=settings.cosmos_db_patients_container,
            partition_key=PartitionKey(path="/id"),
        )
        self.appointments_container = self.database.create_container_if_not_exists(
            id=settings.cosmos_db_appointments_container,
            partition_key=PartitionKey(path="/patient_id"),
        )
        self.schedules_container = self.database.create_container_if_not_exists(
            id="schedules",
            partition_key=PartitionKey(path="/doctor_id"),
        )
        self.notes_container = self.database.create_container_if_not_exists(
            id="clinical_notes",
            partition_key=PartitionKey(path="/patient_id"),
        )
        self._doctors = [dict(d) for d in DEFAULT_CLINIC_DOCTORS]
        self._ensure_seed_data()

    def _ensure_seed_data(self):
        """Seeds initial Indian patients and clinician schedules if container is empty."""
        try:
            items = list(self.patients_container.query_items(
                query="SELECT TOP 1 * FROM c", enable_cross_partition_query=True
            ))
            if not items:
                logger.info("Cosmos DB patients container is empty. Auto-seeding initial fixtures...")
                patients_data = [
                    PatientRecord(
                        id="P-10023",
                        first_name="Aarav",
                        last_name="Sharma",
                        date_of_birth="1985-04-12",
                        phone_number="+91-98765-43210",
                        insurance_provider="Star Health Comprehensive",
                        insurance_policy_number="SH-889210",
                        emergency_contact="Neha Sharma (+91-98765-43211)",
                    ),
                    PatientRecord(
                        id="P-10024",
                        first_name="Priya",
                        last_name="Patel",
                        date_of_birth="1985-11-22",
                        phone_number="+91-98123-45678",
                        insurance_provider="HDFC ERGO Health",
                        insurance_policy_number="HE-443102",
                        emergency_contact="Amit Patel (+91-98123-45679)",
                    ),
                    PatientRecord(
                        id="P-10025",
                        first_name="Vikram",
                        last_name="Malhotra",
                        date_of_birth="1978-07-05",
                        phone_number="+91-99887-76655",
                        insurance_provider="Care Health Insurance",
                        insurance_policy_number="CH-992318",
                        emergency_contact="Pooja Malhotra (+91-99887-76656)",
                    ),
                    PatientRecord(
                        id="P-10026",
                        first_name="Sneha",
                        last_name="Gupta",
                        date_of_birth="1992-03-14",
                        phone_number="+91-98223-34455",
                        insurance_provider="Niva Bupa Health",
                        insurance_policy_number="NB-332190",
                        emergency_contact="Rajesh Gupta (+91-98223-34456)",
                    ),
                    PatientRecord(
                        id="P-10027",
                        first_name="Rahul",
                        last_name="Verma",
                        date_of_birth="1988-09-30",
                        phone_number="+91-97112-23344",
                        insurance_provider="ICICI Lombard",
                        insurance_policy_number="IL-551029",
                        emergency_contact="Sunita Verma (+91-97112-23345)",
                    ),
                    PatientRecord(
                        id="P-10028",
                        first_name="Ananya",
                        last_name="Desai",
                        date_of_birth="2015-05-12",
                        phone_number="+91-98334-45566",
                        insurance_provider="Star Health Comprehensive",
                        insurance_policy_number="SH-889211",
                        emergency_contact="Kavita Desai (+91-98334-45567)",
                    ),
                ]
                for p in patients_data:
                    self.patients_container.upsert_item(body=p.model_dump())

            # Ensure all clinic doctors have schedules from 9 AM to 9 PM for today and future 30 days
            standard_slots = [
                "09:00 AM", "10:00 AM", "11:30 AM", "01:00 PM",
                "02:30 PM", "04:00 PM", "05:30 PM", "07:00 PM", "08:30 PM"
            ]
            today = date.today()

            for offset in range(30):
                curr_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
                for doc in DEFAULT_CLINIC_DOCTORS:
                    sched_id = f"{doc['id']}_{curr_date}"
                    slots = [TimeSlot(slot_time=s, is_booked=False) for s in standard_slots]
                    sched = DoctorSchedule(
                        doctor_id=doc["id"],
                        doctor_name=doc["name"],
                        specialty=doc["specialty"],
                        date=curr_date,
                        slots=slots
                    )
                    doc_body = sched.model_dump()
                    doc_body["id"] = sched_id
                    self.schedules_container.upsert_item(body=doc_body)

            # Seed default confirmed appointments if container is empty
            appt_check = list(self.appointments_container.query_items(
                query="SELECT TOP 1 * FROM c", enable_cross_partition_query=True
            ))
            if not appt_check:
                today_str = str(today)
                tmrw_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
                default_appts = [
                    Appointment(
                        id="APT-C101",
                        patient_id="P-10023",
                        doctor_id="DOC-01",
                        doctor_name="Dr. Ananya Rao",
                        specialty="Cardiology",
                        appointment_date=today_str,
                        appointment_time="09:00 AM",
                        reason_for_visit="Hypertension 6-month checkup & BP review",
                        status="CONFIRMED",
                    ),
                    Appointment(
                        id="APT-C102",
                        patient_id="P-10025",
                        doctor_id="DOC-01",
                        doctor_name="Dr. Ananya Rao",
                        specialty="Cardiology",
                        appointment_date=today_str,
                        appointment_time="11:30 AM",
                        reason_for_visit="Post-coronary stent routine followup",
                        status="CONFIRMED",
                    ),
                    Appointment(
                        id="APT-G201",
                        patient_id="P-10024",
                        doctor_id="DOC-02",
                        doctor_name="Dr. Rajesh Iyer",
                        specialty="General Practice",
                        appointment_date=today_str,
                        appointment_time="10:00 AM",
                        reason_for_visit="Seasonal allergic rhinitis & throat irritation",
                        status="CONFIRMED",
                    ),
                    Appointment(
                        id="APT-D301",
                        patient_id="P-10026",
                        doctor_id="DOC-03",
                        doctor_name="Dr. Sunita Kapoor",
                        specialty="Dermatology",
                        appointment_date=today_str,
                        appointment_time="09:00 AM",
                        reason_for_visit="Eczema flare-up & contact dermatitis",
                        status="CONFIRMED",
                    ),
                    Appointment(
                        id="APT-O401",
                        patient_id="P-10027",
                        doctor_id="DOC-04",
                        doctor_name="Dr. Vikram Sen",
                        specialty="Orthopedics",
                        appointment_date=today_str,
                        appointment_time="10:00 AM",
                        reason_for_visit="Right knee ligament strain evaluation",
                        status="CONFIRMED",
                    ),
                    Appointment(
                        id="APT-P501",
                        patient_id="P-10028",
                        doctor_id="DOC-05",
                        doctor_name="Dr. Meera Nambiar",
                        specialty="Pediatrics",
                        appointment_date=today_str,
                        appointment_time="11:30 AM",
                        reason_for_visit="Routine pediatric growth & immunizations",
                        status="CONFIRMED",
                    ),
                ]
                for a in default_appts:
                    self.appointments_container.upsert_item(body=a.model_dump())

                logger.info("Successfully seeded Cosmos DB containers.")
        except Exception as e:
            logger.warning(f"Could not auto-seed Cosmos DB: {e}")

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
        # Query schedules container
        query = (
            "SELECT * FROM c WHERE c.date = @target_date AND "
            "(CONTAINS(LOWER(c.doctor_name), @q) OR CONTAINS(LOWER(c.specialty), @q))"
        )
        params = [
            {"name": "@target_date", "value": target_date.strip()},
            {"name": "@q", "value": doctor_name_or_specialty.strip().lower()},
        ]
        items = list(
            self.schedules_container.query_items(
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
        # Check if slot is already booked (double-booking prevention)
        query = (
            "SELECT * FROM c WHERE LOWER(c.doctor_name) = @doc "
            "AND c.appointment_date = @date AND c.appointment_time = @time AND c.status = 'CONFIRMED'"
        )
        params = [
            {"name": "@doc", "value": doctor_name.strip().lower()},
            {"name": "@date", "value": appointment_date.strip()},
            {"name": "@time", "value": appointment_time.strip()},
        ]
        existing = list(
            self.appointments_container.query_items(
                query=query, parameters=params, enable_cross_partition_query=True
            )
        )
        if existing:
            return (
                False,
                f"Time slot '{appointment_time}' on {appointment_date} is already booked.",
                None,
            )

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

    def get_all_patients(self) -> List[PatientRecord]:
        query = "SELECT * FROM c WHERE c.active = true"
        items = list(
            self.patients_container.query_items(
                query=query, enable_cross_partition_query=True
            )
        )
        return [PatientRecord(**item) for item in items]

    def get_all_appointments(self) -> List[Appointment]:
        query = "SELECT * FROM c"
        items = list(
            self.appointments_container.query_items(
                query=query, enable_cross_partition_query=True
            )
        )
        return [Appointment(**item) for item in items]

    def get_doctor_appointments(
        self, doctor_name_or_id: str, target_date: Optional[str] = None
    ) -> List[Appointment]:
        query = "SELECT * FROM c WHERE (CONTAINS(LOWER(c.doctor_name), @doc) OR c.doctor_id = @doc_id)"
        params = [
            {"name": "@doc", "value": doctor_name_or_id.strip().lower()},
            {"name": "@doc_id", "value": doctor_name_or_id.strip()},
        ]
        if target_date:
            query += " AND c.appointment_date = @target_date"
            params.append({"name": "@target_date", "value": target_date})
        try:
            items = list(
                self.appointments_container.query_items(
                    query=query, parameters=params, enable_cross_partition_query=True
                )
            )
            res = [Appointment(**item) for item in items]
            return sorted(res, key=lambda a: (a.appointment_date, a.appointment_time))
        except Exception as e:
            logger.warning(f"Error querying doctor appointments in Cosmos DB: {e}")
            return []

    def register_patient(self, patient: PatientRecord) -> PatientRecord:
        try:
            self.patients_container.upsert_item(body=patient.model_dump())
            logger.info(f"Registered patient {patient.id} in Cosmos DB.")
        except Exception as e:
            logger.warning(f"Error registering patient in Cosmos DB: {e}")
        return patient

    def create_clinical_note(self, note: ClinicalNote) -> ClinicalNote:
        try:
            self.notes_container.upsert_item(body=note.model_dump())
            logger.info(f"Persisted clinical note {note.id} for patient {note.patient_id} in Cosmos DB.")
        except Exception as e:
            logger.warning(f"Error persisting clinical note to Cosmos DB: {e}")
        return note

    def get_patient_clinical_notes(self, patient_id: str) -> List[ClinicalNote]:
        notes = []
        try:
            query = "SELECT * FROM c WHERE c.patient_id = @pid"
            params = [{"name": "@pid", "value": patient_id}]
            items = list(
                self.notes_container.query_items(
                    query=query, parameters=params, partition_key=patient_id
                )
            )
            for item in items:
                notes.append(ClinicalNote(**item))
        except Exception as e:
            logger.warning(f"Error reading clinical notes from Cosmos DB: {e}")

        # Fallback to sample records if container is new / no dynamic notes yet
        if not notes:
            import os
            records_file = "data/knowledge/sample_patient_records.json"
            if os.path.exists(records_file):
                try:
                    import json
                    with open(records_file, "r", encoding="utf-8") as f:
                        all_recs = json.load(f)
                    for r in all_recs:
                        if r.get("patient_id") == patient_id and r.get("record_type") == "soap_note":
                            notes.append(
                                ClinicalNote(
                                    id=r.get("id", f"NOTE-{patient_id}-1"),
                                    patient_id=patient_id,
                                    patient_name=r.get("patient_name", "Patient"),
                                    doctor_id="DOC-01",
                                    doctor_name=r.get("author", "Dr. Ananya Rao"),
                                    date=r.get("timestamp", "2025-08-10")[:10],
                                    subjective=r.get("content", ""),
                                    objective="Vitals recorded during clinical encounter.",
                                    assessment="Clinical evaluation as noted.",
                                    plan="Continue prescribed therapeutic plan.",
                                    status="CONFIRMED_BY_DOCTOR",
                                )
                            )
                except Exception as ex:
                    logger.debug(f"Fallback reading sample records skipped: {ex}")

        return sorted(notes, key=lambda n: n.created_at, reverse=True)

    def get_doctors(self) -> List[Dict[str, Any]]:
        return self._doctors

    def add_doctor(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = doc_data.get("id") or f"DOC-0{len(self._doctors) + 1}"
        new_doc = {
            "id": doc_id,
            "name": doc_data["name"].strip(),
            "specialty": doc_data.get("specialty", "General Practice").strip(),
            "qualification": doc_data.get("qualification", "MD").strip(),
            "department": doc_data.get("department", "Clinical Department").strip(),
            "badge": doc_data.get("badge", "Consultant Specialist").strip(),
            "avatar": doc_data.get("avatar", "🩺"),
            "color": doc_data.get("color", "#0d9488"),
        }
        self._doctors.append(new_doc)
        # Seed schedules in Cosmos DB schedules_container for next 15 days
        standard_slots = doc_data.get("slots") or ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM", "04:30 PM"]
        today = date.today()
        for offset in range(15):
            curr_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
            slots = [TimeSlot(slot_time=s, is_booked=False) for s in standard_slots]
            sched = DoctorSchedule(
                doctor_id=doc_id,
                doctor_name=new_doc["name"],
                specialty=new_doc["specialty"],
                date=curr_date,
                slots=slots,
            )
            try:
                self.schedules_container.upsert_item(body=sched.model_dump())
            except Exception as e:
                logger.warning(f"Error persisting new doctor schedule in Cosmos DB: {e}")
        return new_doc

    def send_appointment_notification(
        self, appointment_id: str, channel: str = "SMS"
    ) -> Dict[str, Any]:
        try:
            query = "SELECT * FROM c WHERE c.id = @id"
            params = [{"name": "@id", "value": appointment_id}]
            items = list(
                self.appointments_container.query_items(
                    query=query, parameters=params, enable_cross_partition_query=True
                )
            )
            if not items:
                return {"success": False, "message": f"Appointment {appointment_id} not found."}
            appt = items[0]
            pat_id = appt.get("patient_id")
            pat_name = f"Patient {pat_id}"
            pat_phone = "+91-98765-43210"
            if pat_id:
                pat = self.get_patient_by_id(pat_id)
                if pat:
                    pat_name = f"{pat.first_name} {pat.last_name}"
                    pat_phone = pat.phone_number

            msg_body = (
                f"Dear {pat_name}, your appointment with {appt.get('doctor_name')} is confirmed for "
                f"{appt.get('appointment_date')} at {appt.get('appointment_time')} (Booking Ticket: {appt.get('id')}) at MedFront Health Clinic. "
                f"Please arrive 10 minutes prior."
            )
            logger.info(f"[{channel} NOTIFICATION SENT] To {pat_phone}: '{msg_body}'")
            record = {
                "success": True,
                "channel": channel,
                "recipient_phone": pat_phone,
                "patient_name": pat_name,
                "patient_id": pat_id,
                "doctor_name": appt.get("doctor_name"),
                "appointment_id": appt.get("id"),
                "ticket_number": appt.get("id"),
                "appointment_date": appt.get("appointment_date"),
                "appointment_time": appt.get("appointment_time"),
                "message": msg_body,
                "status": "DELIVERED",
                "timestamp": datetime.now().isoformat(),
            }
            if not hasattr(self, "_notifications"):
                self._notifications = []
            self._notifications.append(record)
            try:
                appt["notification_sent"] = True
                appt["notification_channel"] = channel
                appt["notification_recipient"] = pat_phone
                appt["notification_ticket_id"] = appt.get("id")
                self.appointments_container.upsert_item(body=appt)
            except Exception as e_upsert:
                logger.debug(f"Could not persist notification fields on Cosmos appointment: {e_upsert}")
            return record
        except Exception as e:
            logger.error(f"Error sending notification in Cosmos DB: {e}")
            return {"success": False, "message": str(e)}

    def get_recent_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not hasattr(self, "_notifications"):
            self._notifications = []
        return list(reversed(self._notifications[-limit:]))




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
