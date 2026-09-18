"""
MedFront Action Layer - Healthcare Action Tools & Dispatcher.
Implements the business logic functions called by the AI Receptionist (GPT-4o)
and provides a universal dispatcher with strict error handling and audit logging.
"""

import json
import logging
import re
from datetime import date as date_module
from typing import Any, Dict, Optional

from src.actions.db_service import get_db_service
from src.actions.models import ActionResult

logger = logging.getLogger("MedFront.Actions.Tools")


def _normalize_dob(dob_str: str) -> str:
    """Normalizes natural spoken or written date strings into ISO YYYY-MM-DD."""
    clean = dob_str.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
        return clean

    clean_ord = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", clean, flags=re.IGNORECASE)
    clean_ord = clean_ord.replace(",", " ").replace("-", " ").replace("/", " ")
    parts = clean_ord.split()

    month_names = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "june": 6, "jun": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12
    }

    if len(parts) == 3:
        p0, p1, p2 = parts[0].lower(), parts[1].lower(), parts[2].lower()
        if p0.isdigit() and p1 in month_names and p2.isdigit():
            return f"{int(p2):04d}-{month_names[p1]:02d}-{int(p0):02d}"
        if p0 in month_names and p1.isdigit() and p2.isdigit():
            return f"{int(p2):04d}-{month_names[p0]:02d}-{int(p1):02d}"
        if p0.isdigit() and len(p0) == 4 and p1 in month_names and p2.isdigit():
            return f"{int(p0):04d}-{month_names[p1]:02d}-{int(p2):02d}"
        if p0.isdigit() and p1.isdigit() and p2.isdigit() and len(p2) == 4:
            v0, v1 = int(p0), int(p1)
            if v1 > 12 >= v0:
                return f"{int(p2):04d}-{v0:02d}-{v1:02d}"
            return f"{int(p2):04d}-{v1:02d}-{v0:02d}"

    return dob_str


SPECIALTY_SYNONYMS = {
    # Cardiology synonyms and common mis-transcriptions
    "cardio": "Cardiology",
    "cardio department": "Cardiology",
    "cardiology department": "Cardiology",
    "cardiologist": "Cardiology",
    "heart": "Cardiology",
    "cardiac": "Cardiology",
    "rd cardo": "Cardiology",
    "rd cardo department": "Cardiology",
    "rd cardio": "Cardiology",
    "cardo": "Cardiology",
    "rdo": "Cardiology",
    "rdo department": "Cardiology",
    "rdo dept": "Cardiology",
    "rd o": "Cardiology",
    "heart department": "Cardiology",
    
    # General Medicine synonyms
    "general": "General Practice",
    "general physician": "General Practice",
    "general medicine": "General Practice",
    "gp": "General Practice",
    "physician": "General Practice",
    "internal medicine": "General Practice",
    "routine": "General Practice",
    "regular": "General Practice",
    
    # Dermatology synonyms
    "derma": "Dermatology",
    "dermatologist": "Dermatology",
    "skin": "Dermatology",
    "skin department": "Dermatology",
    "skin clinic": "Dermatology",
    "skin specialist": "Dermatology",
}

DOCTOR_ALIASES = {
    "ananya": "Dr. Ananya Rao",
    "dr. ananya": "Dr. Ananya Rao",
    "dr ananya": "Dr. Ananya Rao",
    "rao": "Dr. Ananya Rao",
    "dr. rao": "Dr. Ananya Rao",
    "dr. ananya rao": "Dr. Ananya Rao",
    "ananya rao": "Dr. Ananya Rao",
    
    "rajesh": "Dr. Rajesh Iyer",
    "dr. rajesh": "Dr. Rajesh Iyer",
    "dr rajesh": "Dr. Rajesh Iyer",
    "iyer": "Dr. Rajesh Iyer",
    "dr. iyer": "Dr. Rajesh Iyer",
    "dr. rajesh iyer": "Dr. Rajesh Iyer",
    "rajesh iyer": "Dr. Rajesh Iyer",
    
    "sunita": "Dr. Sunita Kapoor",
    "dr. sunita": "Dr. Sunita Kapoor",
    "dr sunita": "Dr. Sunita Kapoor",
    "kapoor": "Dr. Sunita Kapoor",
    "dr. kapoor": "Dr. Sunita Kapoor",
    "dr. sunita kapoor": "Dr. Sunita Kapoor",
    "sunita kapoor": "Dr. Sunita Kapoor",
}


def _canonicalize_doctor_or_specialty(query: Optional[str]) -> str:
    """
    Normalizes spoken doctor names, specialties, and acoustic mis-transcriptions
    into standard database clinician identities or specialties.
    """
    if not query:
        return "Cardiology"

    q_lower = query.strip().lower()

    # 1. Exact lookup in doctor aliases
    if q_lower in DOCTOR_ALIASES:
        return DOCTOR_ALIASES[q_lower]

    # 2. Check specialty synonyms
    if q_lower in SPECIALTY_SYNONYMS:
        return SPECIALTY_SYNONYMS[q_lower]

    # 3. Strip fluff words like 'department', 'dept', 'clinic'
    cleaned = re.sub(r"\b(department|dept|clinic|center|ward)\b", "", q_lower, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)

    if cleaned in SPECIALTY_SYNONYMS:
        return SPECIALTY_SYNONYMS[cleaned]

    if cleaned in DOCTOR_ALIASES:
        return DOCTOR_ALIASES[cleaned]

    # 4. Fuzzy fallback using difflib for phonetic / STT mis-hearings
    import difflib
    all_keys = list(SPECIALTY_SYNONYMS.keys()) + list(DOCTOR_ALIASES.keys())
    matches = difflib.get_close_matches(cleaned, all_keys, n=1, cutoff=0.5)
    if matches:
        matched_key = matches[0]
        if matched_key in SPECIALTY_SYNONYMS:
            return SPECIALTY_SYNONYMS[matched_key]
        if matched_key in DOCTOR_ALIASES:
            return DOCTOR_ALIASES[matched_key]

    return query.strip()


def _normalize_target_date(d_str: Optional[str]) -> str:
    """
    Normalizes natural relative date terms ('tomorrow', 'today', 'next monday')
    or spoken dates into ISO YYYY-MM-DD format.
    """
    from datetime import date, datetime, timedelta

    today = date.today()
    if not d_str:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    s = d_str.strip().lower()

    # Common relative keywords
    if s in ["today", "this day"]:
        return today.strftime("%Y-%m-%d")
    if s in ["tomorrow", "tmrw", "next day"]:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if s in ["day after tomorrow", "overmorrow"]:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")

    # Named weekdays (e.g. 'monday', 'next monday')
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    for wname, wday in weekdays.items():
        if wname in s:
            days_ahead = wday - today.weekday()
            if days_ahead <= 0 or "next" in s:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # Standard ISO format check
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    # Natural spoken formats
    for fmt in [
        "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y",
        "%B %d, %Y", "%b %d, %Y"
    ]:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return (today + timedelta(days=1)).strftime("%Y-%m-%d")


def verify_patient_identity(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
    full_name: Optional[str] = None,
    dob: Optional[str] = None,
    **kwargs: Any,
) -> ActionResult:
    """
    Verifies caller identity deterministically using exact match on (first_name, last_name, DOB).
    Normalizes parameter variations from Brain tool calls (e.g. full_name or dob).
    """
    if full_name and not (first_name and last_name):
        parts = full_name.strip().split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    first_name = first_name or kwargs.get("patient_first_name")
    last_name = last_name or kwargs.get("patient_last_name")
    raw_dob = date_of_birth or dob or kwargs.get("birth_date")

    if not first_name or not last_name or not raw_dob:
        return ActionResult(
            success=False,
            message="Both full patient name and date of birth are required for identity verification.",
            error_code="PARAMETER_MISMATCH",
        )

    clean_dob = _normalize_dob(raw_dob)

    db = get_db_service()
    logger.info(f"Authenticating patient: '{first_name} {last_name}', DOB: '{clean_dob}'")

    patient = db.get_patient_by_identity(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=clean_dob,
    )

    if not patient:
        return ActionResult(
            success=False,
            message=f"No active patient record found for {first_name} {last_name} with date of birth {clean_dob}.",
            error_code="PATIENT_NOT_FOUND",
        )

    return ActionResult(
        success=True,
        message=f"Patient identity verified: {patient.first_name} {patient.last_name} (MRN: {patient.id}).",
        data={
            "patient_id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "full_name": f"{patient.first_name} {patient.last_name}",
            "insurance_provider": patient.insurance_provider,
            "policy_number": patient.insurance_policy_number,
        },
    )


def check_schedule_availability(
    doctor_name_or_specialty: Optional[str] = None,
    target_date: Optional[str] = None,
    **kwargs: Any,
) -> ActionResult:
    """
    Queries clinic schedules to retrieve open time slots for a doctor or specialty on a given date.
    Normalizes relative dates ('tomorrow') and handles phonetic/specialty synonyms.
    """
    raw_doc = (
        doctor_name_or_specialty
        or kwargs.get("doctor")
        or kwargs.get("doctor_name")
        or kwargs.get("specialty")
        or "Cardiology"
    )
    raw_date = target_date or kwargs.get("date") or kwargs.get("appointment_date")

    # Canonicalize clinician/specialty & normalize date
    canonical_query = _canonicalize_doctor_or_specialty(raw_doc)
    iso_date = _normalize_target_date(raw_date)

    db = get_db_service()
    logger.info(f"Checking schedule availability for query='{raw_doc}' (canonical='{canonical_query}') on {iso_date}")

    schedules = db.get_doctor_schedules(
        doctor_name_or_specialty=canonical_query, target_date=iso_date
    )

    # Fallback: if no schedule found, attempt search with raw query or check all doctors on that date
    if not schedules and canonical_query != raw_doc:
        schedules = db.get_doctor_schedules(
            doctor_name_or_specialty=raw_doc, target_date=iso_date
        )

    if not schedules:
        return ActionResult(
            success=False,
            message=f"No clinician schedule found matching '{canonical_query}' on {iso_date}.",
            data={"available_slots": []},
            error_code="NO_SCHEDULE_FOUND",
        )

    results = []
    total_open_slots = 0
    slot_summary = []

    for sched in schedules:
        open_slots = [s.slot_time for s in sched.slots if not s.is_booked]
        total_open_slots += len(open_slots)
        results.append({
            "doctor_id": sched.doctor_id,
            "doctor_name": sched.doctor_name,
            "specialty": sched.specialty,
            "date": sched.date,
            "available_slots": open_slots,
        })
        if open_slots:
            slot_summary.append(f"{sched.doctor_name} ({sched.specialty}): {', '.join(open_slots[:4])}")

    if total_open_slots == 0:
        return ActionResult(
            success=True,
            message=f"No open slots remaining for {canonical_query} on {iso_date}.",
            data={"schedules": results, "available_slots": []},
        )

    slots_text = "; ".join(slot_summary)
    return ActionResult(
        success=True,
        message=f"Found {total_open_slots} available slots on {iso_date}: {slots_text}.",
        data={"schedules": results, "total_open_slots": total_open_slots},
    )


def book_appointment(
    patient_id: Optional[str] = None,
    doctor_name: Optional[str] = None,
    appointment_date: Optional[str] = None,
    appointment_time: Optional[str] = None,
    reason_for_visit: str = "General Consultation",
    **kwargs: Any,
) -> ActionResult:
    """
    Atomically books an appointment slot for a verified patient with the requested clinician.
    """
    raw_doc = doctor_name or kwargs.get("doctor") or kwargs.get("doctor_name_or_specialty")
    raw_date = appointment_date or kwargs.get("date") or kwargs.get("target_date")
    appointment_time = appointment_time or kwargs.get("time") or kwargs.get("slot_time")
    reason_for_visit = reason_for_visit or kwargs.get("reason") or "General Consultation"
    patient_id = patient_id or kwargs.get("patient_mrn")

    doctor_name = _canonicalize_doctor_or_specialty(raw_doc)
    appointment_date = _normalize_target_date(raw_date)

    if not patient_id:
        return ActionResult(
            success=False,
            message="Patient identity must be verified before an appointment can be confirmed. Please collect the patient's full name and date of birth first.",
            error_code="PATIENT_UNVERIFIED",
        )

    if not doctor_name or not appointment_date or not appointment_time:
        missing = []
        if not doctor_name:
            missing.append("doctor name")
        if not appointment_date:
            missing.append("date")
        if not appointment_time:
            missing.append("time slot")
        return ActionResult(
            success=False,
            message=f"Missing required booking details: please specify {', '.join(missing)}.",
            error_code="INCOMPLETE_PARAMETERS",
        )

    db = get_db_service()
    logger.info(
        f"Booking appointment for patient {patient_id} with {doctor_name} at {appointment_date} {appointment_time}"
    )

    success, msg, appt = db.book_appointment(
        patient_id=patient_id,
        doctor_name=doctor_name,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason_for_visit=reason_for_visit,
    )

    if not success or not appt:
        return ActionResult(
            success=False,
            message=msg,
            error_code="BOOKING_FAILED",
        )

    return ActionResult(
        success=True,
        message=(
            f"Appointment confirmed with {appt.doctor_name} on {appt.appointment_date} "
            f"at {appt.appointment_time}. Confirmation ID: {appt.id}"
        ),
        data=appt.model_dump(),
    )


def cancel_appointment(patient_id: str, appointment_id: str) -> ActionResult:
    """
    Cancels an existing appointment and reopens the clinician's slot.
    """
    db = get_db_service()
    logger.info(f"Cancelling appointment {appointment_id} for patient {patient_id}")

    success, msg = db.cancel_appointment(
        patient_id=patient_id, appointment_id=appointment_id
    )

    return ActionResult(
        success=success,
        message=msg,
        error_code=None if success else "CANCELLATION_FAILED",
    )


def get_patient_appointments(patient_id: str) -> ActionResult:
    """
    Lists all active scheduled appointments for a patient.
    """
    db = get_db_service()
    logger.info(f"Retrieving active appointments for patient {patient_id}")

    appts = db.get_patient_appointments(patient_id=patient_id)

    return ActionResult(
        success=True,
        message=f"Found {len(appts)} scheduled appointment(s) for patient {patient_id}.",
        data={"appointments": [a.model_dump() for a in appts]},
    )


# Universal Dispatcher mapping tool names to callable Python functions
TOOL_REGISTRY = {
    "verify_patient_identity": verify_patient_identity,
    "check_schedule_availability": check_schedule_availability,
    "check_availability": lambda doctor=None, date=None, doctor_name_or_specialty=None, target_date=None, **kw: (
        check_schedule_availability(
            doctor_name_or_specialty=doctor_name_or_specialty or doctor or "Cardiology",
            target_date=target_date or date or str(date_module.today()),
        )
    ),
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "get_patient_appointments": get_patient_appointments,
}


def execute_tool(tool_name: str, arguments: Any) -> Dict[str, Any]:
    """
    Universal dispatcher called by the conversation engine when Azure OpenAI emits a tool call.
    Parses JSON strings or dicts, runs the matching tool, and returns a serializable dict result.
    """
    logger.info(f"Executing tool '{tool_name}' with raw arguments: {arguments}")

    if tool_name not in TOOL_REGISTRY:
        logger.error(f"Tool '{tool_name}' is not registered in TOOL_REGISTRY.")
        return ActionResult(
            success=False,
            message=f"Unknown tool: '{tool_name}'.",
            error_code="TOOL_NOT_FOUND",
        ).model_dump()

    # Parse arguments if passed as JSON string
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Invalid JSON arguments: {str(e)}",
                error_code="INVALID_ARGUMENTS",
            ).model_dump()

    tool_func = TOOL_REGISTRY[tool_name]
    try:
        result: ActionResult = tool_func(**arguments)
        return result.model_dump()
    except TypeError as te:
        logger.error(f"Argument mismatch for '{tool_name}': {te}")
        return ActionResult(
            success=False,
            message=f"Missing or invalid parameters for tool '{tool_name}': {str(te)}",
            error_code="PARAMETER_MISMATCH",
        ).model_dump()
    except Exception as e:
        logger.exception(f"Unhandled exception executing tool '{tool_name}': {e}")
        return ActionResult(
            success=False,
            message=f"Internal tool execution error: {str(e)}",
            error_code="EXECUTION_ERROR",
        ).model_dump()
