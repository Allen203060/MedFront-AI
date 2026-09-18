# AuraCare AI Receptionist - Project Soul (`SOUL.md`)

*Last Updated: 2026-09-16*

## 1. Project Vision & Identity
**AuraCare (MedFront)** is an enterprise-grade, HIPAA-compliant clinical Voice AI receptionist and doctor assistant built natively on the Microsoft Azure ecosystem (aligning with Microsoft Certified Azure AI Engineer Associate AI-102 / AI-103 architectures). It replaces fragile third-party AI stacks with a unified, zero-trust Azure foundation designed for low-latency phone triage, patient record retrieval, and automated scheduling.

---

## 2. Core Architecture Blueprint
```
                   [Patient Phone Call (PSTN)]
                                │
                                ▼
           [Azure Communication Services (ACS)]
                     Call Automation SDK
                                │
                 Bi-directional WebSockets (PCM Audio)
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[Azure AI Speech (STT)]                      [Azure AI Speech (TTS)]
- Continuous stream recognition              - Neural voices (Jenny / Aria)
- Silence & barge-in detection               - Streaming chunk playback
        │                                               ▲
        ▼                                               │
   [FastAPI Backend / Asyncio Orchestrator] ────────────┘
        │                       │
        ▼                       ▼
[Azure OpenAI (GPT-4o)]    [Two-Layer Data & RAG Engine]
- System Prompt / Personas  ├─ Layer A: Cosmos DB (Exact ID & CRUD)
- Function / Tool Calling   └─ Layer B: Azure AI Search (Scoped RAG)
```

---

## 3. Current Phase & Progress
Following the **5-Module Isolated Development Plan**:

- [x] **Project Initialization & Scaffolding**
  - Architecture: Isolated modular directory pattern (`src/telephony`, `src/speech`, `src/brain`, `src/rag`, `src/actions`, `src/merger`).
  - Configuration: Pydantic Settings with zero-trust Managed Identity support (`DefaultAzureCredential`).
  - Context Engine: Integrated **Graft** (`@nanonets/graft`) for persistent Tree-sitter AST knowledge mapping.
  - Documentation: Enterprise [README.md](file:///home/allen20306/allen/Azure_VoiceAI/README.md) with Linux & Windows setup guides.
  - Development Mode: Autonomous Execution Mode enabled in `.agents/rules/rules.md`.
- [x] **Module 1: Telephony Isolation (ACS)**
  - Target: Inbound call answering, WebRTC browser caller, Call Automation integration.
  - Status: *Completed*
- [x] **Module 2: Speech Processing Isolation (Azure AI Speech)**
  - Target: Continuous STT with 700ms VAD timeout, Neural TTS (`en-IN-NeerjaNeural`), in-memory streaming.
  - Status: *Completed*
- [x] **Module 3: Conversation Engine Isolation (Azure OpenAI)**
  - Target: GPT-4o Agentic Brain, intent routing, persona prompts, decoupled metadata harvester.
  - Status: *Completed*
- [ ] **Module 4: Knowledge Base & Scoped RAG Isolation (Azure AI Search)**
  - Target: Dual-index setup (`clinic-knowledge-index` + `patient-records-index`), OData filtering by `patient_id`.
  - Status: *Ready for Implementation*
- [ ] **Module 5: Action Layer & Database Isolation (Cosmos DB + Tools)**
  - Target: Function calling integration (`check_availability`, `book_appointment`, `verify_patient`).
  - Status: *Ready for Implementation*
- [x] **Tri-Module Integration (The Voice Merger):**
  - Live full-duplex conversational voice loop connecting Module 1 + Module 2 + Module 3.
  - Resolved audio blackout deadlocks, 6-second LLM latency, duplicate audio playback, and acoustic mic feedback.
  - Status: *Operational & Stabilized*
- [x] **Module 5: Action Layer & Database Isolation (Cosmos DB + Tools)**
  - Target: Function calling integration (`check_schedule_availability`, `book_appointment`, `verify_patient_identity`, `cancel_appointment`, `get_patient_appointments`).
  - Implementation: Domain models ([src/actions/models.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/src/actions/models.py)), Cosmos DB + Mock Store ([src/actions/db_service.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/src/actions/db_service.py)), OpenAI Tool Schemas ([src/actions/schemas.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/src/actions/schemas.py)), Tools & Dispatcher ([src/actions/tools.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/src/actions/tools.py)), Interactive CLI ([src/actions/cli.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/src/actions/cli.py)), and 100% passing test suite ([tests/test_actions.py](file:///c:/Users/Alisha%20Garg/Desktop/Medfront/tests/test_actions.py)).
  - Status: **Completed & Verified** ✅
- [ ] **The Merger:** Full integration of the 5 modules with real-time bi-directional streaming and barge-in cancellation.
  - Status: *Pending Modules 1-4*

---

## 4. Key Architectural Decisions
1. **Cloud Ecosystem:** Native Microsoft Azure across all layers (ACS, Speech, Azure OpenAI, AI Search, Cosmos DB) for enterprise HIPAA compliance and unified identity.
2. **Two-Layer Healthcare Storage:** Separation of transactional identity lookups (Cosmos DB) from clinical unstructured narratives (Azure AI Search) to avoid fuzzy patient identity mismatches.
3. **Dual-Persona RBAC:** 
   - *Receptionist:* Restricted to administrative access scope, mandatory phone verification.
   - *Doctor:* Full longitudinal clinical history access via authenticated role-based access control.
4. **Barge-in Voice UX:** Continuous STT monitoring during TTS playback; immediate audio buffer cancellation upon user speech detection.
5. **Decoupled Team Structure:** Independent module directories (`src/telephony/`, `src/speech/`, etc.) with standalone entry points for isolated unit testing and parallel team development.
6. **Agent Context Engineering (Graft):** Implemented Tree-sitter powered codebase indexing via `@nanonets/graft` to provide AI coding agents with instant AST topological context, reducing token costs and tool exploration cycles by 40-60%.
7. **Autonomous Execution:** Upgraded agent operating rules in `.agents/rules/rules.md` to permit autonomous file management and command execution while maintaining strict engineering tutoring and progress logging.

---

## 5. Next Immediate Milestones
1. Select next isolated module to implement:
   - **Module 3: Brain & Conversation Engine (Azure OpenAI)** — Terminal-based GPT-4o loop wiring up the newly built Module 5 Tool Calling schemas.
   - **Module 2: Speech Processing** — Standalone Azure AI Speech continuous STT and neural TTS benchmark scripts.
   - **Module 4: Knowledge Base & Scoped RAG** — Dual-index Azure AI Search setup with OData partition filtering.
   - **Module 1: Telephony (ACS)** — FastAPI webhook endpoints, inbound call answering, static audio playback.
