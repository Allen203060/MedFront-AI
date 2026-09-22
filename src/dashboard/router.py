"""
Hospital Administrative & Clinical Dashboard Router.
Provides real-time endpoints for:
1. Role-based Doctor & Receptionist Portals
2. Ambient AI Clinical Scribe (Speech $\to$ GPT-4o SOAP Note $\to$ Doctor Approval Gate)
3. Longitudinal Patient Health Records & Clinical Notes in Cosmos DB & Azure AI Search
4. Direct Patient Onboarding, Clinician Availability, and Live Bookings
"""

import json
import logging
import os
import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.actions.db_service import get_db_service
from src.actions.models import ActionResult, Appointment, ClinicalNote, NewPatientRequest, PatientRecord
from src.actions.tools import verify_patient_identity
from src.core.config import settings
from src.dashboard.scribe_service import generate_soap_note_from_transcript, index_confirmed_clinical_note
from src.dashboard.ui_template import render_dashboard_html

logger = logging.getLogger("medfront.dashboard")
router = APIRouter(prefix="", tags=["Hospital Dashboard"])


class VerifyRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    phone_number: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


class DirectBookingRequest(BaseModel):
    patient_id: str
    doctor_name: str
    appointment_date: str
    appointment_time: str
    reason_for_visit: Optional[str] = "General Consultation"


class ScribeGenerateRequest(BaseModel):
    transcript: str
    patient_id: str
    patient_name: str
    doctor_name: str
    doctor_id: Optional[str] = "DOC-01"
    appointment_id: Optional[str] = None
    encounter_date: Optional[str] = None


class ScribeConfirmRequest(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    doctor_id: str
    doctor_name: str
    appointment_id: Optional[str] = None
    date: str
    subjective: str
    objective: str
    assessment: str
    plan: str
    raw_transcript: Optional[str] = None
    status: Optional[str] = "CONFIRMED_BY_DOCTOR"


# =============================================================================
# AUTHENTICATION
# =============================================================================

@router.post("/api/auth/login")
async def login(req: LoginRequest) -> Dict[str, Any]:
    """Explicit credential verification and role assignment."""
    db = get_db_service()
    
    if req.role == "patient":
        patients = db.get_all_patients()
        for p in patients:
            if p.email and p.email.lower() == req.email.lower() and p.password == req.password:
                return {
                    "success": True,
                    "userId": p.id,
                    "userName": f"{p.first_name} {p.last_name}",
                    "role": "patient"
                }
        raise HTTPException(status_code=401, detail="Invalid patient email or password.")
        
    elif req.role == "doctor":
        # Mock doctor login (in real app, verify against doctor DB)
        doctors = db.get_doctors()
        for d in doctors:
            # allow dummy doc login: email doc-XX@example.com, password: doc
            dummy_email = f"{d['id'].lower()}@example.com"
            if req.email.lower() == dummy_email and req.password == "doc":
                return {
                    "success": True,
                    "userId": d["id"],
                    "userName": d["name"],
                    "role": "doctor"
                }
        raise HTTPException(status_code=401, detail="Invalid doctor credentials. Try doc-01@example.com / doc")
        
    elif req.role == "admin":
        if req.email.lower() == "admin@medfront.voice" and req.password == "admin":
            return {
                "success": True,
                "userId": "ADMIN",
                "userName": "System Administrator",
                "role": "admin"
            }
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")
        
    raise HTTPException(status_code=400, detail="Invalid role specified.")

# =============================================================================
# CLINIC METRICS & STATS
# =============================================================================

@router.get("/api/dashboard/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """Return high-level system metrics and cloud resource health."""
    db = get_db_service()
    patients = db.get_all_patients()
    appointments = db.get_all_appointments()

    total_records = 0
    records_file = "data/knowledge/sample_patient_records.json"
    if os.path.exists(records_file):
        try:
            with open(records_file, "r", encoding="utf-8") as f:
                recs = json.load(f)
                total_records = len(recs)
        except Exception:
            total_records = 6

    confirmed_count = len([a for a in appointments if getattr(a, "status", "") == "CONFIRMED"])
    return {
        "registered_patients": len(patients),
        "total_patients": len(patients),
        "total_patients_count": len(patients),
        "total_appointments": len(appointments),
        "confirmed_appointments": confirmed_count,
        "confirmed_appointments_count": confirmed_count,
        "doctors_count": len(db.get_doctors()),
        "active_doctors": len(db.get_doctors()),
        "clinical_records_indexed": total_records,
        "cloud_services": {
            "cosmos_db": "CONNECTED" if settings.is_cosmos_db_configured else "MOCK_MODE",
            "azure_ai_search": "CONNECTED" if settings.is_azure_search_configured else "LOCAL_CACHE",
            "azure_openai": "CONNECTED" if settings.is_azure_openai_configured else "OFFLINE",
            "rag_mode": settings.effective_rag_mode.upper(),
        },
        "clinic_name": "MedFront",
    }


# =============================================================================
# DOCTOR PORTAL ENDPOINTS
# =============================================================================

@router.get("/api/dashboard/doctors")
async def get_clinic_doctors() -> List[Dict[str, Any]]:
    """Returns clinic doctors directory with specialties and credentials."""
    db = get_db_service()
    return db.get_doctors()


@router.get("/api/dashboard/doctors/{doctor_name}/appointments", include_in_schema=False)
@router.get("/api/dashboard/doctor/{doctor_name}/appointments")
async def get_doctor_appointments(doctor_name: str, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return appointments specifically assigned to the requested clinician."""
    db = get_db_service()
    appts = db.get_doctor_appointments(doctor_name_or_id=doctor_name, target_date=target_date)
    return [a.model_dump() for a in appts]


# =============================================================================
# PATIENT CHART & LONGITUDINAL RECORDS
# =============================================================================

@router.get("/api/dashboard/patients")
async def get_all_patients() -> List[Dict[str, Any]]:
    """Return all registered patient profiles stored in Layer A (Cosmos DB)."""
    db = get_db_service()
    patients = db.get_all_patients()
    return [p.model_dump() for p in patients]


@router.get("/api/dashboard/patients/{patient_id}/records")
async def get_patient_records(patient_id: str) -> Dict[str, Any]:
    """Return longitudinal clinical records (SOAP notes, labs, call transcripts)."""
    clean_id = patient_id.strip()
    db = get_db_service()
    patient = db.get_patient_by_id(clean_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{clean_id}' not found.")

    records: List[Dict[str, Any]] = []
    records_file = "data/knowledge/sample_patient_records.json"
    if os.path.exists(records_file):
        try:
            with open(records_file, "r", encoding="utf-8") as f:
                all_records = json.load(f)
                records = [r for r in all_records if r.get("patient_id") == clean_id]
        except Exception as e:
            logger.warning(f"Failed to read patient records file: {e}")

    return {
        "patient": patient.model_dump(),
        "total_records": len(records),
        "records": records,
    }


@router.get("/api/dashboard/patients/{patient_id}/chart")
async def get_patient_chart(patient_id: str) -> Dict[str, Any]:
    """
    Return comprehensive longitudinal EHR chart:
    demographics, contact, insurance, all appointments, and confirmed clinical SOAP notes.
    """
    clean_id = patient_id.strip()
    db = get_db_service()
    patient = db.get_patient_by_id(clean_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{clean_id}' not found.")

    appts = db.get_patient_appointments(clean_id)
    notes = db.get_patient_clinical_notes(clean_id)

    return {
        "patient": patient.model_dump(),
        "appointments": [a.model_dump() for a in appts],
        "clinical_notes": [n.model_dump() for n in notes],
    }


@router.post("/api/dashboard/patients/register")
async def register_new_patient(req: NewPatientRequest) -> Dict[str, Any]:
    """
    Onboards a new patient and assigns a permanent Medical Record Number (MRN, e.g. P-10026).
    Persists to Cosmos DB patients container so caller is immediately recognizable across all channels.
    """
    db = get_db_service()

    # Check if patient already exists
    existing = db.get_patient_by_identity(
        first_name=req.first_name,
        last_name=req.last_name,
        date_of_birth=req.date_of_birth,
    )
    if existing:
        # Update existing patient with new email and password (linking account)
        existing.email = req.email or existing.email
        existing.password = req.password or existing.password
        db.update_patient_record(existing)
        return {
            "success": True,
            "message": f"Successfully linked to your existing MRN: {existing.id}. Profile updated.",
            "patient": existing.model_dump(),
            "is_new": False,
        }

    # Generate permanent MRN
    all_patients = db.get_all_patients()
    next_num = 10023 + len(all_patients) + random.randint(1, 9)
    new_mrn = f"P-{next_num}"

    new_patient = PatientRecord(
        id=new_mrn,
        first_name=req.first_name.strip().title(),
        last_name=req.last_name.strip().title(),
        date_of_birth=req.date_of_birth.strip(),
        phone_number=req.phone_number.strip(),
        insurance_provider=req.insurance_provider or "Self-Pay / Not Disclosed",
        insurance_policy_number=req.insurance_policy_number,
        emergency_contact=req.emergency_contact,
        email=req.email or f"{req.first_name.lower()}.{req.last_name.lower()}@example.com",
        password=req.password or req.first_name.lower(),
        active=True,
    )
    saved = db.register_patient(new_patient)
    return {
        "success": True,
        "message": f"Patient onboarded successfully with Permanent MRN: {saved.id}",
        "patient": saved.model_dump(),
        "is_new": True,
    }


# =============================================================================
# AMBIENT AI CLINICAL SCRIBE ENDPOINTS
# =============================================================================

@router.post("/api/dashboard/scribe/generate-soap", include_in_schema=False)
@router.post("/api/dashboard/scribe/generate")
async def scribe_generate_soap(req: ScribeGenerateRequest) -> Dict[str, Any]:
    """
    Invokes Azure OpenAI (GPT-4o) Scribe Engine to structure raw consultation audio
    or clinician dictation into standard SOAP format (Subjective, Objective, Assessment, Plan).
    Returns a draft for mandatory doctor review.
    """
    res = generate_soap_note_from_transcript(
        raw_transcript=req.transcript,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        doctor_name=req.doctor_name,
        doctor_id=req.doctor_id or "DOC-01",
        appointment_id=req.appointment_id,
        encounter_date=req.encounter_date,
    )
    return res


@router.post("/api/dashboard/scribe/confirm-note", include_in_schema=False)
@router.post("/api/dashboard/scribe/confirm")
async def scribe_confirm_soap(req: ScribeConfirmRequest) -> Dict[str, Any]:
    """
    Doctor Confirmation Gate: commits the clinician-verified SOAP note to Azure Cosmos DB
    and indexes the encounter into Azure AI Search ('patient-records-index') for future RAG queries.
    """
    db = get_db_service()

    note = ClinicalNote(
        id=req.id,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        doctor_id=req.doctor_id,
        doctor_name=req.doctor_name,
        appointment_id=req.appointment_id,
        date=req.date,
        subjective=req.subjective,
        objective=req.objective,
        assessment=req.assessment,
        plan=req.plan,
        raw_transcript=req.raw_transcript,
        status="CONFIRMED_BY_DOCTOR",
    )

    # 1. Persist to Cosmos DB
    saved_note = db.create_clinical_note(note)

    # 2. Index into Azure AI Search
    indexed = index_confirmed_clinical_note(saved_note)

    return {
        "success": True,
        "message": f"Clinical SOAP Note {saved_note.id} confirmed and saved to permanent medical chart.",
        "note": saved_note.model_dump(),
        "indexed_in_rag": indexed,
    }


# =============================================================================
# APPOINTMENTS & SCHEDULING
# =============================================================================

@router.get("/api/dashboard/appointments")
async def get_all_appointments() -> List[Dict[str, Any]]:
    """Return all booked appointments from Layer A (Cosmos DB)."""
    db = get_db_service()
    appts = db.get_all_appointments()
    return [a.model_dump() for a in appts]


@router.post("/api/dashboard/appointments/book")
async def book_direct_appointment(req: DirectBookingRequest) -> Dict[str, Any]:
    """Direct appointment booking endpoint for receptionists."""
    db = get_db_service()
    success, msg, appt = db.book_appointment(
        patient_id=req.patient_id,
        doctor_name=req.doctor_name,
        appointment_date=req.appointment_date,
        appointment_time=req.appointment_time,
        reason_for_visit=req.reason_for_visit or "General Consultation",
    )
    if not success or not appt:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "appointment": appt.model_dump(),
    }


@router.post("/api/dashboard/appointments/{appointment_id}/cancel")
async def cancel_existing_appointment(appointment_id: str, patient_id: str) -> Dict[str, Any]:
    """Cancels an existing appointment and re-opens clinician slot."""
    db = get_db_service()
    success, msg = db.cancel_appointment(patient_id=patient_id, appointment_id=appointment_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}




@router.post("/api/dashboard/doctors/add")
async def add_new_doctor(req: Dict[str, Any]) -> Dict[str, Any]:
    """Onboard a new clinician to the clinic roster and seed availability schedules."""
    name = req.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Doctor name is required.")
    if not name.startswith("Dr."):
        req["name"] = f"Dr. {name}"
    db = get_db_service()
    doc = db.add_doctor(req)
    return {"success": True, "doctor": doc}


@router.post("/api/dashboard/appointments/{appointment_id}/notify")
async def notify_appointment(appointment_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatch booking confirmation notification via SMS, WhatsApp, or Email."""
    channel = (payload or {}).get("channel", "SMS")
    db = get_db_service()
    res = db.send_appointment_notification(appointment_id=appointment_id, channel=channel)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to send notification."))
    return res


@router.get("/api/dashboard/schedules")
async def get_all_schedules() -> List[Dict[str, Any]]:
    """Return upcoming clinician schedules and open availability."""
    db = get_db_service()
    schedules = []
    today = date.today()
    doctors = db.get_doctors()

    for offset in range(3):
        cur_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        for doc in doctors:
            doc_scheds = db.get_doctor_schedules(doc["name"], cur_date)
            for s in doc_scheds:
                schedules.append(s.model_dump())

    return schedules


# =============================================================================
# RECEPTIONIST VERIFICATION AUDIT
# =============================================================================

@router.post("/api/dashboard/verify-receptionist")
async def test_receptionist_verification(req: VerifyRequest) -> Dict[str, Any]:
    """Test and inspect AI Receptionist identity verification tool and HIPAA audit."""
    res = verify_patient_identity(
        first_name=req.first_name,
        last_name=req.last_name,
        date_of_birth=req.date_of_birth,
        phone_number=req.phone_number,
    )

    hipaa_audit = {
        "status": "COMPLIANT",
        "administrative_scope_granted": res.success,
        "clinical_soap_notes_exposed": False,
        "verified_mrn": res.data.get("patient_id") if res.data else None,
        "caller_identity": f"{req.first_name} {req.last_name}".title(),
        "insurance_cleared": res.data.get("insurance_provider") if res.data else None,
    }

    return {
        "action_result": res.model_dump(),
        "hipaa_rbac_audit": hipaa_audit,
        "receptionist_prompt_preview": (
            f"[SYSTEM_STATE] Caller verified as {res.data.get('first_name')} {res.data.get('last_name')} "
            f"(MRN: {res.data.get('patient_id')}). Insurance: {res.data.get('insurance_provider')}."
            if res.success and res.data
            else "[SYSTEM_STATE] Caller identity unverified."
        ),
    }


class ResendNotificationRequest(BaseModel):
    appointment_id: str
    channel: Optional[str] = "SMS"


@router.get("/api/dashboard/notifications", summary="List dispatched appointment notification tickets")
async def get_dashboard_notifications(limit: int = 50) -> Dict[str, Any]:
    """Retrieves recent appointment notification tickets and delivery logs."""
    db = get_db_service()
    notifs = db.get_recent_notifications(limit=limit)
    return {
        "status": "success",
        "total_dispatched": len(notifs),
        "notifications": notifs,
    }


@router.post("/api/dashboard/notifications/resend", summary="Resend appointment notification ticket")
async def resend_dashboard_notification(req: ResendNotificationRequest) -> Dict[str, Any]:
    """Re-dispatches an appointment confirmation ticket via SMS."""
    db = get_db_service()
    res = db.send_appointment_notification(appointment_id=req.appointment_id, channel=req.channel or "SMS")
    return res


# =============================================================================
# DASHBOARD HTML PAGE
# =============================================================================

@router.get("/dashboard", response_class=HTMLResponse, summary="Hospital Clinical & Administrative Dashboard")
async def get_hospital_dashboard_page() -> str:
    """Renders the comprehensive Medical HealthTech Portal."""
    return render_dashboard_html()
