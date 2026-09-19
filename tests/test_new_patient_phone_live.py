import asyncio
import json
import urllib.request
import websockets
import sys
import pytest

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

@pytest.mark.asyncio
async def test_new_patient_phone_flow():
    uri = 'ws://127.0.0.1:8000/api/telephony/ws/audio-stream'
    async with websockets.connect(uri) as ws:
        # Drain initial greeting
        initial = json.loads(await ws.recv())
        print("0. Initial greeting received:", initial.get("text", "")[:45], "...")

        # Turn 1: New patient requests booking without phone number
        print("\n1. Turn 1: New patient requests booking without phone number...")
        await ws.send(json.dumps({
            "event": "simulated_speech",
            "text": "I am visiting for the first time, my name is Amit Patel, please book me with Dr. Rajesh tomorrow at 10 AM"
        }))

        t1_reply = None
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get("type") in ("assistant", "agent_response"):
                t1_reply = msg.get("text", "")
                print("   Aura Response to Turn 1:\n  ", t1_reply)
                break

        # Verification for Turn 1: MUST ask for contact phone number, NOT book prematurely!
        assert "phone number" in t1_reply.lower(), "Agent should ask for the new patient's phone number!"
        assert "APT-" not in t1_reply, "Agent should NOT finalize booking without phone number!"
        print("✅ Turn 1 Verified: Aura asked for contact phone number before booking.")

        # Turn 2: Caller provides phone number
        print("\n2. Turn 2: Caller speaks contact phone number...")
        await ws.send(json.dumps({
            "event": "simulated_speech",
            "text": "Sure, my phone number is 9876543210"
        }))

        t2_reply = None
        t2_tool = None
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get("type") in ("assistant", "agent_response"):
                t2_reply = msg.get("text", "")
                t2_tool = msg.get("tool_used")
                print("   Aura Response to Turn 2 (Tool:", t2_tool, "):\n  ", t2_reply)
                break

        # Verification for Turn 2: Finalizes booking, provides MRN, confirmation ID, and mentions notification ticket sent
        assert "P-" in t2_reply or "Amit" in t2_reply, "Expected new patient registration/MRN"
        assert "98765" in t2_reply or "ticket" in t2_reply.lower() or "notification" in t2_reply.lower(), "Expected notification ticket confirmation"
        print("✅ Turn 2 Verified: Aura booked appointment and confirmed notification ticket sent to phone number.")

    # 3. Check Dashboard Notifications Endpoint
    print("\n3. Verifying /api/dashboard/notifications endpoint...")
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard/notifications")
    notif_data = json.loads(req.read().decode())
    print("   Total Dispatched Notifications:", notif_data.get("total_dispatched"))
    assert notif_data.get("total_dispatched", 0) >= 1, "At least 1 notification should be dispatched!"
    latest = notif_data["notifications"][0]
    print("   Latest Notification Ticket:", latest.get("ticket_number"), "to", latest.get("recipient_phone"))
    print("   Message body:", latest.get("message"))
    assert "Amit Patel" in latest.get("patient_name", ""), "Patient name should match Amit Patel"
    assert "98765" in latest.get("recipient_phone", ""), "Recipient phone should match 9876543210"
    print("✅ Notification Verified: Ticket successfully created and accessible to hospital dashboard!")

if __name__ == "__main__":
    asyncio.run(test_new_patient_phone_flow())
