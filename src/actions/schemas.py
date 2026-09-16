"""
MedFront Action Layer - OpenAI Function Calling Schemas.
Defines the strict JSON Schema specifications for all healthcare action tools
passed to Azure OpenAI (GPT-4o) during multi-turn voice orchestration.
"""

from typing import Any, Dict, List

# Complete collection of tools available to the Receptionist AI
HEALTHCARE_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "verify_patient_identity",
            "description": (
                "Verifies a caller's identity against deterministic patient records using their name "
                "and date of birth. Mandatory first step before reading or modifying personal appointments."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Patient's legal first name (case-insensitive)."
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Patient's legal last name (case-insensitive)."
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Patient's date of birth in YYYY-MM-DD format (e.g. '1985-04-12')."
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Optional caller phone number for secondary verification."
                    }
                },
                "required": ["first_name", "last_name", "date_of_birth"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_schedule_availability",
            "description": (
                "Queries the clinic schedule to find available appointment time slots for a specific doctor "
                "or medical specialty on a requested date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name_or_specialty": {
                        "type": "string",
                        "description": "Name of the doctor (e.g., 'Dr. Sarah Smith') or specialty (e.g., 'Cardiology', 'General Practice')."
                    },
                    "target_date": {
                        "type": "string",
                        "description": "Target date in YYYY-MM-DD format (e.g., '2026-09-20')."
                    }
                },
                "required": ["doctor_name_or_specialty", "target_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "Atomically books an appointment slot for a verified patient with a specified doctor at a given date/time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique verified Patient ID (e.g., 'P-10023'). Caller must be verified first."
                    },
                    "doctor_name": {
                        "type": "string",
                        "description": "Full name of the clinician to book with (e.g., 'Dr. Sarah Smith')."
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Date of appointment in YYYY-MM-DD format."
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Time slot to book (e.g., '10:00 AM', '02:30 PM')."
                    },
                    "reason_for_visit": {
                        "type": "string",
                        "description": "Brief clinical reason or chief complaint described by the caller."
                    }
                },
                "required": ["patient_id", "doctor_name", "appointment_date", "appointment_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": (
                "Cancels an existing confirmed appointment for a patient and frees up the time slot on the doctor's schedule."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique Patient ID owning the appointment."
                    },
                    "appointment_id": {
                        "type": "string",
                        "description": "The unique Appointment ID to cancel (e.g., 'APT-89210')."
                    }
                },
                "required": ["patient_id", "appointment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": (
                "Retrieves all upcoming or past scheduled appointments for a verified patient."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Unique verified Patient ID (e.g., 'P-10023')."
                    }
                },
                "required": ["patient_id"]
            }
        }
    }
]
