"""
Taxonomy enumerations for MedFront-AI Agentic Brain.
Defines all supported user intents and backend tool names.
"""

from enum import Enum


class IntentCategory(str, Enum):
    """
    Extensible taxonomy of user intent categories classified by the IntentRouter.
    """
    CASUAL_CONVERSATION = "CASUAL_CONVERSATION"
    CLINIC_INFORMATION = "CLINIC_INFORMATION"
    PATIENT_RECORD_LOOKUP = "PATIENT_RECORD_LOOKUP"
    APPOINTMENT_BOOKING = "APPOINTMENT_BOOKING"
    APPOINTMENT_CANCELLATION = "APPOINTMENT_CANCELLATION"
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    PATIENT_INFORMATION_COLLECTION = "PATIENT_INFORMATION_COLLECTION"
    EMERGENCY_TRIAGE = "EMERGENCY_TRIAGE"
    UNKNOWN_OR_UNSUPPORTED = "UNKNOWN_OR_UNSUPPORTED"


class ToolName(str, Enum):
    """
    Backend tool identifiers that can be executed by the Brain's tool registry.
    """
    CHECK_AVAILABILITY = "check_availability"
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    VERIFY_PATIENT_IDENTITY = "verify_patient_identity"
    GET_CLINIC_POLICY = "get_clinic_policy"
