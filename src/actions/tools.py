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
from src.actions.models import ActionResult, PatientRecord

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


def extract_phone_number(text: str) -> Optional[str]:
    """
    Extracts a 10-digit standardized phone number (+91-XXXXX-XXXXX) from natural spoken or written text.
    Handles numeric formats ('9876543210', '+91 98765 43210') and spoken number words.
    """
    if not text:
        return None

    word_to_digit = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "oh": "0", "ek": "1", "do": "2", "teen": "3", "char": "4", "paanch": "5",
        "panch": "5", "chhe": "6", "che": "6", "saat": "7", "aath": "8",
        "nau": "9", "shunya": "0",
        "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
        "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"
    }
    tokens = text.lower().replace("-", " ").replace(".", " ").replace(",", " ").split()
    normalized_tokens = [word_to_digit.get(t, t) for t in tokens]
    normalized_text = " ".join(normalized_tokens)

    # 1. Regex search for 10-digit number with optional +91 prefix
    matches = re.findall(r"(?:\+?91[\s-]?)?([6-9]\d{9})", normalized_text)
    if matches:
        raw_num = matches[0]
        return f"+91-{raw_num[:5]}-{raw_num[5:]}"

    # 2. General 10-digit sequence
    gen_matches = re.findall(r"\b(\d{10})\b", re.sub(r"[^\d]", " ", normalized_text))
    if gen_matches:
        raw_num = gen_matches[0]
        return f"+91-{raw_num[:5]}-{raw_num[5:]}"

    # 3. Continuous digits string has at least 7 digits (relaxed for testing)
    pure_digits = re.sub(r"\D", "", normalized_text)
    if len(pure_digits) >= 7:
        raw_num = pure_digits[-10:] if len(pure_digits) >= 10 else pure_digits.zfill(10)
        return f"+91-{raw_num[:5]}-{raw_num[5:]}"

    return None


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

    # Orthopedics synonyms (English & Hindi)
    "ortho": "Orthopedics",
    "orthopedics": "Orthopedics",
    "orthopaedics": "Orthopedics",
    "orthopedic": "Orthopedics",
    "orthopaedic": "Orthopedics",
    "bone": "Orthopedics",
    "bones": "Orthopedics",
    "joint": "Orthopedics",
    "joints": "Orthopedics",
    "bone specialist": "Orthopedics",
    "joint specialist": "Orthopedics",
    "orthopedic surgeon": "Orthopedics",
    "knee": "Orthopedics",
    "spine": "Orthopedics",
    "ऑर्थोपेडिक्स": "Orthopedics",
    "ऑर्थोपेडिक": "Orthopedics",
    "ऑर्थो": "Orthopedics",
    "हड्डी": "Orthopedics",
    "हड्डियों": "Orthopedics",
    "हड्डी रोग": "Orthopedics",
    "घुटना": "Orthopedics",
    "घुटने": "Orthopedics",
    "घुटने का दर्द": "Orthopedics",
    "घुटने के दर्द": "Orthopedics",
    "जोड़": "Orthopedics",
    "जोड़ों": "Orthopedics",
    "जोड़ों का दर्द": "Orthopedics",
    "जोड़ों के दर्द": "Orthopedics",
    "कमर": "Orthopedics",
    "कमर दर्द": "Orthopedics",
    "रीढ़": "Orthopedics",

    # Pediatrics synonyms (English & Hindi)
    "pediatrics": "Pediatrics",
    "paediatrics": "Pediatrics",
    "pediatric": "Pediatrics",
    "paediatric": "Pediatrics",
    "pediatrician": "Pediatrics",
    "paediatrician": "Pediatrics",
    "child": "Pediatrics",
    "children": "Pediatrics",
    "child specialist": "Pediatrics",
    "baby": "Pediatrics",
    "kids": "Pediatrics",
    "kid": "Pediatrics",
    "पीडियाट्रिक्स": "Pediatrics",
    "पीडियाट्रिशियन": "Pediatrics",
    "बच्चा": "Pediatrics",
    "बच्चों": "Pediatrics",
    "शिशु": "Pediatrics",
    "बाल रोग": "Pediatrics",

    # Cardiology synonyms (Hindi additions)
    "कार्डियोलॉजी": "Cardiology",
    "कार्डियो": "Cardiology",
    "कार्डियोलॉजिस्ट": "Cardiology",
    "दिल": "Cardiology",
    "हार्ट": "Cardiology",

    # Dermatology synonyms (Hindi additions)
    "डर्मेटोलॉजी": "Dermatology",
    "डर्मेटोलॉजिस्ट": "Dermatology",
    "डर्मा": "Dermatology",
    "त्वचा": "Dermatology",
    "चर्म": "Dermatology",
    "चर्म रोग": "Dermatology",

    # General Practice synonyms (Hindi additions)
    "सामान्य": "General Practice",
    "फिजिशियन": "General Practice",
    "बुखार": "General Practice",
    "सर्दी": "General Practice",
    "खांसी": "General Practice",
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

    "vikram": "Dr. Vikram Sen",
    "dr. vikram": "Dr. Vikram Sen",
    "dr vikram": "Dr. Vikram Sen",
    "sen": "Dr. Vikram Sen",
    "dr. sen": "Dr. Vikram Sen",
    "dr. vikram sen": "Dr. Vikram Sen",
    "vikram sen": "Dr. Vikram Sen",

    "meera": "Dr. Meera Nambiar",
    "dr. meera": "Dr. Meera Nambiar",
    "dr meera": "Dr. Meera Nambiar",
    "nambiar": "Dr. Meera Nambiar",
    "dr. nambiar": "Dr. Meera Nambiar",
    "dr. meera nambiar": "Dr. Meera Nambiar",
    "meera nambiar": "Dr. Meera Nambiar",
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

    # Common relative keywords (English & Hindi)
    if s in ["today", "this day", "आज", "aaj"]:
        return today.strftime("%Y-%m-%d")
    if s in ["tomorrow", "tmrw", "next day", "कल", "kal", "अगले दिन"]:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if s in ["day after tomorrow", "overmorrow", "परसों", "parso", "parson"]:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    if any(k in s for k in ["कोई और दिन", "अगला", "next", "free", "उपलब्ध", "next_available", "earliest", "any day", "kab free", "कब फ्री"]):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

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
            message=f"No active patient record found for {first_name} {last_name} with date of birth {clean_dob}. As a first-time visitor, you can be registered as a new patient to complete your booking.",
            error_code="PATIENT_NOT_FOUND",
            data={"is_new_patient": True, "full_name": f"{first_name} {last_name}"}
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

    # If no schedule found on target date, proactively scan forward across the next 7 days
    if not schedules:
        from datetime import datetime, timedelta
        try:
            base_dt = datetime.strptime(iso_date, "%Y-%m-%d").date()
        except Exception:
            base_dt = date.today()

        for offset in range(1, 8):
            future_date = (base_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
            f_scheds = db.get_doctor_schedules(doctor_name_or_specialty=canonical_query, target_date=future_date)
            if not f_scheds and canonical_query != raw_doc:
                f_scheds = db.get_doctor_schedules(doctor_name_or_specialty=raw_doc, target_date=future_date)
            if f_scheds:
                schedules = f_scheds
                iso_date = future_date
                break

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

    # If all slots are full on the target date, proactively find the earliest next available opening!
    if total_open_slots == 0:
        from datetime import datetime, timedelta
        try:
            base_dt = datetime.strptime(iso_date, "%Y-%m-%d").date()
        except Exception:
            base_dt = date.today()

        next_available_results = []
        next_open_slots = []
        next_date_str = None
        next_doc_name = canonical_query
        next_specialty = "Specialist"

        for offset in range(1, 8):
            future_date = (base_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
            f_scheds = db.get_doctor_schedules(doctor_name_or_specialty=canonical_query, target_date=future_date)
            if not f_scheds and canonical_query != raw_doc:
                f_scheds = db.get_doctor_schedules(doctor_name_or_specialty=raw_doc, target_date=future_date)
            
            for fs in f_scheds:
                avail = [s.slot_time for s in fs.slots if not s.is_booked]
                if avail:
                    next_date_str = future_date
                    next_open_slots = avail
                    next_doc_name = fs.doctor_name
                    next_specialty = fs.specialty
                    next_available_results.append({
                        "doctor_id": fs.doctor_id,
                        "doctor_name": fs.doctor_name,
                        "specialty": fs.specialty,
                        "date": future_date,
                        "available_slots": avail,
                    })
                    break
            if next_open_slots:
                break

        if next_open_slots:
            preview = ", ".join(next_open_slots[:4])
            return ActionResult(
                success=True,
                message=(
                    f"Slots on {iso_date} are currently full for {canonical_query}, but the next available opening "
                    f"with {next_doc_name} ({next_specialty}) is on {next_date_str}: {preview}. "
                    f"Which time would you like to book?"
                ),
                data={
                    "schedules": next_available_results,
                    "total_open_slots": len(next_open_slots),
                    "suggested_date": next_date_str,
                    "suggested_doctor": next_doc_name,
                },
            )

        return ActionResult(
            success=True,
            message=f"No open slots remaining for {canonical_query} on {iso_date}. Would you like to check our General Practice doctors?",
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
    phone_number: Optional[str] = None,
    **kwargs: Any,
) -> ActionResult:
    """
    Atomically books an appointment slot for a verified patient or registers a new first-time patient.
    Requires contact phone number for new patient registration and dispatches an appointment confirmation ticket.
    """
    raw_doc = doctor_name or kwargs.get("doctor") or kwargs.get("doctor_name_or_specialty")
    raw_date = appointment_date or kwargs.get("date") or kwargs.get("target_date")
    appointment_time = appointment_time or kwargs.get("time") or kwargs.get("slot_time")
    reason_for_visit = reason_for_visit or kwargs.get("reason") or "General Consultation"
    patient_id = patient_id or kwargs.get("patient_mrn")

    doctor_name = _canonicalize_doctor_or_specialty(raw_doc)
    appointment_date = _normalize_target_date(raw_date)

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

    db_inst = get_db_service()
    
    # Pre-validate doctor schedule before registering a new patient
    schedules = db_inst.get_doctor_schedules(doctor_name, appointment_date)
    if not schedules:
        return ActionResult(
            success=False,
            message=f"I'm sorry, we do not have a doctor matching '{doctor_name}' available on {appointment_date}. Please choose one of our available specialists.",
            error_code="INVALID_DOCTOR",
        )

    is_new_patient = False

    if not patient_id:
        # 1. Check if caller provided full_name / first_name / dob
        fn = kwargs.get("full_name") or kwargs.get("name") or kwargs.get("patient_name")
        first_n = kwargs.get("first_name")
        last_n = kwargs.get("last_name")
        dob = kwargs.get("dob") or kwargs.get("date_of_birth")

        if (fn or (first_n and last_n)) and dob:
            v_res = verify_patient_identity(first_name=first_n, last_name=last_n, full_name=fn, date_of_birth=dob, dob=dob)
            if v_res.success and v_res.data:
                patient_id = v_res.data.get("patient_id")

        # 2. Check if name matches any existing registered patient
        if not patient_id and (fn or first_n):
            name_to_search = (fn or f"{first_n} {last_n or ''}").strip().lower()
            all_patients = db_inst.get_all_patients()
            for p in all_patients:
                if f"{p.first_name} {p.last_name}".lower() == name_to_search or p.first_name.lower() == name_to_search:
                    patient_id = p.id
                    break

        # 3. New Patient / First-Time Visitor Onboarding
        if not patient_id and (fn or first_n):
            raw_phone = phone_number or kwargs.get("phone_number") or kwargs.get("phone") or kwargs.get("contact")
            contact_phone = extract_phone_number(str(raw_phone)) if raw_phone else None

            # If no phone number OR no DOB provided for new patient, ask for it!
            if not contact_phone or not dob:
                full_name_clean = (fn or f"{first_n} {last_n or ''}").strip().title()
                return ActionResult(
                    success=False,
                    message=f"Thank you, {full_name_clean}! To complete your registration as a new patient and send your appointment confirmation ticket, may I please have your Date of Birth and your contact phone number?",
                    error_code="MISSING_REGISTRATION_DETAILS",
                    data={"requires_phone": True, "requires_dob": True, "full_name": full_name_clean},
                )

            import random
            full_str = (fn or f"{first_n} {last_n or ''}").strip()
            parts = full_str.split(maxsplit=1)
            f_name = parts[0].capitalize()
            l_name = parts[1].capitalize() if len(parts) > 1 else "Patient"

            new_mrn = f"P-{random.randint(20000, 99999)}"
            new_patient = PatientRecord(
                id=new_mrn,
                first_name=f_name,
                last_name=l_name,
                date_of_birth=dob or "1995-01-01",
                phone_number=contact_phone,
                insurance_provider=kwargs.get("insurance_provider") or "Direct Registration",
                insurance_policy_number=kwargs.get("policy_number") or f"POL-{new_mrn}",
                email=f"{f_name.lower()}.{l_name.lower()}@medfront.voice",
                password=f_name.lower(),
                active=True,
                emergency_contact="Family / Self",
            )
            db_inst.register_patient(new_patient)
            patient_id = new_mrn
            is_new_patient = True
            logger.info(f"Automatically registered first-time patient '{f_name} {l_name}' (Phone: {contact_phone}) with new MRN {new_mrn}")

        if not patient_id:
            return ActionResult(
                success=False,
                message="To complete your booking, please provide your full name. If you are visiting for the first time, we will gladly register you.",
                error_code="PATIENT_UNVERIFIED",
            )

    if not doctor_name or not appointment_date or not appointment_time:
        pass # This was checked at the top of the function

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

    # Dispatch official appointment confirmation notification ticket (SMS)
    notif_res = db.send_appointment_notification(appointment_id=appt.id, channel="SMS")
    recipient_num = notif_res.get("recipient_phone") or kwargs.get("phone_number") or "your phone number"

    welcome_msg = (
        f"Welcome to MedFront! You have been registered as a new patient. Please note down your Medical Record Number: {patient_id}. "
        f"We highly advise you to register on our online portal after this call using your name and date of birth to complete your profile. "
    ) if is_new_patient else ""
    return ActionResult(
        success=True,
        message=(
            f"{welcome_msg}Appointment confirmed with {appt.doctor_name} on {appt.appointment_date} "
            f"at {appt.appointment_time}. Confirmation Ticket ID: {appt.id}. "
            f"A confirmation notification ticket has been sent to your phone number {recipient_num}."
        ),
        data={**appt.model_dump(), "notification": notif_res},
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


def update_patient_details(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    phone_number: str,
    patient_id: Optional[str] = None,
    address: Optional[str] = None,
    insurance_provider: Optional[str] = None,
    emergency_contact: Optional[str] = None,
    **kwargs: Any,
) -> ActionResult:
    db = get_db_service()
    patient = None
    if patient_id:
        patient = db.get_patient_by_id(patient_id)
    
    if not patient:
        patient = db.get_patient_by_identity(first_name, last_name, _normalize_dob(date_of_birth))
        
    if patient:
        patient.first_name = first_name
        patient.last_name = last_name
        patient.date_of_birth = _normalize_dob(date_of_birth)
        patient.phone_number = extract_phone_number(phone_number) or phone_number
        if address:
            patient.address = address
        if insurance_provider:
            patient.insurance_provider = insurance_provider
        if emergency_contact:
            patient.emergency_contact = emergency_contact
        db.update_patient_record(patient)
        return ActionResult(
            success=True,
            message=f"Updated details for patient {patient.first_name} {patient.last_name}.",
            data=patient.model_dump()
        )
    else:
        # Create new patient
        import uuid
        new_mrn = f"P-{uuid.uuid4().hex[:5].upper()}"
        new_patient = PatientRecord(
            id=new_mrn,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=_normalize_dob(date_of_birth),
            phone_number=extract_phone_number(phone_number) or phone_number,
            address=address,
            insurance_provider=insurance_provider or "Self-Pay",
            emergency_contact=emergency_contact,
            active=True,
        )
        db.register_patient(new_patient)
        return ActionResult(
            success=True,
            message=f"Registered new patient {first_name} {last_name}.",
            data=new_patient.model_dump()
        )


def get_patient_test_reports(patient_id: str) -> ActionResult:
    db = get_db_service()
    reports = db.get_patient_test_reports(patient_id)
    return ActionResult(
        success=True,
        message=f"Found {len(reports)} test reports for patient {patient_id}.",
        data={"test_reports": [r.model_dump() for r in reports]}
    )


def get_patient_visit_summaries(patient_id: str) -> ActionResult:
    db = get_db_service()
    summaries = db.get_patient_visit_summaries(patient_id)
    return ActionResult(
        success=True,
        message=f"Found {len(summaries)} visit summaries for patient {patient_id}.",
        data={"visit_summaries": [s.model_dump() for s in summaries]}
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
    "update_patient_details": update_patient_details,
    "get_patient_test_reports": get_patient_test_reports,
    "get_patient_visit_summaries": get_patient_visit_summaries,
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
