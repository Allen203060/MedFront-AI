# Modular Healthcare Voice AI Scaffolding & Architecture

## 1. Architectural Philosophy: The Isolated Multi-Module Pattern

Enterprise voice AI systems are notoriously difficult to debug when built as monolithic applications. A single phone call involves:
1. **Network Telephony Signaling & Webhook Event Grid** (SIP/PSTN handling via Azure Communication Services).
2. **Full-Duplex Media Transport** (PCM 16-bit 16kHz audio over WebSockets).
3. **Continuous Audio Stream Processing** (Real-time Speech-to-Text and chunked Neural Text-to-Speech via Azure AI Speech).
4. **Conversational Intelligence & Agentic Logic** (LLM orchestration, prompt engineering, and structured function calling via Azure OpenAI).
5. **Deterministic Identity Resolution & Scoped Retrieval** (Cosmos DB NoSQL transactions + Azure AI Search hybrid vector retrieval).

If these 5 subsystems are intertwined from day one, tracking down an audio stutter, a race condition during barge-in, or an invalid OData filter becomes an exercise in frustration.

### The Isolated Module Pattern
To enable multi-developer collaboration and clean unit/integration testing, the repository is structured into **5 completely decoupled modules**, unified only at the final **Merger** layer:

```
                                  [ src/ ]
                                     │
      ┌──────────────┬───────────────┼───────────────┬──────────────┐
      ▼              ▼               ▼               ▼              ▼
 [telephony/]    [speech/]      [brain/]          [rag/]        [actions/]
  Module 1:       Module 2:      Module 3:       Module 4:       Module 5:
   ACS Call       Azure AI       Azure OpenAI     Azure AI        Cosmos DB
  Automation     Continuous       Structured     Search Scoped     & Patient
   Webhooks     STT / TTS      Conversation     Hybrid Index        CRUD
      │              │               │               │              │
      └──────────────┴───────┬───────┴───────────────┴──────────────┘
                             ▼
                        [merger/]
                  Full-Duplex Voice
                  FastAPI WebSocket
                  Barge-in Controller
```

---

## 2. Directory Structure & Team Ownership

The codebase is partitioned so individual engineers or sub-teams can work on independent modules without git merge conflicts:

| Subdirectory | Target Azure Service | Team Responsibility |
| :--- | :--- | :--- |
| `src/core/` | Azure Identity / Key Vault | Shared app configuration (`config.py`), base logging, telemetry, security. |
| `src/telephony/` | Azure Communication Services (ACS) | Inbound call routing, Event Grid webhook verification, call leg automation. |
| `src/speech/` | Azure AI Speech Services | Audio stream buffers, continuous STT push-streams, neural voice synthesis. |
| `src/brain/` | Azure OpenAI (GPT-4o) | Conversation state, receptionist/doctor system prompts, tool schemas. |
| `src/rag/` | Azure AI Search | Hybrid search, vector embedding pipelines, scoped OData patient filters. |
| `src/actions/` | Azure Cosmos DB | Deterministic patient lookup `(last_name, dob)`, appointment mutations, FHIR mappings. |
| `src/merger/` | FastAPI WebSockets + Asyncio | Low-latency audio loop wiring all 5 modules together with barge-in cancellation. |
| `tests/` | Pytest | Isolated unit and integration tests for each individual module. |

---

## 3. Configuration & Zero-Trust Security Strategy

In healthcare software handling Protected Health Information (PHI), credentials must never be committed to source code or hardcoded in configuration files.

### Configuration Hierarchy
1. **Local Development:** A local `.env` file (strictly excluded via `.gitignore`) read by Pydantic's `BaseSettings`.
2. **Enterprise Azure Deployment:** `DefaultAzureCredential` from `azure-identity`. The app transparently authenticates via:
   - Managed Identity in Azure App Service / Azure Container Apps.
   - Azure CLI credentials during local developer testing.
   - Environment variables in automated CI/CD runners.

```
                  ┌────────────────────────────────────────┐
                  │      src/core/config.py (Pydantic)     │
                  └───────────────────┬────────────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   [Local Dev (.env file)]                  [Azure Cloud (Zero Secrets)]
   Endpoint URLs, local keys,               Managed Identity via
   mock toggle flags                        DefaultAzureCredential()
```

---

## 4. Latency Considerations from Day 1

Every architectural decision in the voice stack is optimized for end-to-end response latency (target: **< 1200ms** from caller speech cessation to first audio playback byte):

- **FastAPI with Asyncio:** Avoid blocking I/O on the main thread. Audio chunk streaming requires non-blocking asynchronous generators.
- **Push Audio Streams:** Instead of saving audio to temporary disk files, audio is streamed directly in-memory as raw 16-bit 16kHz PCM chunks.
- **Pydantic V2:** High-performance Rust-backed data validation and serialization for function call parameters and API models.
