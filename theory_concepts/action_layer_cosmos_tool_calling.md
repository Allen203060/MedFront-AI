# Theory & Concepts: Action Layer, Cosmos DB Partitioning & OpenAI Function Calling

## 1. Architectural Role of the Action Layer

In a conversational Voice AI architecture, the Large Language Model (LLM) is purely a **reasoning engine**, not a database or an execution runtime. 

If an LLM says:
> *"I have booked your appointment with Dr. Smith for Tuesday at 10:00 AM."*

Without an action layer, the LLM has merely generated a statistically probable sequence of tokens. **Nothing was actually scheduled in the clinic's database.**

The **Action Layer** acts as the deterministic bridge between probabilistic natural language and transactional database state:

```
[Patient Voice Input]
       │
       ▼
[Azure OpenAI (GPT-4o)]
       │ (Emits structured JSON Tool Call: `book_appointment(...)`)
       ▼
[Action Layer Dispatcher] ──(Validates types via Pydantic)
       │
       ▼
[Database Service (Cosmos DB)] ──(Executes atomic ACID transaction)
       │
       ▼
[Tool Result Output] ──(Injected back into LLM context to confirm to caller)
```

---

## 2. Why Azure Cosmos DB (NoSQL) for Healthcare Voice AI?

Voice conversations impose a strict latency ceiling: **the total end-to-end response time must remain under 1200ms**. If an identity lookup or availability check takes 300ms, the caller experiences awkward conversational pauses.

### A. Sub-10ms Point Reads
Azure Cosmos DB provides guaranteed single-digit millisecond latency for point reads (reading a document by its `id` and `partition_key`). 

```
Point Read Latency:  ██ 5-8 ms (Cosmos DB)
Relational Join:     ████████████████ 45-120 ms (SQL Server / Postgres)
```

### B. Partition Key Strategy: `/patient_id`
In Cosmos DB, data is distributed across physical partitions based on a chosen **Partition Key**. 

For MedFront, we enforce `/patient_id` as the partition key across all patient-specific containers:
1. **Physical Isolation:** All encounters, appointments, and contact info for a specific patient live in the same logical partition.
2. **Query Efficiency:** Querying a patient's data with `SELECT * FROM c WHERE c.patient_id = 'P-10023'` targets a single physical partition (1-2 Request Units / RUs), completely avoiding expensive cross-partition fan-out queries.
3. **HIPAA Data Boundary:** Hard partition scoping prevents query contamination across different patients.

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure Cosmos DB Database                  │
├──────────────────────────────┬──────────────────────────────┤
│  Container: `patients`       │  Container: `appointments`   │
│  Partition Key: /patient_id  │  Partition Key: /patient_id  │
├──────────────────────────────┼──────────────────────────────┤
│  [Partition: P-10023]        │  [Partition: P-10023]        │
│  - Demographics (Chen)       │  - Appt 1: 2026-09-20        │
│  - Insurance info            │  - Appt 2: 2026-10-15        │
├──────────────────────────────┼──────────────────────────────┤
│  [Partition: P-10024]        │  [Partition: P-10024]        │
│  - Demographics (Gomez)      │  - Appt 1: 2026-09-22        │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 3. Mechanics of OpenAI Function / Tool Calling

OpenAI Function Calling (Tools API) allows GPT-4o to output structured JSON matching a predefined JSON Schema rather than arbitrary conversational text.

### The 4-Step Tool Lifecycle:
1. **Schema Declaration:** When invoking Azure OpenAI, the client sends a `tools` parameter containing the function name, description, and JSON Schema of arguments.
2. **Model Decision:** GPT-4o analyzes the caller's request. If the user asks *"Can I see Dr. Smith on Tuesday?"*, the model emits `finish_reason: "tool_calls"` with arguments `{"doctor_name_or_specialty": "Dr. Smith", "target_date": "2026-09-22"}`.
3. **Deterministic Execution:** The Python orchestrator catches the tool call, executes the verified Python function (`check_schedule_availability`), and gets the actual open slots from Cosmos DB.
4. **Context Injection & Natural Response:** The orchestrator appends the tool result message with role `tool` and `tool_call_id` back to the conversation history. GPT-4o then generates a natural voice-friendly response to the caller: *"Dr. Smith has an opening at 10:00 AM and 2:30 PM on Tuesday. Which one works best for you?"*

```
Caller: "Do you have anything open with Dr. Smith next Tuesday?"
   │
   ▼
[Azure OpenAI] ──(Generates Tool Call JSON)
   │
   ▼
[Python Dispatcher]
   │ ──> Calls `check_schedule_availability("Dr. Smith", "2026-09-22")`
   │ <── Returns `{"available_slots": ["10:00 AM", "02:30 PM"]}`
   │
   ▼
[Azure OpenAI] ──(Receives Tool Result)
   │
   ▼
Voice Output: "Dr. Smith is available at 10:00 AM and 2:30 PM on Tuesday."
```

---

## 4. Concurrency & Preventing Double-Booking Race Conditions

In real-world clinics, two patients or receptionists might attempt to book the same appointment slot simultaneously.

### The Problem:
1. Caller A asks for Tuesday 10:00 AM (Slot is open).
2. Caller B asks for Tuesday 10:00 AM (Slot is open).
3. Both callers confirm simultaneously.

### The Healthcare Solution:
1. **Atomic State Check:** The slot is verified immediately prior to mutation within an isolated transaction lock.
2. **E-Tag / Optimistic Concurrency:** In Azure Cosmos DB, every document has an `_etag`. When updating a schedule document, we pass `If-Match: <etag>`. If another process modified the schedule between read and write, Cosmos DB rejects the update with HTTP `412 Precondition Failed`.
3. **Graceful Voice Recovery:** If a slot collision occurs, the tool returns `success: False, error: "SLOT_TAKEN"`, allowing the AI Receptionist to immediately inform the caller: *"I apologize, that 10:00 AM slot was just taken. I also have 2:30 PM available on the same day—would that work?"*
