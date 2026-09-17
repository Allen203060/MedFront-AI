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
        first_name="Robert",
        last_name="Chen",
        date_of_birth="1985-04-12"
    )
    assert res.success is True
    assert res.data is not None
    assert res.data["patient_id"] == "P-10023"
    assert res.data["first_name"] == "Robert"
    assert res.data["last_name"] == "Chen"


def test_verify_patient_identity_case_insensitivity():
    """Validates case-insensitive trimming on patient names."""
    res = verify_patient_identity(
        first_name="  robert  ",
        last_name="CHEN ",
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


def test_end_to_end_booking_and_double_booking_prevention(target_test_date):
    """
    Tests:
    1. Booking an open slot.
    2. Attempting duplicate booking on same slot (must be rejected).
    3. Retrieving booked appointments.
    4. Cancelling appointment and verifying slot is freed.
    """
    patient_id = "P-10023"
    doctor_name = "Dr. Sarah Smith"
    slot_time = "10:00 AM"

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


def test_execute_tool_dispatcher_with_json_string(target_test_date):
    """Validates the universal dispatcher when receiving JSON serialized strings from LLM."""
    args_json = f'{{"doctor_name_or_specialty": "Dr. James Wilson", "target_date": "{target_test_date}"}}'
    res = execute_tool("check_schedule_availability", args_json)
    assert isinstance(res, dict)
    assert res["success"] is True


def test_execute_tool_dispatcher_unknown_tool():
    """Validates error response when an unregistered tool is requested."""
    res = execute_tool("non_existent_tool", {})
    assert res["success"] is False
    assert res["error_code"] == "TOOL_NOT_FOUND"


def test_execute_tool_dispatcher_invalid_args():
    """Validates parameter mismatch handling in dispatcher."""
    res = execute_tool("verify_patient_identity", {"invalid_param": "test"})
    assert res["success"] is False
    assert res["error_code"] == "PARAMETER_MISMATCH"
