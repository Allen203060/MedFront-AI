"""
MedFront Action Layer - Healthcare Action Tools & Dispatcher.
Implements the business logic functions called by the AI Receptionist (GPT-4o)
and provides a universal dispatcher with strict error handling and audit logging.
"""

import json
import logging
from typing import Any, Dict, Optional

from src.actions.db_service import get_db_service
from src.actions.models import ActionResult

logger = logging.getLogger("MedFront.Actions.Tools")


def verify_patient_identity(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    phone_number: Optional[str] = None,
) -> ActionResult:
    """
    Verifies caller identity deterministically using exact match on (first_name, last_name, DOB).
    Prevents probabilistic vector hallucination of patient records.
    """
    db = get_db_service()
    logger.info(f"Executing verify_patient_identity: {first_name} {last_name}, DOB: {date_of_birth}")

    patient = db.get_patient_by_identity(
        first_name=first_name, last_name=last_name, date_of_birth=date_of_birth
    )

    if not patient:
        logger.warning(f"Verification failed: No patient found matching {first_name} {last_name} ({date_of_birth})")
        return ActionResult(
            success=False,
            message="No patient record found matching the provided name and date of birth.",
            error_code="PATIENT_NOT_FOUND",
        )

    # Optional phone number sanity check
    if phone_number:
        # Normalize digits
        clean_input = "".join(filter(str.isdigit, phone_number))
        clean_db = "".join(filter(str.isdigit, patient.phone_number))
        if clean_input and clean_db and clean_input[-4:] != clean_db[-4:]:
            logger.warning(f"Phone mismatch for patient {patient.id}")
            # We still allow verification if DOB matches, but flag in data
            return ActionResult(
                success=True,
                message=f"Patient {patient.first_name} {patient.last_name} verified (Note: phone number differed).",
                data={
                    "patient_id": patient.id,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "insurance_provider": patient.insurance_provider,
                },
            )

    return ActionResult(
        success=True,
        message=f"Patient {patient.first_name} {patient.last_name} successfully verified.",
        data={
            "patient_id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "insurance_provider": patient.insurance_provider,
        },
    )


def check_schedule_availability(
    doctor_name_or_specialty: str, target_date: str
) -> ActionResult:
    """
    Queries clinic schedules to retrieve open time slots for a doctor or specialty on a given date.
    """
    db = get_db_service()
    logger.info(f"Checking schedule availability for '{doctor_name_or_specialty}' on {target_date}")

    schedules = db.get_doctor_schedules(
        doctor_name_or_specialty=doctor_name_or_specialty, target_date=target_date
    )

    if not schedules:
        return ActionResult(
            success=False,
            message=f"No clinician schedule found matching '{doctor_name_or_specialty}' on {target_date}.",
            data={"available_slots": []},
            error_code="NO_SCHEDULE_FOUND",
        )

    results = []
    total_open_slots = 0

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

    if total_open_slots == 0:
        return ActionResult(
            success=True,
            message=f"No open slots remaining for '{doctor_name_or_specialty}' on {target_date}.",
            data={"schedules": results, "available_slots": []},
        )

    return ActionResult(
        success=True,
        message=f"Found {total_open_slots} available slots for '{doctor_name_or_specialty}' on {target_date}.",
        data={"schedules": results},
    )


def book_appointment(
    patient_id: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    reason_for_visit: str = "General Consultation",
) -> ActionResult:
    """
    Atomically books an appointment slot for a verified patient with the requested clinician.
    """
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
