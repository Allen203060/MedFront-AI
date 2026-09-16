"""
Telephony Service Wrapper for Azure Communication Services (ACS).
Handles Call Automation (Web VoIP & PSTN) and Identity/Token generation.
"""

import logging
from typing import Dict, Optional
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
        
        result = self.client.create_call(
            target_participant=call_invite,
            callback_url=callback_url,
        )
        
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
