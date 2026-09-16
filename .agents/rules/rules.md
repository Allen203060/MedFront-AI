---
trigger: always_on
---

# MedFront AI Receptionist - Core Operating Directives (`rules.md`)

**System Directive:** You (the AI Agent) must read, internalize, and strictly adhere to the rules defined in this document for *every* prompt and interaction within this workspace. Do not deviate from these rules under any circumstances. This workspace hosts the **MedFront AI Receptionist & Clinical Voice AI** project, built natively on Microsoft Azure (aligning with AI-102/103 enterprise architectures and HIPAA-compliant healthcare standards).

---

## 1. Autonomous Execution & Development
* **Autonomous Code & File Management:** You are authorized to create, update, and manage project application files, documentation, `SOUL.md`, `CHALLENGES.md`, and `theory_concepts/` autonomously.
* **Autonomous Commands:** You are authorized to execute terminal commands, test scripts, and build tasks on my behalf.
* **Complete Code Delivery:** Always write complete, production-ready, clean, well-typed code (no lazy pseudo-code or unexplained ellipses).
* **Clear Reporting:** Always explain changes made, list modified files, and summarize execution results.

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
* Maintain and autonomously update `SOUL.md` in the workspace root.
* **Contents:**
  * High-level architectural blueprint (Azure ecosystem layout, data flows).
  * Current progress across the **5 Isolated Project Modules** and **The Merger**.
  * Active design decisions (e.g., Cosmos DB vs. PostgreSQL, SOAP note schema, FHIR alignment).
  * Next logical implementation steps.
* Update `SOUL.md` at the end of each session or major technical milestone. Keep it dense and token-efficient.

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
* **Documentation Retrieval Requirement:** Whenever designing or implementing features involving LangChain, LangGraph, or cloud services, query available MCP tools (such as `docs-langchain` and `google-developer-knowledge`) to pull the latest SDK specifications and best practices before drafting code.

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
* **Autonomous Theory Note Creation:** For each major concept taught, autonomously generate a markdown summary file in `/theory_concepts/` (e.g., `/theory_concepts/barge_in_audio_streaming.md`, `/theory_concepts/scoped_healthcare_rag.md`, `/theory_concepts/acs_call_automation_websockets.md`).
* **Content:** Include architectural diagrams (ASCII/Mermaid), latency implications, Azure SDK mechanics, and failure modes.

---

## 9. Framework & SDK Syntax Breakdown
* Whenever providing code snippets (FastAPI WebSockets, Azure Call Automation callbacks, Azure AI Speech push streams, Azure AI Search vector filters, LangGraph state graphs), explicitly dissect the syntax:
  * What each parameter and configuration flag controls.
  * How async event loops, generators, and audio stream callbacks behave.
  * Why specific error handling and timeout configurations are required.

---

## 10. Interview Prep & Challenge Journaling (`CHALLENGES.md`)
* **Autonomous Maintenance:** Autonomously create and maintain `CHALLENGES.md` in the workspace root.
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
