import asyncio
import json
import websockets
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    uri = 'ws://127.0.0.1:8000/api/telephony/ws/audio-stream'
    async with websockets.connect(uri) as ws:
        # Drain initial greeting
        initial = json.loads(await ws.recv())
        print("1. Initial greeting:", initial.get("text", "")[:50], "...")

        # Turn 1: Hindi utterance
        print("\n2. Sending Hindi greeting...")
        await ws.send(json.dumps({"event": "simulated_speech", "text": "नमस्ते, मुझे डॉक्टर से मिलना है"}))
        
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get("type") in ("assistant", "agent_response"):
                t1 = msg.get("text", "")
                has_hindi = any('\u0900' <= ch <= '\u097f' for ch in t1)
                print(f"   Aura Response (Hindi={has_hindi}): {t1}")
                assert has_hindi, "Expected Hindi response to Hindi greeting!"
                break

        # Turn 2: English utterance (Language Switch + First-Time Patient Booking)
        print("\n3. Sending English first-time booking utterance...")
        await ws.send(json.dumps({
            "event": "simulated_speech",
            "text": "I am visiting for the first time, my name is Suresh Verma, please book me with Dr. Rajesh Kumar tomorrow at 10 AM"
        }))

        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            if msg.get("type") in ("assistant", "agent_response"):
                t2 = msg.get("text", "")
                has_hindi_t2 = any('\u0900' <= ch <= '\u097f' for ch in t2)
                tool = msg.get("tool_used")
                print(f"   Aura Response (Switched to English={not has_hindi_t2}, Tool={tool}):\n   {t2}")
                assert not has_hindi_t2, "Expected English response, agent remained locked in Hindi!"
                assert tool == "book_appointment", f"Expected book_appointment tool, got {tool}"
                assert "Suresh" in t2 or "P-" in t2 or "confirmed" in t2.lower(), "Expected booking confirmation"
                print("\n✅ Verification Successful: Hindi greeted in Hindi, then smoothly switched to English and booked first-time patient!")
                break

if __name__ == "__main__":
    asyncio.run(main())
