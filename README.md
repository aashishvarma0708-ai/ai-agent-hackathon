# CivicResolve AI — V0.1

Hackathon MVP for intelligent civic complaint intake, public-service triage, municipal routing, risk scoring, voice transcription, tracking, and an authority dashboard.

## What works in V0.1

- Web/text complaint intake
- Image + text complaint understanding with Groq vision
- Browser voice recording with Streamlit
- Multilingual speech-to-text with Groq Whisper
- Public-service triage:
  - Municipal civic
  - Emergency / police / fire / medical
  - Legal
  - Consumer
  - Other / unknown
- Verified national fallback directory for external public services
- Deterministic municipal routing
- Deterministic Civic Risk Score
- Complaint ID generation
- SQLite persistence
- Complaint tracking
- Authority dashboard
- Agent activity log
- Offline keyword fallback if the Groq call fails

## Run on your Mac

```bash
cd ~/Desktop
unzip civicresolve_ai_v01.zip
cd civicresolve_ai_v01

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cp .env.example .env
```

Open `.env` and replace:

```text
GROQ_API_KEY=your_groq_api_key_here
```

Then run:

```bash
python -m streamlit run app/main.py
```

## Recommended demo

1. Open **Report Issue**
2. Submit: "Large pothole outside school, two bikes nearly crashed"
3. Add location and optionally a pothole image
4. Show:
   - AI triage
   - category
   - risk score
   - routing department
   - ticket ID
   - agent activity
5. Try **Voice Complaint**
6. Say the same complaint naturally
7. Show that voice becomes the same unified complaint object
8. Open **Authority Dashboard**
9. Update status and show history
10. Try an external case such as:
    - "Someone is threatening me"
    - "I need legal aid"
    - "I want to complain about an online seller"

## Architecture principle

AI interprets. Python enforces. Tools act.

The LLM extracts structured facts. Python decides IDs, risk score, SLA, routing lookup, database writes, and state transitions.

## Next upgrades

- Real geocoding + jurisdiction
- Geographic duplicate detection
- Dynamic priority from repeated reports
- SLA timer and auto-escalation
- Before/after image resolution verification
- Civic hotspot map
- Citizen confirmation loop
- Telugu/Hindi UI labels
- Real phone-call adapter as a future extension
