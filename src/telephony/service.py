"""
Telephony Service Wrapper for Azure Communication Services (ACS).
Handles Call Automation (Web VoIP & PSTN) and Identity/Token generation.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple
from azure.communication.callautomation import (
    CallAutomationClient,
    CallConnectionClient,
    FileSource,
    CallConnectionProperties,
    CommunicationUserIdentifier,
    CallInvite,
)
from azure.communication.identity import (
    CommunicationIdentityClient,
    CommunicationTokenScope,
)
from src.core.config import settings

logger = logging.getLogger(__name__)


class TelephonyService:
    def __init__(self) -> None:
        """Initialize ACS CallAutomationClient and IdentityClient."""
        if not settings.acs_connection_string:
            logger.warning("ACS_CONNECTION_STRING is not set. Telephony operations will fail.")
            self.client: Optional[CallAutomationClient] = None
            self.identity_client: Optional[CommunicationIdentityClient] = None
        else:
            self.client = CallAutomationClient.from_connection_string(
                settings.acs_connection_string
            )
            self.identity_client = CommunicationIdentityClient.from_connection_string(
                settings.acs_connection_string
            )
            logger.info("CallAutomationClient and CommunicationIdentityClient initialized successfully.")

    def create_web_caller_token(self) -> Dict[str, str]:
        """
        Generates an ephemeral ACS user identity and a VoIP access token
        for the web browser caller.
        """
        if not self.identity_client:
            raise RuntimeError("Identity client not initialized. Check ACS_CONNECTION_STRING.")

        caller_user = self.identity_client.create_user()
        token_response = self.identity_client.get_token(
            caller_user, 
            scopes=[CommunicationTokenScope.VOIP]
        )

        return {
            "caller_user_id": caller_user.properties["id"],
            "token": token_response.token,
            "expires_on": str(token_response.expires_on),
        }

    def call_web_user(self, caller_user_id: str, callback_url: str) -> str:
        """
        Call Automation initiates an outbound VoIP call to the browser WebRTC user.
        Wraps the user inside CallInvite as required by Azure Call Automation SDK.
        """
        if not self.client:
            raise RuntimeError("CallAutomationClient is not configured.")

        target_user = CommunicationUserIdentifier(caller_user_id)
        call_invite = CallInvite(target=target_user)

        logger.info(f"Initiating Call Automation call to Web User: {caller_user_id}")
        
        result = None
        # Automatic retry for transient TCP idle resets (ConnectionResetError: 104)
        for attempt in range(2):
            try:
                result = self.client.create_call(
                    target_participant=call_invite,
                    callback_url=callback_url,
                )
                break
            except Exception as e:
                if attempt == 0 and ("Connection reset" in str(e) or "104" in str(e)):
                    logger.warning(f"ACS connection reset on attempt 1, retrying immediately: {e}")
                    time.sleep(0.3)
                    continue
                raise
        
        # Safely extract call_connection_id across SDK variations
        call_connection_id = getattr(result, "call_connection_id", None)
        if not call_connection_id and hasattr(result, "call_connection_properties"):
            call_connection_id = result.call_connection_properties.call_connection_id

        logger.info(f"Call initiated successfully. CallConnectionId: {call_connection_id}")
        return str(call_connection_id)

    def answer_call(self, incoming_call_context: str, callback_url: str) -> CallConnectionProperties:
        """Answers an incoming call."""
        if not self.client:
            raise RuntimeError("CallAutomationClient is not configured.")

        logger.info(f"Answering inbound call. Event callback target: {callback_url}")
        return self.client.answer_call(
            incoming_call_context=incoming_call_context,
            callback_url=callback_url,
        )

    def play_audio(self, call_connection_id: str, audio_url: str) -> None:
        """Instructs ACS to play audio to all participants on the call."""
        if not self.client:
            raise RuntimeError("CallAutomationClient is not configured.")

        call_connection: CallConnectionClient = self.client.get_call_connection(call_connection_id)
        logger.info(f"Playing audio from {audio_url} on call {call_connection_id}")
        play_source = FileSource(url=audio_url)
        call_connection.play_media_to_all(play_source=play_source)


    def hang_up(self, call_connection_id: str) -> None:
        """Terminates the call for all participants."""
        if not self.client:
            raise RuntimeError("CallAutomationClient is not configured.")

        logger.info(f"Hanging up call {call_connection_id}")
        call_connection: CallConnectionClient = self.client.get_call_connection(call_connection_id)
        call_connection.hang_up(is_for_everyone=True)


# Export singleton
telephony_service = TelephonyService()


def resolve_caller_identity_and_greeting(
    caller_id: Optional[str] = None,
) -> Tuple[str, Optional[Any], Optional[Any]]:
    """
    Caller ID Auto-Lookup (Instant Zero-Friction Verification):
    Queries Cosmos DB Layer A by phone number during call setup handshake.
    If recognized:
      - If upcoming appointment exists:
        "Hello Mr./Ms. {last_name}, welcome back to MedFront Clinic. Are you calling regarding your upcoming appointment with {doctor_name}?"
      - If no upcoming appointment:
        "Hello Mr./Ms. {last_name}, welcome back to MedFront Clinic. How may I assist you today?"
    If not recognized:
      "Hello! Thank you for calling MedFront. My name is Aura. How may I assist you today?"
    """
    default_greeting = (
        "Hello! Thank you for calling MedFront. "
        "May I know your preferred language for this conversation: English, Hindi, or Punjabi?"
    )

    if not caller_id or str(caller_id).lower() in ["anonymous", "unknown", "none", ""]:
        return default_greeting, None, None

    from datetime import date
    from src.actions.db_service import get_db_service

    try:
        db = get_db_service()
        patient = db.get_patient_by_phone(str(caller_id))
        if not patient:
            return default_greeting, None, None

        appts = db.get_patient_appointments(patient.patient_id)
        today_str = str(date.today())
        upcoming = [
            a for a in appts 
            if getattr(a, "status", "") == "CONFIRMED" and getattr(a, "appointment_date", "") >= today_str
        ]
        upcoming.sort(key=lambda x: (x.appointment_date, x.appointment_time))
        next_appt = upcoming[0] if upcoming else None

        salutation = "Mr."
        if hasattr(patient, "gender") and patient.gender and patient.gender.lower().startswith("f"):
            salutation = "Ms."
        elif patient.first_name.lower() in ["priya", "divya", "meera", "sunita", "ananya", "neha", "pooja"]:
            salutation = "Ms."

        if next_appt:
            greeting = (
                f"Hello {salutation} {patient.last_name}, welcome back to MedFront Clinic. "
                f"May I know your preferred language for this conversation: English, Hindi, or Punjabi? "
                f"Are you calling regarding your upcoming appointment with {next_appt.doctor_name}?"
            )
        else:
            greeting = (
                f"Hello {salutation} {patient.last_name}, welcome back to MedFront Clinic. "
                f"May I know your preferred language for this conversation: English, Hindi, or Punjabi?"
            )

        logger.info(
            f"[CALLER ID RECOGNIZED]: Patient {patient.patient_id} ({patient.first_name} {patient.last_name}) "
            f"via phone {caller_id}. Upcoming appointment: {next_appt.id if next_appt else 'None'}"
        )
        return greeting, patient, next_appt

    except Exception as e:
        logger.warning(f"Error in resolve_caller_identity_and_greeting: {e}")
        return default_greeting, None, None
