# AuraCare AI Receptionist - Project Soul (`SOUL.md`)

*Last Updated: 2026-09-18*

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
- Continuous stream recognition              - Neural voices (en-IN-NeerjaNeural)
- Silence & barge-in detection (700ms VAD)   - Streaming chunk playback
        │                                               ▲
        ▼                                               │
   [FastAPI Backend / Asyncio Orchestrator] ────────────┘
        │                       │
        ▼                       ▼
[Azure OpenAI (GPT-4.1-mini)]  [Two-Layer Data & RAG Engine]
- System Prompt / Personas     ├─ Layer A: Cosmos DB (Exact ID & CRUD)
- Function / Tool Calling      └─ Layer B: Azure AI Search (Scoped RAG)
```

---

## 3. Current Phase & Progress
Following the **5-Module Isolated Development Plan**:

- [x] **Project Initialization & Scaffolding**
  - Architecture: Isolated modular directory pattern (`src/telephony`, `src/speech`, `src/brain`, `src/rag`, `src/actions`, `src/merger`).
  - Configuration: Pydantic Settings with zero-trust Managed Identity support (`DefaultAzureCredential`).
  - Context Engine: Integrated **Graft** (`@nanonets/graft`) for persistent Tree-sitter AST knowledge mapping.
  - Documentation: Enterprise [README.md](file:///home/allen20306/allen/Azure_VoiceAI/README.md) with Linux & Windows setup guides.
- [x] **Module 1: Telephony Isolation (ACS)**
  - Target: Inbound call answering, WebRTC browser caller, Call Automation integration.
  - Status: **Completed & Operational** ✅
- [x] **Module 2: Speech Processing Isolation (Azure AI Speech)**
  - Target: Continuous STT with 700ms VAD timeout, Indian English Neural TTS (`en-IN-NeerjaNeural`), in-memory streaming.
  - Status: **Completed & Operational** ✅
- [x] **Module 3: Conversation Engine Isolation (Azure OpenAI)**
  - Target: GPT-4.1-mini Agentic Brain, intent routing, persona prompts, decoupled metadata harvester.
  - Status: **Completed & Operational** ✅
- [x] **Module 4: Knowledge Base & Scoped RAG Isolation (Azure AI Search)**
  - Target: Dual-index setup (`clinic-knowledge-index` + `patient-records-index`), OData filtering by `patient_id`, Azure OpenAI `text-embedding-3-large` with 1536-dim Matryoshka Representation Learning (MRL) embeddings.
  - Status: **Completed & Live on Azure** ✅
- [x] **Module 5: Action Layer & Database Isolation (Cosmos DB + Tools)**
  - Target: Function calling integration (`check_schedule_availability`, `book_appointment`, `verify_patient_identity`, `cancel_appointment`, `get_patient_appointments`).
  - Implementation: Live Azure Cosmos DB auto-provisioning & seeding (`auracare_db`), Indian patient cohort (`Aarav Sharma`, `Priya Patel`, `Vikram Malhotra`), optimistic concurrency double-booking prevention, 100% passing test suite.
  - Status: **Completed & Live on Azure** ✅
- [x] **The Merger:** Full integration of the 5 modules with real-time bi-directional streaming, live RAG provider (`LiveRAGProvider`), live tool execution (`LiveToolRegistry`), and barge-in cancellation.
  - Status: **Assembled & Live** ✅

---

## 4. Key Architectural Decisions
1. **Cloud Ecosystem:** Native Microsoft Azure across all layers (ACS, Speech, Azure OpenAI, AI Search, Cosmos DB) for enterprise HIPAA compliance and unified identity.
2. **Two-Layer Healthcare Storage:** Separation of transactional identity lookups (Cosmos DB) from clinical unstructured narratives (Azure AI Search) to avoid fuzzy patient identity mismatches.
3. **Dual-Persona RBAC:** 
   - *Receptionist:* Restricted to administrative access scope, mandatory phone verification.
   - *Doctor:* Full longitudinal clinical history access via authenticated role-based access control.
4. **Barge-in Voice UX:** Continuous STT monitoring during TTS playback; immediate audio buffer cancellation upon user speech detection.
5. **Decoupled Team Structure:** Independent module directories (`src/telephony/`, `src/speech/`, etc.) with standalone entry points for isolated unit testing and parallel team development.
6. **Matryoshka Embeddings (MRL):** Shortening `text-embedding-3-large` vectors from 3072 to 1536 dimensions with $L_2$ normalization, saving 50% index storage and reducing HNSW query latency without precision loss.
7. **Idempotent DB Seeding & Slot Protection:** Cosmos DB auto-provisions collections with partition keys and checks existing active bookings before atomic slot mutation to prevent race conditions.
8. **Clinical & Administrative Dashboard:** Integrated glassmorphic hospital portal providing real-time inspection of Layer A Cosmos DB patient records, Layer B scoped RAG clinical charts, active bookings, and an interactive Receptionist Identity Resolution & HIPAA RBAC simulator.

---

## 5. Active System Status
- All 29 automated tests (`tests/test_actions.py`, `tests/test_rag.py`, `tests/test_dashboard.py`) passing against live Azure cloud resources.
- Bi-directional sub-millisecond voice barge-in with server-client interrupt protocol and local Web Audio RMS cutoff.
- Azure AI Speech PhraseListGrammar domain biasing for Indian specialties, colloquial department terms, and clinic doctor names.
- Multi-tier relative date normalization ("tomorrow" -> ISO `YYYY-MM-DD`) and fuzzy/phonetic doctor & specialty canonicalization ("Rd Cardo" -> "Cardiology").
- 17 knowledge chunks indexed in Azure AI Search.
- Indian patient cohort seeded in Azure Cosmos DB `auracare_db`.
- Hospital Clinical & Voice AI Portal live at `http://localhost:8000/dashboard` and `/`.
- Dual-tier Web Calling pipeline active: Instant 1-click 16kHz PCM streaming WebSocket + ACS Call Automation WebRTC carrier dialing with HTML5 iframe permission delegation.
- Ready for end-to-end telephone & web caller voice calls.
