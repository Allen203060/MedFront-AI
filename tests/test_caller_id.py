"""
Unit and Integration Tests for Caller ID Auto-Lookup (Instant Zero-Friction Verification)
and Full-Duplex Human Barge-In Signal Processing.

Validates:
1. Cosmos DB Layer A phone number lookup (exact and normalized 10-digit matching).
2. Dynamic greeting personalization based on upcoming confirmed appointments.
3. Returning patient recognition vs. anonymous first-time callers.
4. WebSocket handshake pre-populating session identity within the call setup window.
5. Client-side and server-side barge-in interrupt signal handling.
"""

import json
import pytest
from starlette.testclient import TestClient

from src.actions.db_service import get_db_service
from src.telephony.service import resolve_caller_identity_and_greeting
from src.main import app


def test_get_patient_by_phone_normalized():
    """Verify phone lookup matches varied formatting (country codes, spaces, dashes)."""
    db = get_db_service()

    # 1. Exact formatted match
    p1 = db.get_patient_by_phone("+91-98765-43210")
    assert p1 is not None
    assert p1.first_name == "Aarav"
    assert p1.last_name == "Sharma"

    # 2. Raw 10-digit unformatted
    p2 = db.get_patient_by_phone("9876543210")
    assert p2 is not None
    assert p2.id == p1.id

    # 3. Spaces and hyphens
    p3 = db.get_patient_by_phone("+91 98123 45678")
    assert p3 is not None
    assert p3.first_name == "Priya"
    assert p3.last_name == "Patel"

    # 4. Unknown non-existent number
    p4 = db.get_patient_by_phone("+1-555-000-9999")
    assert p4 is None


def test_caller_id_greeting_with_upcoming_appointment():
    """
    Returning caller with upcoming confirmed appointment should get:
    'Hello Mr. Sharma, welcome back to MedFront Clinic. Are you calling regarding your upcoming appointment with Dr. Ananya Rao?'
    """
    from datetime import date
    db = get_db_service()
    # Ensure confirmed appointment exists for Aarav Sharma
    db.book_appointment(
        patient_id="P-10023",
        doctor_name="Dr. Ananya Rao",
        appointment_date=str(date.today()),
        appointment_time="09:00 AM",
        reason_for_visit="Routine checkup",
    )

    greeting, patient, next_appt = resolve_caller_identity_and_greeting("+91-98765-43210")
    assert patient is not None
    assert patient.last_name == "Sharma"
    assert next_appt is not None
    assert "Dr. Ananya Rao" in next_appt.doctor_name

    assert "Mr. Sharma" in greeting
    assert "welcome back to MedFront Clinic" in greeting
    assert "Dr. Ananya Rao" in greeting
    assert "upcoming appointment" in greeting.lower()


def test_caller_id_greeting_returning_patient_no_appointment():
    """
    Returning caller with no active upcoming appointment should get:
    'Hello Mr. Malhotra, welcome back to MedFront Clinic. May I know your preferred language for this conversation: English, Hindi, or Punjabi?'
    """
    greeting, patient, next_appt = resolve_caller_identity_and_greeting("+91-99887-76655")
    assert patient is not None
    assert patient.last_name == "Malhotra"
    assert next_appt is None
    assert "Mr. Malhotra" in greeting
    assert "welcome back to MedFront Clinic" in greeting
    assert "May I know your preferred language" in greeting


def test_caller_id_greeting_anonymous_or_unknown():
    """
    Anonymous or unknown phone number defaults to standard Aura greeting.
    """
    greeting, patient, next_appt = resolve_caller_identity_and_greeting("anonymous")
    assert patient is None
    assert next_appt is None
    assert "Thank you for calling MedFront" in greeting
    assert "preferred language" in greeting

    greeting2, patient2, _ = resolve_caller_identity_and_greeting(None)
    assert patient2 is None
    assert "Thank you for calling MedFront" in greeting2


def test_websocket_caller_id_handshake_recognized():
    """
    Verify WebSocket connection with ?caller_id=+91-98765-43210 yields recognized patient
    greeting and metadata payload in the initial turn.
    """
    client = TestClient(app)
    with client.websocket_connect("/api/telephony/ws/audio-stream?caller_id=+91-98765-43210") as ws:
        # First message is the assistant greeting
        msg_str = ws.receive_text()
        msg = json.loads(msg_str)

        assert msg["type"] == "assistant"
        assert "Mr. Sharma" in msg["text"]
        assert "Dr. Ananya Rao" in msg["text"]

        assert "recognized_patient" in msg
        rp = msg["recognized_patient"]
        assert rp is not None
        assert rp["patient_id"] == "P-10023"
        assert "Sharma" in rp["name"]
        assert rp["upcoming_doctor"] == "Dr. Ananya Rao"


def test_websocket_client_barge_in_handling():
    """
    Verify sending client_barge_in over WebSocket safely clears playback without terminating connection.
    """
    client = TestClient(app)
    with client.websocket_connect("/api/telephony/ws/audio-stream?caller_id=+91-98765-43210") as ws:
        # Initial greeting
        ws.receive_text()

        # Simulate client detecting speech during audio playback and sending instant cutoff signal
        ws.send_text(json.dumps({"event": "client_barge_in", "type": "interrupt"}))

        # Send regular prompt turn to verify connection remains active and responsive
        ws.send_text(json.dumps({"event": "simulated_speech", "text": "Can I check Dr. Rao's slots?"}))

        found_reply = False
        for _ in range(5):
            reply_raw = ws.receive_text()
            data = json.loads(reply_raw)
            if data.get("type") in ("assistant", "agent_response"):
                found_reply = True
                assert len(data.get("text", "")) > 0
                break

        assert found_reply, "Expected assistant response following barge-in event"
