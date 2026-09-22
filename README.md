# MedFront / AuraCare - Enterprise Healthcare Voice AI

[![Azure Native](https://img.shields.io/badge/Azure-Native_AI--102%2F103-0078D4?logo=microsoftazure)](https://azure.microsoft.com/)
[![Python 3.10 | 3.11](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Zero Trust Security](https://img.shields.io/badge/Security-Zero_Trust_Managed_Identity-blue)](#)

**MedFront (AuraCare)** is an enterprise-grade clinical Voice AI receptionist and doctor assistant built natively on the Microsoft Azure ecosystem. Designed in alignment with **AI-102 / AI-103 enterprise architectures**, it replaces fragile multi-vendor API stacks with a unified, zero-trust Azure foundation for low-latency phone triage, deterministic patient verification, and automated clinical scheduling.

---

## Key Capabilities

1. **Full-Duplex Phone Streaming:** Real-time bi-directional audio streaming over WebSockets via Azure Communication Services (ACS) and Azure AI Speech.
2. **True Audio Barge-In:** Continuous speech recognition (STT) during playback; interrupts and purges TTS output buffers immediately when the caller speaks.
3. **Two-Layer Healthcare Storage:**
   - **Deterministic Layer A (Azure Cosmos DB):** Exact identity resolution (`last_name`, `dob`, `phone_number` $\to$ `patient_id`) and transactional scheduling CRUD.
   - **Scoped Probabilistic Layer B (Azure AI Search):** Hybrid vector search over clinical narratives and clinic FAQs with mandatory OData partition filtering (`patient_id eq '{id}'`).
4. **Dual-Persona RBAC:**
   - **Receptionist AI:** Phone-based voice agent restricted to administrative scope and mandatory caller verification.
   - **Doctor AI:** Web/portal copilot with longitudinal clinical history access and Ambient Scribe synthesis.
5. **Zero-Trust Security:** Zero hardcoded API keys in production; leverages Azure Managed Identities (`DefaultAzureCredential`).

---

## Architectural Blueprint

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

## Repository Structure

The codebase is partitioned into isolated modules so team members can build and test each subsystem independently:

```
MedFront-AI/
├── .env.example             # Sanitized environment variable template
├── pyproject.toml           # Enterprise package configuration
├── requirements.txt         # Pinned Azure dependencies
├── docs/                    # Architecture & system design documentation
├── data/                    # Clinical knowledge store & vector cache
│   ├── knowledge/           # Source clinic policies (.md) and patient records (.json)
│   └── cache/               # Runtime local vector store cache (.json)
├── src/
│   ├── core/                # Shared configuration (Pydantic), Azure credentials, logging
│   ├── telephony/           # Module 1: Azure Communication Services call automation
│   ├── speech/              # Module 2: Azure AI Speech continuous STT & streaming TTS
│   ├── brain/               # Module 3: Azure OpenAI (GPT-4o) conversation & personas
│   ├── rag/                 # Module 4: Azure AI Search scoped hybrid retrieval
│   ├── actions/             # Module 5: Cosmos DB patient lookup & tool mutations
│   ├── dashboard/           # Doctor copilot dashboard & Ambient Scribe UI
│   └── merger/              # Final Integration: Low-latency full-duplex WebSocket loop
├── scripts/                 # Administrative & database utility tools
│   ├── database/            # Database patch, backfill & migration scripts
│   └── queries/             # Data lookup & inspection scripts
└── tests/                   # Independent unit, integration, and sandbox tests
```

---

## Prerequisites

- **Python:** Version **3.10** or **3.11** (recommended for pre-compiled `azure-cognitiveservices-speech` C++ wheels).
- **Node.js:** Version **v18+** or **v20+**.
- **Git:** Version **2.30+**.
- **Azure Subscription:** With access to provision:
  - Azure Communication Services (with a purchased PSTN phone number).
  - Azure AI Speech Services.
  - Azure OpenAI Service (with `gpt-4o` deployment).
  - Azure AI Search.
  - Azure Cosmos DB (NoSQL API).

---

## Setup Guide (Linux / macOS)

### 1. Install System Audio Dependencies (Linux Only)
If testing local microphone audio directly on Linux, install ALSA development headers:
```bash
sudo apt-get update && sudo apt-get install -y libasound2 libasound2-dev
```

### 2. Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/Allen203060/MedFront-AI.git
cd MedFront-AI

# Create virtual environment with Python 3.10 or 3.11
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```
Open `.env` in your editor and fill in your Azure service keys and endpoints.

---

## Setup Guide (Windows)

### 1. Open PowerShell as Administrator (Execution Policy)
If you haven't enabled PowerShell script execution on your workstation, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Clone Repository & Create Virtual Environment
```powershell
git clone https://github.com/Allen203060/MedFront-AI.git
cd MedFront-AI

# Create virtual environment using Python 3.10 or 3.11
python -m venv .venv

# Activate virtual environment
# In PowerShell:
.\.venv\Scripts\Activate.ps1
# Or in Command Prompt (CMD):
copy .env.example .env
```

### 3. Install Python Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```powershell
# In PowerShell:
Copy-Item .env.example .env
# Or in Command Prompt (CMD):
copy .env.example .env
```
Open `.env` in Notepad or VS Code and enter your Azure service credentials.

---

## Verification & Sanity Check

Verify that your environment and configuration are correctly wired:

```bash
# Validate settings loading (Linux & Windows)
python -c "from src.core.config import settings; print(f'Config OK! Environment: {settings.environment}, Model: {settings.azure_openai_deployment_name}')"

# Verify Orchestrator brain import
python -c "from src.brain.orchestrator import AgenticBrainOrchestrator; print('Orchestrator ready!')"
```

---

## Modular Development Progression

To avoid tangled dependencies, follow the isolated module path:

1. **Module 1 (Telephony):** Answer inbound call $\to$ play static `.wav` greeting $\to$ hang up.
2. **Module 2 (Speech Pipeline):** Offline `.wav` transcription (STT) and text synthesis (TTS).
3. **Module 3 (Brain):** Interactive terminal chat loop with GPT-4o and persona prompts.
4. **Module 4 (Scoped RAG):** Dual-index search with strict OData `patient_id` filters.
5. **Module 5 (Actions):** Deterministic Cosmos DB lookups and appointment booking tools.
6. **The Merger:** Assemble modules into the low-latency full-duplex WebSocket loop.

---

## Security & Data Directives

- **Data Privacy Guardrail:** Never query patient records without an exact `patient_id` OData partition filter.
- **Credential Hygiene:** Never commit `.env` or secrets to git. In cloud deployments, enable `USE_MANAGED_IDENTITY=true` to use Azure Entra ID / Managed Identities.
