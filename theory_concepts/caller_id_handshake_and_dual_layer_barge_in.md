# Healthcare Telephony Mechanics: Instant Caller ID Handshake & Dual-Layer Conversational Barge-In

## 1. Architectural Overview & Latency Budget

In clinical voice AI systems, patient experience is defined by two key latency parameters:
1. **Time-to-Greeting & Identification (TTG):** Must occur within the initial 200ms call setup handshake.
2. **Interrupt Turnaround Latency (Barge-In):** Must silence artificial speech within $<100\text{ms}$ when human vocalization begins.

```
Incoming PSTN Call (ACS) / WebRTC (Browser)
                     │
         [200ms Setup Handshake]
                     ├──> Extract ANI (caller_id / phone_number)
                     ├──> Query Cosmos DB Layer A: (Normalized 10-digit suffix)
                     │       └── Matches Patient Record: 'P-10023' (Aarav Sharma)
                     ├──> Check Longitudinal Appointments (status='CONFIRMED', date >= today)
                     │       └── Next: 'Dr. Ananya Rao' (Cardiology, 2026-09-20)
                     │
                     ▼
         [Personalized Synthesized Greeting]
   "Hello Mr. Sharma, welcome back to MedFront Clinic.
    Are you calling regarding your upcoming appointment with Dr. Rao?"
```

---

## 2. Zero-Friction Identity Resolution Mechanics

### Why Suffix Normalization?
Telephony protocols transmit phone numbers in various formats:
- E.164 with international dial codes: `+919876543210`
- Delimited with hyphens: `+91-98765-43210`
- Local National Format: `09876543210` or `9876543210`

By stripping all non-digit characters (`re.sub(r"\D", "", phone)`) and indexing the **last 10 digits**, the system eliminates formatting divergence and performs instantaneous $O(1)$ partition-keyed lookups against Cosmos DB Layer A.

### Zero-Friction Pre-Verification
When `resolve_caller_identity_and_greeting` identifies a caller:
1. It injects `patient_id` and `verified_name` directly into the agent's multi-turn session memory (`brain_orchestrator.memory.update_session(...)`).
2. The initial system prompt turn is pre-seeded with caller context.
3. Subsequent action calls (e.g. `check_schedule_availability` or `book_appointment`) do not require the patient to re-verify identity.

---

## 3. Dual-Layer Real-Time Barge-In Architecture

### Why Single-Direction Cloud STT Barge-In Fails
In traditional voice bots, the bot streams audio from the speaker while the microphone streams to a cloud STT engine. When the human speaks:
$$\text{Latency} = T_{\text{mic\_buffer}} + T_{\text{upload}} + T_{\text{cloud\_stt\_hypothesis}} + T_{\text{download\_interrupt}} + T_{\text{client\_drain}}$$
This creates an 800–1200ms lag where the AI continues speaking over the user.

```
=============================================================================
                DUAL-LAYER REAL-TIME BARGE-IN TIMING DIAGRAM
=============================================================================

Human Speaks: "Wait, stop"
   │
   ├─► [LAYER 1: Client-Side RMS VAD] (0ms - 35ms)
   │   • Web Audio AudioWorklet / ScriptProcessor computes buffer RMS energy
   │   • rms = sqrt(sum(x^2)/N) > 0.035
   │   • currentSourceNode.stop() [0ms instant local speaker cutoff]
   │   • Transmits WebSocket frame: {"type": "client_barge_in"}
   │
   └─► [LAYER 2: Cloud STT Safety Catch] (70ms - 150ms)
       • Azure Speech SDK with StablePartialResultThreshold="1"
       • on_interim callback fires immediately on first syllable
       • Telephony client cancels ACS media playback (cancel_all_media_operations)
       • Server pushes {"type": "interrupt"} as redundant safety guarantee
=============================================================================
```

---

## 4. Azure Production Directives & Failure Modes

1. **Acoustic Speaker Feedback (Echo Loopback):**
   - Laptops without headphones leak assistant audio from speakers back into the microphone.
   - Fixed by combining Web Audio API `echoCancellation: true` hardware constraints with an echo-suppression algorithm on the server: if the transcribed text has $\ge 75\%$ lexical overlap with the sentence that was just spoken by the assistant within 300ms, it is filtered out as acoustic loopback.

2. **WebSocket Thread Safety:**
   - Azure Speech SDK callbacks run on native C++ worker threads.
   - Disagreeing event loops or un-synchronized concurrent `websocket.send_json` invocations result in `RuntimeError: Another coroutine is already writing to this socket`.
   - Wrapping WebSocket writes in an `asyncio.Lock()` ensures deterministic, non-colliding message ordering.
