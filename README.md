# CivicResolve AI

> **"AI interprets. Python enforces. Tools act."**

CivicResolve AI is an AI-assisted civic grievance and resolution platform designed for municipal corporations and public services. It enables citizens to report civic issues through multiple accessible channels—**Web Form**, **Conversational AI Chat**, and **Real-Time Phone Callbot**—and orchestrates end-to-end municipal triage, automated duplicate detection, deterministic risk scoring, SLA tracking, field resolution verification, and citizen confirmation.

The system enforces a strict architectural boundary: **Generative AI extracts facts and interprets multimodal unstructured inputs, while deterministic Python code controls business logic, state transitions, risk scores, SLAs, department routing, and database transactions.**

---

## Table of Contents

1. [Key Features](#1-key-features)
2. [Final Complaint Lifecycle](#2-final-complaint-lifecycle)
3. [Multi-Channel Intake Architecture](#3-multi-channel-intake-architecture)
4. [Duplicate Detection Engine](#4-duplicate-detection-engine)
5. [Evidence System](#5-evidence-system)
6. [Callbot Architecture](#6-callbot-architecture)
7. [Project Structure](#7-project-structure)
8. [Technology Stack](#8-technology-stack)
9. [Prerequisites & System Requirements](#9-prerequisites--system-requirements)
10. [Fresh Installation from GitHub](#10-fresh-installation-from-github)
11. [Environment Variables Configuration](#11-environment-variables-configuration)
12. [Local Execution Commands](#12-local-execution-commands)
13. [Twilio & ngrok Setup (Callbot Local Development)](#13-twilio--ngrok-setup-callbot-local-development)
14. [Authority & Admin Authentication](#14-authority--admin-authentication)
15. [SQLite Database Management](#15-sqlite-database-management)
16. [Important API Endpoints](#16-important-api-endpoints)
17. [Testing & Quality Assurance](#17-testing--quality-assurance)
18. [Full Manual Acceptance Test Checklist](#18-full-manual-acceptance-test-checklist)
19. [Common Troubleshooting & Recovery](#19-common-troubleshooting--recovery)
20. [Production & Expo Deployment Architecture](#20-production--expo-deployment-architecture)
21. [Security Checklist](#21-security-checklist)
22. [Backup & Disaster Recovery](#22-backup--disaster-recovery)
23. [Final Expo Startup Checklist](#23-final-expo-startup-checklist)
24. [Current Verification Status](#24-current-verification-status)

---

## 1. Key Features

### Citizen Capabilities
- **Multi-Channel Intake:** Report issues via structured Web Form, conversational AI Chat, or standard phone call to the AI Voice Callbot.
- **Multimodal Evidence:** Upload initial photographic evidence (JPEG, PNG, WebP) and capture high-accuracy browser GPS coordinates.
- **Evidence Links:** Receive instant, secure SMS links during phone calls to upload photos or confirm GPS without installing an app.
- **Zero-Barrier Reporting:** Evidence is always optional—complaints can be filed with purely spoken or written descriptions.
- **Live Complaint Tracking:** Real-time timeline view of triage trace, assigned department, SLA countdown, and resolution history using Ticket IDs (`CR-YYMMDD-XXXX`).
- **Citizen Confirmation Loop:** Review field repairs, examine resolution photos, and either confirm closure or reject/reopen the grievance.

### AI Intelligence (Groq Multimodal & Whisper)
- **Multimodal Fact Extraction:** Analyzes text and images using `qwen/qwen3.6-27b` and `openai/gpt-oss-20b` to extract category, severity indicators, and location facts without hallucinations.
- **Multilingual Speech-to-Text:** Browser voice input and phone audio transcribed via Groq Whisper (`whisper-large-v3-turbo`) and Deepgram Nova-2.
- **Domain Separation Guardrails:** Automatically separates municipal grievances from emergencies (routed to ERSS 112) and non-municipal matters (NALSA legal aid, National Consumer Helpline).
- **AI Resolution Verification:** Compares pre-repair complaint data against field proof photos submitted by municipal crews (`core/resolution_verifier.py`).

### Authority Command Center
- **Command Center Dashboard:** Real-time visibility into active grievances, priority distribution, department workloads, and SLA health.
- **Workflow State Management:** Full lifecycle progression (`ACKNOWLEDGED` $\rightarrow$ `ASSIGNED` $\rightarrow$ `WORK_STARTED` $\rightarrow$ `RESOLUTION_SUBMITTED`).
- **Field Evidence Capture:** Enforces crew notes and resolution photo upload upon work completion.
- **Automated SLA Engine:** Category and priority-driven countdown timers with deterministic multi-tier escalations.
- **Analytics & Geographic Hotspots:** Heatmap clusters grouping recurring civic issues by jurisdiction and risk intensity.
- **Multi-Admin Credentials:** Environment-driven authentication supporting multiple authority accounts.

---

## 2. Final Complaint Lifecycle

Every grievance transitions through deterministic lifecycle states managed in [`core/db.py`](file:///Users/aashishvarma/Desktop/civicresolve_ai_final/core/db.py):

```
                     ┌──────────────────┐
                     │       NEW        │
                     └─────────┬────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │   ACKNOWLEDGED   │
                     └─────────┬────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │     ASSIGNED     │◄──────────────┐
                     └─────────┬────────┘               │
                               │                        │
                               ▼                        │
                     ┌──────────────────┐               │
                     │   WORK_STARTED   │               │
                     └─────────┬────────┘               │
                               │                        │
                               ▼                        │ (Corrective
                     ┌──────────────────────┐           │  Workflow)
                     │ RESOLUTION_SUBMITTED │           │
                     └─────────┬────────────┘           │
                               │                        │
                               ▼                        │
                  ┌───────────────────────────┐         │
                  │  AI_VERIFICATION_PENDING  │         │
                  └────────────┬──────────────┘         │
                               │                        │
            ┌──────────────────┴──────────────────┐     │
            ▼                                     ▼     │
┌───────────────────────┐             ┌────────────────┴─┐
│ HUMAN_REVIEW_REQUIRED │             │     REOPENED     │
└───────────┬───────────┘             └──────────────────┘
            │                                     ▲
            ▼                                     │ (Citizen Rejects)
┌──────────────────────────┐                      │
│ RESOLVED_PENDING_CITIZEN ├──────────────────────┘
└───────────┬──────────────┘
            │ (Citizen Confirms)
            ▼
┌──────────────────────────┐
│          CLOSED          │
└──────────────────────────┘
```

### Alternative Domain States
- **`EMERGENCY_DISPATCHED`**: Assigned immediately when life-safety threats (fire, active crimes, severe casualties) are identified. Attached to ERSS 112 national emergency directives with an urgent 1-hour SLA.
- **`EXTERNALLY_ROUTED`**: Assigned when non-municipal grievances (consumer disputes, legal aid) are matched against verified national portals (e.g., NALSA, National Consumer Helpline).
- **`REJECTED`**: Administrative termination for invalid or out-of-scope submissions.

### The `REOPENED` Corrective Workflow
1. If the **AI Resolution Verifier** detects that an issue remains unaddressed despite field crew completion notes, or if the **Citizen rejects the resolution**, status transitions to `REOPENED`.
2. Reopened tickets maintain their complete historical audit log and allow authorities to re-assign or restart work without creating duplicate tickets.

---

## 3. Multi-Channel Intake Architecture

Whether submitted through the Web Form, Conversational AI Chat, or AI Voice Callbot, **all intake channels converge on the canonical backend endpoint: `POST /api/complaints`**.

```
  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
  │ Citizen Web    │     │ Conversational │     │ AI Phone Call  │
  │ Report Form    │     │ AI Chat Page   │     │ (Twilio Stream)│
  └───────┬────────┘     └───────┬────────┘     └───────┬────────┘
          │                      │                      │
          │ multipart/form-data  │ application/json     │ Callbot Client
          ▼                      ▼                      ▼
    ═════════════════════════════════════════════════════════════════
                 POST /api/complaints (FastAPI Backend)
    ═════════════════════════════════════════════════════════════════
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [Municipal Pipeline]             [Emergency/External]
       1. AI Multimodal Triage          1. National Directory Match
       2. Location Normalization        2. Official Portal Referral
       3. Duplicate Detection Engine    3. Emergency Escalation
       4. Deterministic Risk Engine
       5. SLA & Dept Dispatch
       6. SQLite Persistence
```

- **Backend Controlled Duplicate Detection:** The frontend and callbot never make independent duplicate decisions; the backend orchestrator guarantees uniform duplicate scoring and link registration across all channels.
- **Unified Ticket Schema:** Every channel yields identical data structures, risk parameters, and SLA deadlines.

---

## 4. Duplicate Detection Engine

Implemented in [`core/duplicates.py`](file:///Users/aashishvarma/Desktop/civicresolve_ai_final/core/duplicates.py) and coordinated by [`core/orchestrator.py`](file:///Users/aashishvarma/Desktop/civicresolve_ai_final/core/orchestrator.py), CivicResolve uses a deterministic weighted multi-factor scoring model:

$$\text{Duplicate Score} = (0.50 \times \text{GeoSim}) + (0.35 \times \text{TextSim}) + (0.15 \times \text{CatSim})$$

### Configured Weights & Thresholds
| Parameter | Setting | Description |
| :--- | :--- | :--- |
| **Geographic Similarity ($\text{GeoSim}$)** | **50% (0.50)** | Distance $\le 50\text{m} \rightarrow 1.0$; Linear decay from $50\text{m}$ to $300\text{m} \rightarrow 0.0$; $> 300\text{m} \rightarrow 0.0$. Text token fallback used if GPS is absent. |
| **Text Similarity ($\text{TextSim}$)** | **35% (0.35)** | Jaccard similarity across filtered grievance keywords (excluding common stopwords). |
| **Category Similarity ($\text{CatSim}$)** | **15% (0.15)** | $1.0$ for exact category match; $0.5$ if either is unknown; incompatible categories skipped. |
| **Detection Threshold** | **0.68** | Minimum combined score required to trigger duplicate linking. |
| **Proximity Override** | **$\ge 0.85$** | If $\text{GeoSim} \ge 0.90$ (within $75\text{m}$), same category, and $\text{TextSim} \ge 0.20$, score is boosted to $\ge 0.85$. |

### Duplicate Handling Rules
1. **Scope:** Only open/active municipal issues are evaluated (skips `CLOSED`, `REJECTED`, and non-municipal tickets).
2. **Parent-Child Link:** A detected duplicate does not create an isolated active ticket; it links to the primary parent issue and registers a record in `supporting_reports`.
3. **Volume-Based Priority Boost:** Increments `report_count` on the parent complaint, triggering automated re-calculation of the parent's **Civic Risk Score** (each additional citizen report increases risk by +4 points, up to +20).
4. **Audit Integrity:** Full citizen details, timestamps, and evidence from secondary reports are preserved in SQLite.
5. **Effective Ticket Returned:** The API returns the primary `complaint_id` with `duplicate_link_info` so the citizen can track the existing parent ticket.

---

## 5. Evidence System

CivicResolve supports multi-stage, non-destructive evidence collection:

- **Initial Evidence:** Citizen-submitted photos and GPS coordinates captured at time of filing.
- **Confirmed GPS Location:** Optional high-accuracy browser geolocation (`latitude`, `longitude`, `gps_accuracy_meters`).
- **Callbot SMS Evidence Link:** Generated dynamically during phone calls (`/evidence/{token}`), enabling mobile image capture via standard mobile browsers.
- **Resolution Proof Evidence:** Captured by municipal supervisors upon marking work completed.
- **Non-Destructive Storage:** Secondary report evidence and follow-up uploads are appended to the `evidence` table; original evidence is never overwritten.
- **Evidence is Never Mandatory:** A citizen without a camera or GPS can always register grievances via text or speech alone.

### Evidence Attachment Endpoint
```http
POST /api/complaints/{complaint_id}/evidence
Content-Type: multipart/form-data
```
- **Supported Image Formats:** `image/jpeg`, `image/png`, `image/webp`
- **Maximum File Size:** **8 MB** ($8 \times 1024 \times 1024$ bytes)
- **Optional Form Fields:** `image` (file), `latitude` (float), `longitude` (float), `gps_accuracy` (float), `location_confirmed` (boolean).

---

## 6. Callbot Architecture

The AI Voice Callbot provides natural, low-latency phone triage using Twilio Media Streams, Deepgram STT/TTS, and Groq LLM:

```
[Citizen Phone]
      │
      ▼ (Twilio Voice)
[Twilio Telecom Gateway]
      │
      ▼ (WebSocket Audio Stream: 8kHz μ-law)
[FastAPI Callbot: wss://<PUBLIC_HOST>/media-stream]
      │
      ├──► [Deepgram Nova-2 Live STT] ──► Real-time Transcripts
      │
      ├──► [CivicResolve CallAgent (Python + Groq)]
      │         ├── 1. Safety hazard evaluation
      │         ├── 2. Evidence permission inquiry
      │         │       ├── If YES ──► Send Twilio SMS Link (/evidence/{token})
      │         │       └── If NO  ──► Spoken landmark / location capture
      │         ├── 3. Structured grievance verification
      │         └── 4. Real-time POST /api/complaints submission
      │
      └──► [Deepgram Aura TTS] ──► Audio Packets (8kHz μ-law)
                │
                ▼ (WebSocket Response)
         [Twilio Caller]
```

### Callbot Conversation Logic
1. **Safety First:** Inquires about immediate dangers or hazards before proceeding.
2. **Evidence Permission:** Asks if the caller can provide photos via SMS.
   - *If YES:* Dispatches a secure one-time link (`/evidence/{token}`) via Twilio SMS.
   - *If NO:* Gracefully proceeds to capture verbal location landmarks.
3. **Backend Submission:** Submits the structured grievance directly to `POST /api/complaints`.
4. **Ticket Confirmation:** Reads out the registered Ticket ID to the caller.
5. **Browser Test Phone:** WebRTC testing interface available at `/test/browser-phone` (secured by `BROWSER_TEST_SECRET`).

---

## 7. Project Structure

```
civicresolve_ai_final/
├── backend/
│   ├── __init__.py
│   └── main.py                     # FastAPI backend application & API routing
├── core/
│   ├── __init__.py
│   ├── agent.py                    # Groq LLM multimodal entity extraction & triage
│   ├── config.py                   # Root environment loading & model settings
│   ├── db.py                       # SQLite schema, migrations & status transition rules
│   ├── duplicates.py               # Deterministic geographic & text duplicate engine
│   ├── escalation.py               # SLA breach escalation logging
│   ├── location.py                 # Haversine distance, landmark dictionary & geocoding
│   ├── orchestrator.py             # Master complaint processor & workflow coordinator
│   ├── resolution_verifier.py      # Multimodal AI resolution verifier & rule fallbacks
│   ├── risk.py                     # Deterministic Civic Risk Scoring engine
│   ├── routing.py                  # Municipal department mapping
│   ├── services.py                 # Non-municipal external directory (ERSS 112, NALSA)
│   ├── sla.py                      # SLA baseline hours matrix & live countdown logic
│   └── voice.py                    # Groq Whisper voice transcription handler
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── civicresolve.js     # Frontend API client
│   │   ├── components/             # Reusable UI widgets (HotspotMap, Badges, Modals)
│   │   ├── context/
│   │   │   └── ComplaintContext.jsx # Global client state
│   │   ├── pages/                  # Route views (Home, Report, Chat, Track, Authority)
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── callbot/
│   ├── app/
│   │   ├── agent.py                # Call conversation agent & Groq schema parser
│   │   ├── browser_phone.py        # Twilio Voice WebRTC browser testing endpoint
│   │   ├── call_state.py           # Per-call session state machine
│   │   ├── civicresolve_client.py  # HTTP client to core CivicResolve backend
│   │   ├── deepgram_stt.py         # Deepgram streaming STT client
│   │   ├── deepgram_tts.py         # Deepgram Aura streaming TTS client
│   │   ├── evidence_links.py       # Secure token generator for SMS evidence
│   │   ├── evidence_routes.py      # Mobile evidence upload UI & POST endpoints
│   │   ├── main.py                 # Callbot FastAPI service & Twilio media WebSocket
│   │   ├── router.py               # Intent router
│   │   └── sms_sender.py           # Twilio SMS dispatch utility
│   ├── requirements.txt            # Callbot dependencies
│   ├── runtime/                    # Generated tokens and link state
│   └── scripts/                    # Voice pipeline & unit test scripts
├── scripts/
│   └── clear_demo_data.py          # Database reset tool
├── tests/
│   ├── test_core.py                # Core engine unit tests
│   ├── test_e2e_workflow_actions.py # Authority action workflow tests
│   ├── test_resolution_workflow.py # AI resolution verification tests
│   └── test_voice_pipeline.py      # Audio upload & transcription tests
├── civicresolve.db                 # Local SQLite database (Runtime / Git-ignored)
├── requirements.txt                # Backend dependencies
├── .env.example                    # Root environment variable template
└── README.md                       # Master platform documentation
```

---

## 8. Technology Stack

- **Frontend:** React 18, Vite 5, Tailwind CSS, Lucide React icons.
- **Backend Service:** FastAPI, Uvicorn, Python 3.10+ (tested on Python 3.14), Pydantic v2.
- **Persistence:** SQLite with connection pooling, table schemas, and automated column migrations.
- **Artificial Intelligence:**
  - **LLM Reasoning & Extraction:** Groq API (`openai/gpt-oss-20b`).
  - **Multimodal Vision:** Groq API (`qwen/qwen3.6-27b`).
  - **Speech Recognition (STT):** Groq Whisper (`whisper-large-v3-turbo`) for browser voice, Deepgram Nova-2 for phone calls.
  - **Speech Synthesis (TTS):** Deepgram Aura for real-time telephony speech synthesis.
- **Telephony & Networking:** Twilio Voice, Twilio Media Streams (8kHz μ-law WebSocket), Twilio Programmable SMS, ngrok tunneling.

---

## 9. Prerequisites & System Requirements

- **Operating System:** macOS, Linux, or Windows (WSL2 recommended).
- **Python:** Python `3.10` to `3.14` installed (`python3 --version`).
- **Node.js:** Node.js `v18.x` or `v20.x`+ and npm (`node -v`, `npm -v`).
- **Git:** Git `2.x`+.
- **External Accounts & API Keys:**
  - [Groq Console](https://console.groq.com/) API Key (Required for AI Triage & Verification).
  - [Deepgram Console](https://console.deepgram.com/) API Key (Required for Callbot STT/TTS).
  - [Twilio Console](https://www.twilio.com/) Account SID, Auth Token & Phone Number (Required for Callbot).
  - [ngrok](https://ngrok.com/) Account & CLI (Required for local Twilio webhook testing).

---

## 10. Fresh Installation from GitHub

### Step 1: Clone Repository
```bash
git clone https://github.com/aashishvarma0708-ai/ai-agent-hackathon.git
cd ai-agent-hackathon
```

### Step 2: Set Up Backend Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Set Up Frontend Environment
```bash
cd frontend
npm install
cd ..
```

### Step 4: Set Up Callbot Environment
```bash
cd callbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

---

## 11. Environment Variables Configuration

Configure private `.env` files in each service directory using the templates below. **Never commit `.env` files to Git.**

### 1. Root Backend Environment: `.env`
Create `.env` in the root workspace directory:
```bash
cp .env.example .env
```
Fill in the configuration:
```env
# AI Models & Keys
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_TEXT_MODEL=openai/gpt-oss-20b
GROQ_VISION_MODEL=qwen/qwen3.6-27b
GROQ_STT_MODEL=whisper-large-v3-turbo

# Local Database (Optional override, defaults to civicresolve.db)
CIVICRESOLVE_DB=civicresolve.db

# Callbot Phone Reference (Optional)
VITE_CALLBOT_NUMBER=+1234567890

# Authority Login Credentials (Constant-time authentication)
ADMIN_EMAIL=admin@civicresolve.local
ADMIN_PASSWORD=your_secure_admin_password
ADMIN_EMAIL_2=civicresolve.admin2@local
ADMIN_PASSWORD_2=your_second_admin_password
```

### 2. Frontend Environment: `frontend/.env`
Create `frontend/.env`:
```bash
cp frontend/.env.example frontend/.env
```
```env
# Backend API Base URL
VITE_API_URL=http://127.0.0.1:8000

# Callbot Number Displayed on UI (Optional)
VITE_CALLBOT_NUMBER=+1234567890
```

### 3. Callbot Environment: `callbot/.env`
Create `callbot/.env`:
```bash
cp callbot/.env.example callbot/.env
```
```env
# Twilio Telephony Credentials
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

# Twilio Client (For browser phone testing)
TWILIO_API_KEY_SID=
TWILIO_API_KEY_SECRET=
TWILIO_TWIML_APP_SID=

# Browser Test Phone Security
BROWSER_TEST_IDENTITY=civicresolve_mac_test
BROWSER_TEST_SECRET=your_browser_test_secret_here

# Deepgram Voice AI
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Groq LLM for Call Conversation
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

# Public ngrok / Server Host (Omit http:// or wss://, e.g. abc123.ngrok-free.app)
PUBLIC_HOST=your-ngrok-subdomain.ngrok-free.app

# Backend Connectivity
CIVICRESOLVE_API_URL=http://127.0.0.1:8000
PUBLIC_APP_URL=http://localhost:5173
```

---

## 12. Local Execution Commands

Open separate terminal windows for each service:

### Terminal 1: Core Backend (Port 8000)
```bash
cd ~/Desktop/civicresolve_ai_final
source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Health Check:* Open `http://127.0.0.1:8000/api/health`

### Terminal 2: React Frontend (Port 5173)
```bash
cd ~/Desktop/civicresolve_ai_final/frontend
npm run dev
```
*Web Application:* Open `http://localhost:5173`

### Terminal 3: AI Callbot (Port 9000)
```bash
cd ~/Desktop/civicresolve_ai_final/callbot
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```
*Callbot Health Check:* Open `http://127.0.0.1:9000/health`

### Terminal 4: ngrok Tunnel (For Telephony Testing)
```bash
ngrok http http://127.0.0.1:9000
```
Copy the generated Forwarding HTTPS URL (e.g., `https://abc-123.ngrok-free.app`).

---

## 13. Twilio & ngrok Setup (Callbot Local Development)

To route inbound voice calls to your local Callbot:

1. **Start Backend, Callbot, and ngrok** as described above.
2. Copy the active ngrok public hostname (e.g., `abc-123.ngrok-free.app`).
3. Update `PUBLIC_HOST` in `callbot/.env`:
   ```env
   PUBLIC_HOST=abc-123.ngrok-free.app
   ```
4. Log in to the **[Twilio Console](https://console.twilio.com/)**.
5. Navigate to **Phone Numbers** $\rightarrow$ **Manage** $\rightarrow$ **Active numbers** $\rightarrow$ Click your Twilio Number.
6. Under **Voice & Fax** $\rightarrow$ **A CALL COMES IN**:
   - Select **Webhook**
   - URL: `https://<YOUR_NGROK_HOST>/voice`
   - HTTP Method: **HTTP POST**
7. Click **Save Configuration**.
8. Call your Twilio Phone Number from any mobile device to interact with the AI assistant.

---

## 14. Authority & Admin Authentication

CivicResolve supports multi-admin authentication configured via environment variables:

- **Primary Admin:** Configured via `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
- **Secondary Admin:** Configured via `ADMIN_EMAIL_2` and `ADMIN_PASSWORD_2`.

### Authentication Rules
- **Constant-Time Verification:** All credentials are mathematically compared using Python's `secrets.compare_digest` to prevent timing attacks. Plain `==` operators are never used.
- **Unified Login UI:** Both administrative accounts use the same login form on the Authority Dashboard page.
- **Incomplete Pairs Ignored:** If only an email or password is configured without its counterpart, that incomplete pair is discarded.
- **HTTP 503 Fallback:** If no valid admin pairs exist in `.env`, the endpoint safely returns `503 Service Unavailable`.
- **Credential Privacy:** Passwords and environment secrets are never returned in JSON payloads or printed to console logs.

> [!NOTE]
> **Demonstration Architecture Note:** Current expo authentication verifies credentials and issues randomized session tokens for controlled demonstrations. Production deployments should enforce cryptographic JWT validation middleware on all protected `/api/admin/*` endpoints.

---

## 15. SQLite Database Management

CivicResolve uses SQLite (`civicresolve.db`) for lightweight, zero-configuration local persistence:

- **Schema Management:** Handled automatically on application startup via `init_db()` in [`core/db.py`](file:///Users/aashishvarma/Desktop/civicresolve_ai_final/core/db.py), including safe column migrations.
- **Data Tables:**
  - `complaints`: Primary grievance records, SLA deadlines, risk metrics, and triage traces.
  - `status_history`: Complete audit trail of every status transition and authority note.
  - `escalations`: Log of automated SLA breach escalations.
  - `evidence`: Multimodal media metadata, confirmed GPS points, and resolution proof.
  - `supporting_reports`: Secondary duplicate citizen reports linked to primary issues.

### Clearing Demo Data (Fresh Reset)
To reset database records without dropping table schemas:
```bash
source .venv/bin/activate
python scripts/clear_demo_data.py
```

---

## 16. Important API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health check, version, and demo mode indicator. |
| `POST` | `/api/admin/login` | Authority authentication with constant-time verification. |
| `POST` | `/api/complaints` | Canonical intake endpoint (supports JSON & multipart with image). |
| `GET` | `/api/complaints/{id}` | Fetches detailed complaint object, history, evidence, and SLA status. |
| `POST` | `/api/complaints/{id}/evidence` | Attaches citizen photos (up to 8MB) and confirmed GPS coordinates. |
| `POST` | `/api/complaints/{id}/citizen-confirmation` | Citizen closure confirmation or rejection/reopen request. |
| `GET` | `/api/admin/complaints` | Retrieves all complaints for the Authority Command Center. |
| `PUT` | `/api/complaints/{id}/status` | Updates complaint status according to strict transition graph. |
| `POST` | `/api/admin/complaints/{id}/complete-work` | Submits field completion note and triggers AI resolution verification. |
| `POST` | `/api/admin/complaints/{id}/verify-resolution`| Manual / re-check endpoint for AI resolution verifier. |
| `POST` | `/api/admin/complaints/{id}/simulate-time` | Virtual time advancement simulator for SLA breach testing. |
| `POST` | `/api/admin/run-sla-check` | Batch evaluation of all open complaints for SLA escalations. |
| `GET` | `/api/admin/analytics` | Aggregated municipal KPIs, department stats, and hotspot clusters. |
| `POST` | `/api/voice/transcribe` | Groq Whisper speech-to-text transcription endpoint. |

---

## 17. Testing & Quality Assurance

Run the automated test suite and compilation checks across all modules:

### 1. Backend Automated Tests (Pytest)
```bash
cd ~/Desktop/civicresolve_ai_final
source .venv/bin/activate
PYTHONPATH=. python -m pytest tests -q
```
*Expected Baseline Result:* `15 passed in ~50s`

### 2. Python Compilation Check
```bash
python -m py_compile backend/main.py core/*.py
```
*(No output indicates successful syntax validation)*

### 3. Frontend Production Build Check
```bash
cd frontend
npm run build
```
*(Confirms zero JSX or bundler errors, output saved to `dist/`)*

### 4. Callbot Compilation Check
```bash
cd ../callbot
source .venv/bin/activate
python -m py_compile app/*.py
```
*(No output indicates successful syntax validation)*

---

## 18. Full Manual Acceptance Test Checklist

### 1. Website Navigation
- [ ] Verify **Home**, **Report Issue**, **AI Chat**, **Track Complaint**, and **Authority Command Center** load properly.
- [ ] Confirm active hotspot map and statistics render on Home.

### 2. Web Form Intake
- [ ] Submit a new complaint: *"Large pothole outside school gate, two bikes slipped"*.
- [ ] Upload a test JPEG/PNG photo and capture browser GPS.
- [ ] Verify Ticket ID generation (`CR-YYMMDD-XXXX`) and immediate routing to Roads & Infrastructure Department.
- [ ] Confirm Civic Risk Score is classified as `HIGH` or `CRITICAL` due to school proximity.

### 3. Duplicate Detection Verification
- [ ] Submit a second complaint with similar text and location within 300 meters.
- [ ] Verify the system identifies the duplicate, links it as a supporting report, increments `report_count`, and returns the existing primary Ticket ID.

### 4. Conversational AI Chat Intake
- [ ] Open AI Chat and type a civic issue (*"Streetlight pole sparking near market"*).
- [ ] Follow interactive clarification prompts and verify complaint registration.
- [ ] Test emergency phrase (*"Someone is attacking a person near the bridge"*); verify immediate emergency referral to ERSS 112.

### 5. Callbot Telephony Flow
- [ ] Call the Twilio number; verify Deepgram STT transcription.
- [ ] Answer safety question; confirm evidence permission inquiry.
- [ ] Request SMS link $\rightarrow$ verify Twilio SMS receipt $\rightarrow$ open `/evidence/{token}` $\rightarrow$ upload photo.
- [ ] Verify complaint appears in Authority Dashboard with attached evidence.

### 6. Authority Lifecycle & AI Verification
- [ ] Log in via Authority Dashboard (`ADMIN_EMAIL` / `ADMIN_PASSWORD`).
- [ ] Transition ticket: `NEW` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `ASSIGNED` $\rightarrow$ `WORK_STARTED`.
- [ ] Click **Complete Work**; enter supervisor notes and attach a repair photo.
- [ ] Verify AI Resolution Verifier evaluates evidence and transitions status to `RESOLVED_PENDING_CITIZEN`.
- [ ] Open Citizen Tracking page and click **Confirm Resolution** $\rightarrow$ verify status becomes `CLOSED`.

---

## 19. Common Troubleshooting & Recovery

### 1. Port Conflicts (`8000` or `9000` already in use)
Identify and terminate lingering background processes:
```bash
# Check port 8000 (Backend)
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill -9 <PID>

# Check port 9000 (Callbot)
lsof -nP -iTCP:9000 -sTCP:LISTEN
kill -9 <PID>
```

### 2. Pytest using Anaconda or Wrong Python Environment
Always enforce the project's virtual environment and Python path:
```bash
source .venv/bin/activate
PYTHONPATH=. python -m pytest tests -q
```

### 3. Callbot Fails to Connect / Silent Call
- **Stale ngrok URL:** Ensure `PUBLIC_HOST` in `callbot/.env` matches your active ngrok domain without `https://`.
- **Backend Unreachable:** Verify Core Backend is running on `http://127.0.0.1:8000`.
- **Missing API Keys:** Verify `DEEPGRAM_API_KEY` and `GROQ_API_KEY` in `callbot/.env`.

### 4. Frontend Cannot Connect to Backend
- Confirm `VITE_API_URL=http://127.0.0.1:8000` in `frontend/.env`.
- Restart the Vite development server (`npm run dev`).

---

## 20. Production & Expo Deployment Architecture

```
                      ┌─────────────────────────┐
                      │    Internet / Users     │
                      └────────────┬────────────┘
                                   │ HTTPS
                                   ▼
                      ┌─────────────────────────┐
                      │  React SPA (Vite / CDN) │
                      └────────────┬────────────┘
                                   │ API Requests
                                   ▼
                      ┌─────────────────────────┐
                      │ FastAPI Backend Service │
                      └────────────┬────────────┘
                                   │ Local Read/Write
                                   ▼
                      ┌─────────────────────────┐
                      │   Persistent Disk /     │
                      │      SQLite DB          │
                      └─────────────────────────┘

   ┌───────────────────┐               ┌─────────────────────────┐
   │  Twilio Telecom   │◄─────────────►│ FastAPI Callbot Service │
   │  (Voice & SMS)    │  WSS / HTTPS  │   (Deepgram + Groq)     │
   └───────────────────┘               └────────────┬────────────┘
                                                    │ REST API
                                                    ▼
                                       [FastAPI Backend Service]
```

### Key Production Requirements
1. **Persistent Volume for SQLite:** Ephemeral containers (like basic serverless functions) will reset SQLite data on restart. Mount a persistent volume for `civicresolve.db`.
2. **Reverse Proxy & SSL:** Terminate TLS using Nginx or Caddy with valid SSL certificates for HTTPS and WSS endpoints.
3. **Environment Security:** Configure production secrets directly in server environment managers—never push `.env` files to source repositories.

---

## 21. Security Checklist

- [x] **Git Isolation:** `.env`, `.env.local`, `.admin_login.txt`, and `civicresolve.db` are strictly git-ignored.
- [x] **No Hardcoded Secrets:** API keys and admin credentials exist solely in runtime environment configurations.
- [x] **Timing-Attack Protection:** Admin authentication utilizes constant-time `secrets.compare_digest`.
- [x] **Safe Media Validation:** Evidence endpoint enforces file size bounds ($\le 8\text{MB}$) and MIME whitelisting (`image/jpeg`, `image/png`, `image/webp`).
- [x] **Token Randomization:** Session tokens use cryptographically secure entropy (`secrets.token_hex(16)`).
- [x] **Credential Rotation:** Rotate development Twilio, Groq, and Deepgram tokens prior to public expo presentations.

---

## 22. Backup & Disaster Recovery

CivicResolve maintains two complementary recovery layers:

1. **Git Source Code:** Version-controlled application code, deterministic rules, tests, and static assets.
2. **Private Configuration & Database Archive:** Local database (`civicresolve.db`) and `.env` files.

### Creating a Safe Project Archive
To generate a clean, portable backup excluding virtual environments and build artifacts:
```bash
cd ~/Desktop/civicresolve_ai_final
tar --exclude='.venv' \
    --exclude='callbot/.venv' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/dist' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    -czvf ../civicresolve_ai_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

---

## 23. Final Expo Startup Checklist

Follow this quick sequence to bring the entire platform live for presentations:

1. **Activate Backend:** `source .venv/bin/activate && python -m uvicorn backend.main:app --port 8000`
2. **Activate Frontend:** `cd frontend && npm run dev`
3. **Activate Callbot:** `cd callbot && source .venv/bin/activate && python -m uvicorn app.main:app --port 9000`
4. **Launch ngrok:** `ngrok http http://127.0.0.1:9000` $\rightarrow$ update `PUBLIC_HOST` in `callbot/.env`.
5. **Verify Health:** Visit `http://127.0.0.1:8000/api/health` and `http://127.0.0.1:9000/health`.
6. **Open Dashboard:** Open `http://localhost:5173` in a web browser.
7. **Perform Demo Intake:** File one test complaint via Web Form or AI Chat.
8. **Demonstrate Telephony:** Place one live call to the Twilio number and upload evidence via SMS link.
9. **Show Authority Resolution:** Complete work in Authority Dashboard and demonstrate AI Resolution Verification.
10. **Confirm Resolution:** Confirm resolution from Citizen Tracking page to showcase closed-loop accountability.

---

## 24. Current Verification Status

- **Automated Tests:** `15 / 15` tests passing in `tests/` (`test_core.py`, `test_e2e_workflow_actions.py`, `test_resolution_workflow.py`, `test_voice_pipeline.py`).
- **Frontend Build:** Production bundle compiled successfully with Vite 5.
- **Python Compilation:** Zero syntax or import errors across all backend and callbot modules.
- **Database Engine:** SQLite 3 with automatic schema initialization and non-destructive column migrations.
- **Multi-Admin Authentication:** Constant-time verification active for primary and secondary administrators.

---

*CivicResolve AI — One place to report. Intelligence to route. Accountability until resolution.*
