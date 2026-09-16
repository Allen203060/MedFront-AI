Viewed implementation.md:1-55
Viewed isolatedPartsProject.md:1-53

To make patient data queriable, contextual, and updatable for both **Receptionists** and **Doctors**, the architecture needs to evolve beyond just "indexing generic clinic FAQs." 

In healthcare systems, patient information cannot rely on flat vector search alone. If an AI uses fuzzy vector similarity to find "John Smith," it might pull "Jonathon Smyth's" cardiac history. 

Here is the architectural breakdown of how to structure the **Patient Knowledge Base & RAG layer** on Azure to handle querying and storing patient information safely.

---

### 1. The Two-Layer Storage Model: Structured DB + Scoped RAG

Instead of dumping all patient info directly into a vector database, we separate **Identity & Transactions** from **Unstructured Clinical Narratives**:

```
[Inbound Query: "What medications is John on?" / "Book an appointment for Jane"]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [1. Exact Identity Lookup]      [2. Scoped Patient RAG]
       Azure Cosmos DB / SQL          Azure AI Search (Hybrid)
    - Patient ID, MRN, DOB         - Doctor's consultation notes
    - Contact & insurance info     - Call transcripts & summaries
    - Appointments & status        - Lab reports, discharge history
    - Filter key: (Name + DOB)     - Filter: `patient_id eq 'P-10023'`
```

#### Layer A: Structured Patient Profile (Azure Cosmos DB)
* **Purpose:** Exact matching, identity verification, and fast CRUD operations.
* **Indexed by:** Unique `patient_id` (MRN), phone number, and `(last_name, dob)`.
* **Stores:**
  * Demographics (Name, DOB, contact, emergency contact).
  * Insurance status and primary physician.
  * Upcoming and past appointment IDs.
  * Active flags (e.g., high-risk patient, language preference).

#### Layer B: Scoped Patient RAG (Azure AI Search)
* **Purpose:** Answering open-ended semantic questions about patient history.
* **Index Structure:**
  * Document text / chunk (SOAP notes, nurse call summaries, lab result interpretations).
  * **Vector Embeddings:** Generated via `text-embedding-3-large` or `text-embedding-ada-002`.
  * **Critical Metadata Fields (Filterable):**
    * `patient_id` (Crucial: all searches are filtered by `patient_id eq '{current_patient_id}'`).
    * `record_type`: (`doctor_note`, `call_transcript`, `lab_result`, `intake_form`).
    * `author_role`: (`doctor`, `receptionist_ai`, `nurse`).
    * `timestamp`: Date/time of entry.
    * `access_level`: (`clinical` vs `administrative`).

---

### 2. The Dual-Persona Access Model: Receptionist vs. Doctor

Both personas query the same patient, but with completely different permissions, guardrails, and detail levels:

| Feature | Receptionist AI (Voice Agent) | Doctor AI (Clinical Assistant / Copilot) |
| :--- | :--- | :--- |
| **Primary Channel** | Phone voice stream (ACS + Speech) | Web portal, dashboard, or clinician mobile app |
| **Identity Verification** | **Mandatory First Step:** Verifies Caller ID + DOB before accessing records | Authenticated via Azure AD (Entra ID) with Clinician RBAC |
| **Query Scope** | Administrative: insurance, appointments, basic prep instructions, clinic policies | Clinical: diagnoses, longitudinal history, vitals trends, lab values, medication history |
| **RAG Filter** | `patient_id eq 'X' and access_level eq 'administrative'` | `patient_id eq 'X'` (Full access across clinical + admin records) |
| **Write Capabilities** | Appends **Call Summaries** and appointment booking requests | Generates & appends **SOAP Notes**, prescriptions, lab orders, and discharge summaries |

---

### 3. How the Flows Work in Practice

#### A. The Reading / Query Flow
1. **Identification:**
   * Caller: *"Hi, I'm Robert Chen, I called earlier about my test results."*
   * Bot: *"Hi Robert. For verification, could you confirm your date of birth?"*
   * System performs an exact lookup on Cosmos DB `(name, dob)` -> returns `patient_id: P-88214`.
2. **Contextual Retrieval (Filtered RAG):**
   * If the **Doctor** asks: *"Summarize Robert Chen's cardiac history over the past year."*
     * Tool query sent to Azure AI Search:
       * Vector query: Embedding of `"cardiac history heart condition"`
       * Filter expression: `patient_id eq 'P-88214' and timestamp ge 2025-01-01`
     * Top relevant chunks (doctor notes, EKG reports) are injected into the LLM prompt.
3. **Generation:**
   * LLM generates a cited, clinical summary strictly grounded in the retrieved chunks.

#### B. The Writing / Storage Flow ("Store info about the patient")
Whenever an interaction occurs, we store data in both layers:

```
[Call Finishes / Doctor Submits Note]
                  │
                  ▼
         [Extraction Worker]
         Azure OpenAI (GPT-4o)
         Extracts structured metadata + generates summary
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
[Update Cosmos DB]    [Ingest into Azure AI Search]
- Last contact date   - Chunk the summary / note
- Appointment status  - Generate vector embeddings
- Updated triage tag  - Tag with `patient_id`, `timestamp`, `role`
```

* **When the Receptionist AI finishes a phone call:**
  1. The raw audio transcript is processed by an LLM extraction function.
  2. Creates a clean structured log: `reason_for_call`, `action_taken`, `follow_up_needed`.
  3. Writes to Cosmos DB for immediate dashboard view.
  4. Embeds the summary and pushes to Azure AI Search tagged with `patient_id: P-88214, record_type: 'call_transcript'`.
* **When the Doctor conducts a visit or dictates a note:**
  1. Voice dictation or typed notes are formatted into a standard **SOAP** (Subjective, Objective, Assessment, Plan) format.
  2. Saved as an immutable clinical encounter in Cosmos DB.
  3. Chunked and indexed in Azure AI Search so future queries from the doctor can retrieve it instantly.

---

### 4. Technical Integration with our Existing Roadmap

In [isolatedPartsProject.md](file:///home/allen20306/allen/Azure_VoiceAI/isolatedPartsProject.md), we had:
* **Module 4:** Knowledge Base (RAG for static clinic policies/FAQs).
* **Module 5:** Action Layer (Function calling & DB).

To accommodate this, we expand them into:
1. **Split Indexes in Azure AI Search**:
   * Index 1: `clinic-knowledge-index` (Static FAQ, insurance policies, public hours - unpartitioned).
   * Index 2: `patient-records-index` (Dynamic, strictly partitioned and filtered by `patient_id`).
2. **Dedicated Function Calling Tools for the LLM**:
   * `verify_patient(name, dob, phone)` -> returns `patient_id`.
   * `query_patient_records(patient_id, query, category)` -> queries filtered RAG.
   * `save_encounter_note(patient_id, summary, category)` -> pushes to DB & embeds to search index.

---

### Questions to Shape the Exact Setup:

1. **Storage Choice:** Would you prefer **Azure Cosmos DB** (NoSQL document store, very flexible for varying note structures) or a relational database like **Azure Database for PostgreSQL** for the structured patient records?
2. **Doctor Interface:** How will the doctors interact with this system? Will they have a separate web dashboard/chat interface, or will this also be accessible via phone/voice?
3. **Data Standards:** Do you plan to keep the schema simple (custom JSON schemas), or do you want to align with healthcare standards like **FHIR (Fast Healthcare Interoperability Resources)**?