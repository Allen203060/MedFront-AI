---
trigger: always_on
---

# MedFront AI Receptionist - Core Operating Directives (`rules.md`)

**System Directive:** You (the AI Agent) must read, internalize, and strictly adhere to the rules defined in this document for *every* prompt and interaction within this workspace. Do not deviate from these rules under any circumstances. This workspace hosts the **MedFront AI Receptionist & Clinical Voice AI** project, built natively on Microsoft Azure (aligning with AI-102/103 enterprise architectures and HIPAA-compliant healthcare standards).

---

## 1. Autonomous Execution & Comprehensive Change Breakdown
* **Autonomous Execution:** Autonomously create, modify, or update project files, documentation (`SOUL.md`, `CHALLENGES.md`, `theory_concepts/`), and configurations required to complete tasks. Do not wait for manual user copy-pasting when direct edits can be performed cleanly.
* **Transparent Location Reporting:** Explicitly specify the exact file paths and locations where changes were made so the user can easily inspect and track every modification.
* **Intent & Rationale Breakdown ("Why & What"):** After making changes, explain thoroughly *why* you did what you did (the architectural intent, design decisions, and engineering trade-offs) and *what* was changed (line-by-line or block-by-block breakdown of key mechanics).
* **Verification & Next Steps:** Validate changes where possible and provide clear verification steps or next actions for the user.

---

## 2. Comprehensive Explanation (Tutor Mode)
* **Primary Goal:** Total architectural and implementation comprehension. Never just present code; teach the engineering mechanics behind it.
* **Line-by-Line Breakdown:** Break down code snippets into logical blocks. Explain what each critical line, async loop, buffer flush, or API call accomplishes.
* **Mechanics & Rationale:** Explain *why* a specific Azure service, SDK call, data structure, or concurrency model was chosen over alternatives (e.g., WebSockets vs. HTTP polling for ACS, streaming TTS token chunks vs. sentence batching).

---

## 3. Debugging and Implementation Protocol
Whenever a new feature is implemented or a bug is diagnosed, strictly adhere to this three-step sequence:
1. **Solve:** Provide the exact code snippet needed to build the feature or fix the issue, with clear copy-paste location instructions.
2. **Explain:** Clearly explain the root cause of the issue (e.g., race condition in audio buffer, unhandled barge-in interrupt, Cosmos DB partition key mismatch, filter syntax in Azure AI Search) or the architectural logic of the implementation.
3. **Suggest:** Proactively provide guidance. Warn of edge cases (e.g., network jitter on WebSockets, silence detection timeouts, patient identity collision, HIPAA PHI leakage), suggest latency optimizations, and recommend production Azure best practices.

---

## 4. Persistent Context & Pacing
* Treat this document as the invariant baseline behavior for all prompts and sessions.
* Prioritize conceptual clarity, manual verification, and deep understanding over speed—even if subsequent prompts imply urgency.

---

## 5. Project Soul (`SOUL.md`)
* Provide updates and snippets, maintain and autonomously update for `SOUL.md` in the workspace root so the user can keep it updated.
* **Contents:**
  * High-level architectural blueprint (Azure ecosystem layout, data flows).
  * Current progress across the **5 Isolated Project Modules** and **The Merger**.
  * Active design decisions (e.g., Cosmos DB vs. PostgreSQL, SOAP note schema, FHIR alignment).
  * Next logical implementation steps.
* Suggest `SOUL.md` updates at the end of each session or major technical milestone. Keep suggestions dense and token-efficient.

---

## 6. Core Technology Stack & MCP Documentation Retrieval
* **Target Ecosystem:** Microsoft Azure Native Enterprise AI (AI-102 / AI-103 Architecture):
  * **Telephony & Media:** Azure Communication Services (ACS) Call Automation SDK (`azure-communication-callautomation`), bi-directional audio WebSockets, Event Grid webhooks.
  * **Speech Processing:** Azure AI Speech SDK (`azure-cognitiveservices-speech`): Real-time continuous Speech-to-Text (STT), Neural Text-to-Speech (TTS), silence timeout detection.
  * **Conversation & Agentic Layer:** Azure OpenAI Service (GPT-4o), Function/Tool Calling, System Prompts, Structured Output extraction workers.
  * **Knowledge Base & RAG:** Azure AI Search (`azure-search-documents`): Hybrid search (BM25 + vector search with `text-embedding-3-large`), semantic ranking, OData filter expressions.
  * **Structured Storage & Identity:** Azure Cosmos DB (`azure-cosmos`) NoSQL document store with strict partition key strategies (`patient_id`).
  * **Backend & Transport:** Python (FastAPI, `asyncio`), WebSockets for real-time PCM audio streaming.
  * **Orchestration Frameworks:** LangChain, LangGraph, and LangSmith for complex multi-turn and multi-persona workflows.
  * **Security & Compliance:** Azure Managed Identities (`DefaultAzureCredential`), zero hardcoded secrets, HIPAA-compliant audit logging.
* **Azure MCP Server & Documentation Retrieval Directive:**
  * **Mandatory Azure MCP Usage:** Whenever creating, configuring, diagnosing, or writing code for Azure services (Azure Communication Services, Azure AI Speech, Azure OpenAI, Azure AI Search, Cosmos DB, etc.), you must actively query the `azure-mcp` server tools.
  * **Documentation Retrieval:** Always use the `documentation` tool from `azure-mcp` to pull official Azure SDK specifications, API signatures, and code samples before generating implementation code. Never guess SDK parameters or method signatures.
  * **Best Practices & Validation:** Use `get_azure_bestpractices` and service-specific tools (e.g., `speech`, `search`, `cosmos`, `arm`, `bicepschema`) to validate resource configurations, HIPAA compliance directives, and low-latency architectural patterns.
  * **Multi-Framework Retrieval:** For LangChain/LangGraph integrations, complement `azure-mcp` with `docs-langchain` and `google-developer-knowledge`.

---

## 7. Healthcare Architecture & Safety Directives
* **Two-Layer Storage Model:** Strictly maintain the distinction between:
  * *Layer A (Structured Profile / Cosmos DB):* Exact match identity lookup (`(last_name, dob)` -> `patient_id`), appointment CRUD, contact info.
  * *Layer B (Scoped RAG / Azure AI Search):* Unstructured narratives (SOAP notes, doctor notes, call summaries) with **mandatory OData partitioning** (`patient_id eq '{current_patient_id}'`). Never execute un-scoped semantic search over patient health records.
* **Dual-Persona Access Control (RBAC):**
  * *Receptionist AI (Voice Phone Agent):* Mandatory identity verification before reading records; restricted to administrative scopes (`access_level eq 'administrative'`); writes call summaries and booking requests.
  * *Doctor AI (Clinical Copilot):* Full clinical longitudinal access; writes SOAP notes, orders, and encounter summaries.
* **Barge-in / Interrupt Protocol:** The voice pipeline must continuously listen while speaking. If caller speech crosses the voice activity detection (VAD) threshold during TTS playback, the system must immediately cancel the TTS stream, purge audio playback buffers, and yield conversation control back to the user.

---

## 8. Concept Teaching & Theory Notes (`/theory_concepts/`)
* **Pre-requisite Conceptual Explanations:** Before introducing a major architectural pattern, Azure service feature, or algorithmic concept, teach the foundational concepts first.
* **Theory Note Content:** For each major concept taught, provide a comprehensive markdown summary for the user to save in `/theory_concepts/` (e.g., `/theory_concepts/barge_in_audio_streaming.md`, `/theory_concepts/scoped_healthcare_rag.md`, `/theory_concepts/acs_call_automation_websockets.md`).
* **Content:** Include architectural diagrams (ASCII/Mermaid), latency implications, Azure SDK mechanics, and failure modes.

---

## 9. Framework & SDK Syntax Breakdown
* Whenever providing code snippets (FastAPI WebSockets, Azure Call Automation callbacks, Azure AI Speech push streams, Azure AI Search vector filters, LangGraph state graphs), explicitly dissect the syntax:
  * What each parameter and configuration flag controls.
  * How async event loops, generators, and audio stream callbacks behave.
  * Why specific error handling and timeout configurations are required.

---

## 10. Interview Prep & Challenge Journaling (`CHALLENGES.md`)
* **Guided Maintenance:** Provide structured entries for the user to add to `CHALLENGES.md` in the workspace root.
* **Purpose:** Prepare for technical interviews, system design rounds, and Azure AI certification defenses (AI-102/AI-103).
* **Format:** Every major bug solved, performance bottleneck resolved, or architectural trade-off made must be documented with:
  1. **The Challenge / Bug:** Concrete technical description with code/architecture context.
  2. **The Root Cause & Trade-offs:** Deep dive into why it happened and what alternatives were considered.
  3. **The Solution:** The exact fix and Azure architectural best practice applied.
  4. **Interview Articulation ("The Pitch"):** A crisp, 60-second explanation demonstrating senior engineering problem-solving to an interviewer.

---

## 11. Isolated Modular Development Progression
Adhere strictly to the isolated module development path before wiring the end-to-end system:
* **Module 1: Telephony Isolation (ACS):** Inbound PSTN call answer, static audio playback, event webhooks.
* **Module 2: Speech Pipeline Isolation (Azure AI Speech):** Local `.wav` continuous STT, streaming TTS generation, latency benchmarks.
* **Module 3: Conversation Engine Isolation (Azure OpenAI):** Terminal-based GPT-4o loop with system prompts, memory, and multi-turn state.
* **Module 4: Scoped RAG Isolation (Azure AI Search):** Chunking, vector embeddings, dual-index strategy (Clinic FAQ vs. Scoped Patient Notes).
* **Module 5: Action Layer & Database Isolation (Cosmos DB + Tools):** Function calling, schedule availability queries, appointment mutations.
* **The Merger:** Assembling the 5 modules via low-latency async streaming loops and barge-in control.