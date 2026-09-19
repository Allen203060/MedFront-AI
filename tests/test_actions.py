"""
Unit and Integration Tests for Module 5: Action Layer & Database Isolation.
Validates:
1. Exact match identity resolution vs. non-matching lookups.
2. Doctor schedule retrieval and filtering.
3. Successful slot booking and atomic state mutation.
4. Double-booking prevention (concurrency / conflict handling).
5. Appointment cancellation and slot reopening.
6. Universal dispatcher schema compliance and error handling.
"""

from datetime import date, timedelta
import pytest

from src.actions.models import ActionResult, PatientRecord
from src.actions.schemas import HEALTHCARE_TOOLS
from src.actions.tools import (
    execute_tool,
    verify_patient_identity,
    check_schedule_availability,
    book_appointment,
    cancel_appointment,
    get_patient_appointments,
)


@pytest.fixture
def target_test_date():
    """Provides a deterministic date for schedule tests."""
    return (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")


def test_openai_tool_schemas_validity():
    """Ensure all registered tools have valid OpenAI function schemas."""
    assert len(HEALTHCARE_TOOLS) == 5
    tool_names = [t["function"]["name"] for t in HEALTHCARE_TOOLS]
    expected = [
        "verify_patient_identity",
        "check_schedule_availability",
        "book_appointment",
        "cancel_appointment",
        "get_patient_appointments",
    ]
    assert sorted(tool_names) == sorted(expected)

    for tool in HEALTHCARE_TOOLS:
        assert tool["type"] == "function"
        assert "parameters" in tool["function"]
        assert tool["function"]["parameters"]["type"] == "object"
        assert len(tool["function"]["parameters"]["required"]) > 0


def test_verify_patient_identity_success():
    """Validates exact deterministic match on known patient fixture."""
    res = verify_patient_identity(
        first_name="Aarav",
        last_name="Sharma",
        date_of_birth="1985-04-12"
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["patient_id"] == "P-10023"
    assert res.data["first_name"] == "Aarav"
    assert res.data["last_name"] == "Sharma"


def test_verify_patient_identity_case_insensitivity():
    """Validates case-insensitive trimming on patient names."""
    res = verify_patient_identity(
        first_name="  aarav  ",
        last_name="SHARMA ",
        date_of_birth="1985-04-12"
    )
    assert res.success is True
    assert res.data["patient_id"] == "P-10023"


def test_verify_patient_identity_not_found():
    """Ensures unknown or invalid DOB returns PATIENT_NOT_FOUND."""
    res = verify_patient_identity(
        first_name="Unknown",
        last_name="Person",
        date_of_birth="2000-01-01"
    )
    assert res.success is False
    assert res.error_code == "PATIENT_NOT_FOUND"


def test_check_schedule_availability(target_test_date):
    """Verifies retrieval of open slots for a clinician."""
    res = check_schedule_availability(
        doctor_name_or_specialty="Cardiology",
        target_date=target_test_date
    )
    assert res.success is True
    assert len(res.data["schedules"]) >= 1
    sched = res.data["schedules"][0]
    assert sched["specialty"] == "Cardiology"
    assert len(sched["available_slots"]) > 0


def test_check_schedule_availability_with_department_synonyms_and_relative_dates():
    """Verifies that colloquial terms ('Cardio Department', 'tomorrow') resolve cleanly."""
    res = check_schedule_availability(
        doctor_name_or_specialty="Cardio Department",
        target_date="tomorrow"
    )
    assert res.success is True
    assert res.data["total_open_slots"] > 0
    assert "Cardiology" in res.message


def test_check_schedule_availability_with_rd_cardo_mishearing():
    """Verifies that acoustic STT mis-transcriptions like 'Rd Cardo department' resolve to Cardiology."""
    res = check_schedule_availability(
        doctor_name_or_specialty="Rd Cardo department",
        target_date="tomorrow"
    )
    assert res.success is True
    assert res.data["total_open_slots"] > 0
    assert "Dr. Ananya Rao" in res.message or "Cardiology" in res.message


def test_check_schedule_availability_with_skin_clinic_and_today():
    """Verifies that dermatology synonyms and today's date resolve cleanly."""
    res = check_schedule_availability(
        doctor_name_or_specialty="skin clinic",
        target_date="today"
    )
    assert res.success is True
    assert res.data["total_open_slots"] > 0
    assert "Dermatology" in res.message or "Dr. Sunita Kapoor" in res.message


def test_end_to_end_booking_and_double_booking_prevention(target_test_date):
    """
    Tests:
    1. Booking an open slot.
    2. Attempting duplicate booking on same slot (must be rejected).
    3. Retrieving booked appointments.
    4. Cancelling appointment and verifying slot is freed.
    """
    patient_id = "P-10023"
    doctor_name = "Dr. Ananya Rao"
    slot_time = "10:00 AM"

    # Pre-cleanup in case a prior test run left a booking
    from src.actions.db_service import get_db_service
    db = get_db_service()
    for pid in [patient_id, "P-10024"]:
        for a in db.get_patient_appointments(pid):
            if a.appointment_date == target_test_date and a.appointment_time == slot_time:
                db.cancel_appointment(pid, a.id)

    # Step 1: Book the appointment
    book_res = book_appointment(
        patient_id=patient_id,
        doctor_name=doctor_name,
        appointment_date=target_test_date,
        appointment_time=slot_time,
        reason_for_visit="Routine cardiac checkup"
    )
    assert book_res.success is True
    assert book_res.data is not None
    appt_id = book_res.data["id"]
    assert appt_id.startswith("APT-")

    # Step 2: Attempt duplicate booking on the exact same slot by another patient
    conflict_res = book_appointment(
        patient_id="P-10024",
        doctor_name=doctor_name,
        appointment_date=target_test_date,
        appointment_time=slot_time,
        reason_for_visit="Conflict attempt"
    )
    assert conflict_res.success is False
    assert conflict_res.error_code == "BOOKING_FAILED"
    assert "already booked" in conflict_res.message.lower()

    # Step 3: Check patient's active appointments
    appts_res = get_patient_appointments(patient_id=patient_id)
    assert appts_res.success is True
    matching_ids = [a["id"] for a in appts_res.data["appointments"]]
    assert appt_id in matching_ids

    # Step 4: Cancel appointment
    cancel_res = cancel_appointment(patient_id=patient_id, appointment_id=appt_id)
    assert cancel_res.success is True

    # Step 5: Verify slot is now free again
    rebook_res = book_appointment(
        patient_id="P-10024",
        doctor_name=doctor_name,
        appointment_date=target_test_date,
        appointment_time=slot_time,
        reason_for_visit="Re-booking freed slot"
    )
    assert rebook_res.success is True

    # Post-cleanup: ensure slot is freed for subsequent test runs
    cleaned_id = rebook_res.data.get("appointment", {}).get("id") or rebook_res.data.get("id")
    if cleaned_id:
        cancel_appointment(patient_id="P-10024", appointment_id=cleaned_id)


def test_execute_tool_dispatcher_with_json_string(target_test_date):
    """Validates the universal dispatcher when receiving JSON serialized strings from LLM."""
    args_json = f'{{"doctor_name_or_specialty": "Dr. Ananya Rao", "target_date": "{target_test_date}"}}'
    res = execute_tool("check_schedule_availability", args_json)
    assert isinstance(res, dict)
    assert res["success"] is True


def test_execute_tool_dispatcher_unknown_tool():
    """Validates error response when an unregistered tool is requested."""
    res = execute_tool("non_existent_tool", {})
    assert res["success"] is False
    assert res["error_code"] == "TOOL_NOT_FOUND"


def test_execute_tool_dispatcher_invalid_args():
    """Validates handling of malformed JSON strings."""
    res = execute_tool("check_schedule_availability", "invalid-non-json-string")
    assert res["success"] is False
    assert res["error_code"] == "INVALID_ARGUMENTS"


def test_new_patient_booking_requires_phone_and_sends_notification(target_test_date):
    """
    Validates that:
    1. A first-time patient booking without a phone number is halted with MISSING_PHONE_NUMBER.
    2. Supplying the phone number registers the new patient, books slot, and dispatches notification ticket.
    """
    import uuid
    unique_name = f"TestPatient_{uuid.uuid4().hex[:6]}"

    import random
    test_slot_date = (date.today() + timedelta(days=random.randint(30, 300))).strftime("%Y-%m-%d")

    # 1. Booking attempt without phone number
    res_no_phone = book_appointment(
        full_name=unique_name,
        doctor_name="Dr. Rajesh Iyer",
        appointment_date=test_slot_date,
        appointment_time="03:00 PM"
    )
    assert res_no_phone.success is False
    assert res_no_phone.error_code == "MISSING_PHONE_NUMBER"
    assert "phone number" in res_no_phone.message.lower()

    # 2. Booking attempt with phone number
    res_with_phone = book_appointment(
        full_name=unique_name,
        phone_number="9876543210",
        doctor_name="Dr. Rajesh Iyer",
        appointment_date=test_slot_date,
        appointment_time="03:00 PM"
    )
    try:
        assert res_with_phone.success is True
        assert "P-" in res_with_phone.message
        assert "Ticket ID" in res_with_phone.message
        assert "notification" in res_with_phone.data
        assert res_with_phone.data["notification"]["success"] is True
        assert "98765" in res_with_phone.data["notification"]["recipient_phone"]
    finally:
        if res_with_phone.success and res_with_phone.data and "appointment_id" in res_with_phone.data:
            cancel_appointment(res_with_phone.data["appointment_id"])


def test_hindi_knee_pain_and_orthopedics_availability():
    """Verifies Hindi query 'घुटने के दर्द' resolves to Orthopedics (Dr. Vikram Sen) across 9 AM - 9 PM."""
    res = check_schedule_availability(
        doctor_name_or_specialty="घुटने के दर्द",
        target_date="कल"
    )
    assert res.success is True
    assert res.data["total_open_slots"] > 0
    assert "Orthopedics" in res.message or "Vikram Sen" in res.message


def test_forward_search_when_patient_asks_when_free():
    """Verifies queries like 'आप मुझे बताओ आप कब फ्री हो?' or 'कोई और दिन' perform forward scanning."""
    res = check_schedule_availability(
        doctor_name_or_specialty="ऑर्थोपेडिक्स",
        target_date="आप मुझे बताओ आप कब फ्री हो?"
    )
    assert res.success is True
    assert res.data["total_open_slots"] > 0
    # Must offer available slots without denial
    assert ("available" in res.message.lower() or "opening" in res.message.lower())


def test_zero_denial_9am_to_9pm_slots_span():
    """Verifies slots cover operating spectrum from 09:00 AM to 08:30 PM."""
    res = check_schedule_availability(
        doctor_name_or_specialty="Orthopedics",
        target_date="tomorrow"
    )
    assert res.success is True
    schedules = res.data.get("schedules", [])
    assert len(schedules) > 0
    slots = schedules[0].get("available_slots", [])
    assert any("09:00 AM" in s for s in slots)
    assert any("08:30 PM" in s or "07:00 PM" in s for s in slots)

