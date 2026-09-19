"""
MedFront Action Layer - Domain Data Models.
Defines Pydantic V2 data schemas for patient records, doctor availability,
appointments, and action tool execution payloads.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PatientRecord(BaseModel):
    """Structured patient demographic and profile record stored in Cosmos DB Layer A."""
    id: str = Field(..., description="Unique Patient ID / Medical Record Number (e.g., 'P-10023')")
    first_name: str = Field(..., description="Patient legal first name")
    last_name: str = Field(..., description="Patient legal last name")
    date_of_birth: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    phone_number: str = Field(..., description="Primary contact phone number in E.164 or standardized format")
    insurance_provider: Optional[str] = Field(default="Self-Pay / Not Disclosed", description="Insurance carrier")
    insurance_policy_number: Optional[str] = Field(default=None, description="Policy/Member ID")
    emergency_contact: Optional[str] = Field(default=None, description="Emergency contact name & phone")
    active: bool = Field(default=True, description="Account active status")


class TimeSlot(BaseModel):
    """An individual appointment time window."""
    slot_time: str = Field(..., description="Time string, e.g., '09:00 AM', '10:30 AM'")
    is_booked: bool = Field(default=False, description="True if already reserved by a patient")
    booked_by_patient_id: Optional[str] = Field(default=None, description="Patient ID who reserved the slot")
    appointment_id: Optional[str] = Field(default=None, description="Associated appointment ID if booked")


class DoctorSchedule(BaseModel):
    """Daily schedule and slot availability for a clinician."""
    doctor_id: str = Field(..., description="Unique Doctor ID, e.g., 'DOC-01'")
    doctor_name: str = Field(..., description="Full clinician name, e.g., 'Dr. Sarah Smith'")
    specialty: str = Field(..., description="Medical specialty, e.g., 'Cardiology', 'General Practice'")
    date: str = Field(..., description="Schedule date in YYYY-MM-DD format")
    slots: List[TimeSlot] = Field(default_factory=list, description="List of time slots for the day")


class Appointment(BaseModel):
    """Booked appointment record stored in Cosmos DB appointments container."""
    id: str = Field(..., description="Unique Appointment ID (e.g., 'APT-89210')")
    patient_id: str = Field(..., description="Patient ID (Partition Key)")
    doctor_id: str = Field(..., description="Clinician ID")
    doctor_name: str = Field(..., description="Clinician Name")
    specialty: str = Field(..., description="Clinic Specialty")
    appointment_date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_time: str = Field(..., description="Time in e.g., '10:00 AM' format")
    reason_for_visit: str = Field(default="General Consultation", description="Reason provided by caller")
    status: str = Field(default="CONFIRMED", description="Status: 'CONFIRMED', 'CANCELLED', 'COMPLETED'")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when appointment was booked"
    )
    notification_sent: bool = Field(default=False, description="Whether confirmation notification was dispatched")
    notification_channel: str = Field(default="SMS", description="Notification channel (SMS/WhatsApp)")
    notification_recipient: Optional[str] = Field(default=None, description="Recipient phone number")
    notification_ticket_id: Optional[str] = Field(default=None, description="Dispatched ticket reference")


class ActionResult(BaseModel):
    """Standardized result envelope returned by all action tools to the LLM orchestrator."""
    success: bool = Field(..., description="True if the action succeeded, False if validation/DB failed")
    message: str = Field(..., description="Human/LLM-friendly summary of the action outcome")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured payload or returned entity")
    error_code: Optional[str] = Field(default=None, description="Error classification if failed")


class ClinicalNote(BaseModel):
    """Structured clinical SOAP note created by clinician or ambient AI scribe."""
    id: str = Field(..., description="Unique Note ID (e.g., 'NOTE-10023-1')")
    patient_id: str = Field(..., description="Patient ID / MRN")
    patient_name: str = Field(..., description="Full patient legal name")
    doctor_id: str = Field(..., description="Clinician ID")
    doctor_name: str = Field(..., description="Full doctor name")
    appointment_id: Optional[str] = Field(default=None, description="Associated appointment ID if applicable")
    date: str = Field(..., description="Clinical encounter date in YYYY-MM-DD")
    subjective: str = Field(..., description="Chief complaint, history of presenting illness, patient symptoms")
    objective: str = Field(..., description="Vitals, observations, physical examination notes")
    assessment: str = Field(..., description="Primary clinical impression or diagnosis")
    plan: str = Field(..., description="Prescriptions, diagnostics, lifestyle guidance, follow-up timeline")
    raw_transcript: Optional[str] = Field(default=None, description="Raw transcription from consultation")
    status: str = Field(default="CONFIRMED_BY_DOCTOR", description="Status: 'DRAFT', 'CONFIRMED_BY_DOCTOR'")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp note was recorded"
    )


class NewPatientRequest(BaseModel):
    """Request payload for receptionist patient onboarding."""
    first_name: str
    last_name: str
    date_of_birth: str
    phone_number: str
    insurance_provider: Optional[str] = "Self-Pay / Not Disclosed"
    insurance_policy_number: Optional[str] = None
    emergency_contact: Optional[str] = None

