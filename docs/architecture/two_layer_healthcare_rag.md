
# Theory & Concepts: Two-Layer Healthcare RAG Architecture

## 1. Overview & Problem Statement
In enterprise clinical and voice applications, deploying a naive RAG (Retrieval-Augmented Generation) pipeline poses severe patient safety and HIPAA compliance risks:
* **The "John Smith" Hazard:** If an LLM uses unconstrained vector search to find patient records, semantic similarity can easily pull records belonging to a different patient with a similar name, similar symptoms, or shared demographic phrases.
* **Non-Deterministic Identity:** Probabilistic search (cosine similarity on vector embeddings) must never be used for identity resolution.

---

## 2. The Solution: Two-Layer Storage Architecture

```
[Incoming Voice / Chat Query: "What medications was John prescribed?"]
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [Layer A: Deterministic]          [Layer B: Scoped Semantic]
       Azure Cosmos DB                   Azure AI Search
    - Exact Identity Matching          - Scoped Patient History
    - Unique MRN / Patient ID          - Doctor notes, SOAP encounters
    - Immutable attributes             - Filter: patient_id eq 'P-10023'
```

### Layer A: Deterministic Identity Store (Azure Cosmos DB)
1. **Purpose:** Strict identity resolution, patient verification, contact info, and transactional records (e.g., appointment slots).
2. **Key Lookups:** 
   - Partition Key: `/patient_id`
   - Point reads or exact queries on verified tuples: `(last_name, dob, phone_number)` -> returns unambiguous `patient_id: "P-88214"`.
3. **Guarantees:** Deterministic ACID operations, zero hallucination of patient identity.

### Layer B: Scoped Semantic Retrieval (Azure AI Search)
1. **Purpose:** Answering natural language inquiries about medical history, consultation notes, call transcripts, and lab report narratives.
2. **Partitioned Index Structure:**
   - Text Chunks & Vector Embeddings (`text-embedding-3-large`).
   - **Mandatory Filter Fields:**
     - `patient_id`: Enforces patient data isolation.
     - `record_type`: (`call_transcript`, `soap_note`, `lab_result`, `discharge_summary`).
     - `access_level`: (`administrative` vs `clinical`).
3. **Execution Rule:**
   - Every search query MUST include an OData filter:
     ```odata
     $filter=patient_id eq 'P-88214' and access_level eq 'administrative'
     ```
   - Unfiltered global searches across patient records are prohibited by design.

---

## 3. Dual-Persona Role-Based Access Control (RBAC)

| Persona | Channel | Identity Check | Permitted Scope |
| :--- | :--- | :--- | :--- |
| **Receptionist AI** | Phone (ACS PSTN) | Mandatory Caller ID + DOB verification | `access_level eq 'administrative'` (scheduling, prep, general FAQs) |
| **Doctor AI** | Secure Web Portal | Entra ID (Azure AD) Clinician SSO | Full clinical longitudinal scope (`access_level in ('clinical', 'administrative')`) |

---

## 4. Key Takeaways for System Design
1. **Never use vector search for identity lookup.**
2. **Enforce hard partition filters at query time** (`patient_id eq '...'`).
3. **Separate transactional records from conversational narratives.**
