# Implementation Plan: Migrate MedFront Frontend to Dedicated React + TypeScript App (Vite)

Migrate the MedFront AI Receptionist & Clinical Portal frontend from monolithic Python string-rendered HTML/JS (`src/dashboard/ui_template.py`) to a standalone, modern, modular **React + TypeScript (Vite)** single-page application located in `frontend/`.

## Architectural Overview

> **Decoupled Architecture**: 
> The frontend will run on its own dedicated Vite dev server (`http://localhost:5173`) with live Hot Module Replacement (HMR). 
> The FastAPI backend (`http://localhost:8000`) will serve purely as the high-performance asynchronous API & WebSocket server.
>
> We will configure Vite's development proxy (`vite.config.ts`) and FastAPI's `CORSMiddleware` (`src/main.py`) so all REST calls (`/api/dashboard/*`) and WebSocket connections (`/ws/audio`) work seamlessly across both local development and containerized production builds.

---

## 100% Feature Parity Specification

1. **Real-time Voice Console**:
   - Bi-directional 16kHz PCM Web Audio streaming over WebSockets (`/ws/audio`).
   - Dynamic audio waveform visualizer during speech and agent playback.
   - Caller & Aura message bubble transcript log with intent badges and tool notifications.
   - Single-source exclusive Web Audio playback with instant client-side and server-side barge-in interrupt handling.
   - Manual text input prompt fallback.

2. **Doctor Portal & Ambient AI Scribe**:
   - Clinician selector dropdown (Cardiology, General Practice, Dermatology, Orthopedics, Pediatrics).
   - Daily schedule agenda for selected clinician.
   - Ambient Clinical AI Scribe: speech transcription / encounter notes input $\to$ GPT-4o SOAP note generation.
   - Doctor Approval Gate: interactive editable Subjective, Objective, Assessment, Plan fields with "Sign & Confirm" button that indexes to Azure AI Search & Cosmos DB.
   - Longitudinal patient clinical notes viewer.

3. **Receptionist Portal & Master Schedule**:
   - Patient identity verification simulator with DOB and phone validation.
   - Direct booking modal with clinician selection, date/time picker, and reason for visit.
   - Master Appointments Registry: filterable, searchable table with 1-click cancellations and phone confirmation ticket tracking.

4. **Patient Health Records Directory**:
   - Patient profile list with MRN, DOB, contact phone, active insurance provider.
   - Detailed side drawer / modal displaying vitals (BP, HR, BMI), allergies, active diagnoses, and chronological clinical encounter history.

5. **Live Cloud Metrics Topbar**:
   - Real-time status badges for Azure Cosmos DB, Azure AI Search / Local RAG mode, Azure OpenAI.
   - Active doctor count, confirmed appointments count, total patients count.
   - Light and dark theme toggle.

---

## Technical Stack & Layout

- **Framework**: Vite + React 18 / 19 + TypeScript
- **Styling**: Vanilla CSS with modern healthcare tokens (custom CSS custom properties, glassmorphism, responsive data tables, dark/light modes) + `lucide-react` icons.
- **Audio Capture & Streaming**: Web Audio API `AudioContext` with custom downsampling hook (`useVoiceConsole.ts`).

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── types/
    │   └── index.ts                 # TypeScript interfaces for Patient, Appointment, Doctor, SOAP, Stats
    ├── services/
    │   └── api.ts                   # Typed Fetch/Axios client for /api/dashboard/*
    ├── hooks/
    │   ├── useCloudStats.ts         # Periodic poller for cloud service health & stats
    │   └── useVoiceConsole.ts       # Web Audio API hook for /ws/audio streaming & barge-in
    └── components/
        ├── Header.tsx               # Brand logo, cloud health pills, role selector, theme toggle
        ├── DoctorPortal.tsx         # Doctor view: Scribe SOAP generator, approval gate, patient notes
        ├── ReceptionistPortal.tsx   # Identity simulator, direct booking modal, master appointments table
        ├── PatientDirectory.tsx     # Patient records, vitals, allergies, HIPAA scoped history
        └── VoiceConsole.tsx         # Live Web Audio microphone caller, waveform visualizer, transcripts
```

---

## Verification Plan

### Automated Tests
1. **Frontend Build Verification**:
   ```bash
   cd frontend && npm run build
   ```
2. **Backend Regression Verification**:
   ```bash
   .venv/bin/pytest -v tests/test_actions.py tests/test_rag.py tests/test_dashboard.py
   ```

### Manual Verification
1. Launch Vite dev server (`npm run dev`) and test at `http://localhost:5173`.
2. Verify cloud status badges query FastAPI `/api/dashboard/stats` via Vite proxy.
3. Test Voice Console: microphone streaming, live transcription, female Hindi/English TTS audio playback, and barge-in cutoff.
4. Test Scribe SOAP note generation and doctor approval signing.
5. Test patient identity verification and appointment booking.
