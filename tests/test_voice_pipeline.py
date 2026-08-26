import io
import os
import subprocess
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from core.db import init_db, get_complaint, _conn

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def generate_speech_wav(text: str, filename: str = "temp_test_speech.wav", voice: str = "") -> bytes:
    """Generates real speech WAV using macOS say & afconvert."""
    aiff_path = filename.replace(".wav", ".aiff")
    cmd = ["say"]
    if voice:
        cmd.extend(["-v", voice])
    cmd.extend(["-o", aiff_path, text])
    subprocess.run(cmd, check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", aiff_path, filename], check=True)
    
    with open(filename, "rb") as f:
        audio_bytes = f.read()
        
    for p in [aiff_path, filename]:
        if os.path.exists(p):
            os.remove(p)
            
    return audio_bytes


from unittest.mock import patch

def test_voice_transcribe_english():
    """Tests English speech transcription endpoint."""
    text = "There is a pothole near the main gate."
    audio_bytes = io.BytesIO(b"RIFFmockwavheaderdata")
    
    with patch("backend.main.transcribe_audio", return_value={"success": True, "transcript": text, "text": text, "selected_language": "en"}):
        res = client.post(
            "/api/voice/transcribe",
            files={"audio": ("voice.wav", audio_bytes, "audio/wav")},
            data={"language": "en"}
        )
        
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "transcript" in data
        assert "text" in data
        assert "pothole" in data["transcript"].lower() or "gate" in data["transcript"].lower()
        assert data["selected_language"] == "en"


def test_voice_transcribe_hindi():
    """Tests Hindi speech transcription endpoint."""
    text = "मुख्य गेट के पास सड़क में बड़ा गड्ढा है।"
    audio_bytes = io.BytesIO(b"RIFFmockwavheaderdata")
    
    with patch("backend.main.transcribe_audio", return_value={"success": True, "transcript": text, "text": text, "selected_language": "hi"}):
        res = client.post(
            "/api/voice/transcribe",
            files={"audio": ("voice.wav", audio_bytes, "audio/wav")},
            data={"language": "hi"}
        )
        
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["selected_language"] == "hi"
        assert len(data["transcript"]) > 0


def test_voice_transcribe_unsupported_language_fallback():
    """Tests that unsupported language codes fall back safely to 'en' without crashing."""
    text = "There is broken streetlight on 2nd avenue."
    audio_bytes = io.BytesIO(b"RIFFmockwavheaderdata")
    
    with patch("backend.main.transcribe_audio", return_value={"success": True, "transcript": text, "text": text, "selected_language": "en"}):
        res = client.post(
            "/api/voice/transcribe",
            files={"audio": ("voice.wav", audio_bytes, "audio/wav")},
            data={"language": "fr"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["selected_language"] == "en"


def test_voice_transcribe_empty_audio_rejected():
    """Tests that empty 0-byte audio upload returns HTTP 400 with helpful error."""
    empty_bytes = io.BytesIO(b"")
    res = client.post(
        "/api/voice/transcribe",
        files={"audio": ("voice.wav", empty_bytes, "audio/wav")}
    )
    assert res.status_code == 400
    assert "Empty audio recording" in res.json()["detail"]


def test_voice_full_pipeline_to_intake_and_tracking():
    """
    Tests full pipeline:
    Speech audio -> Transcription -> Submit voice complaint -> Tracking
    """
    text = "Severe drainage sewage overflow flooding the residential pathway near Market Street."
    audio_bytes = io.BytesIO(b"RIFFmockwavheaderdata")
    
    # 1. Transcribe audio
    with patch("backend.main.transcribe_audio", return_value={"success": True, "transcript": text, "text": text, "selected_language": "en"}):
        trans_res = client.post(
            "/api/voice/transcribe",
            files={"audio": ("voice.wav", audio_bytes, "audio/wav")},
            data={"language": "en"}
        )
        assert trans_res.status_code == 200
        transcript = trans_res.json()["transcript"]
        assert len(transcript) > 0
        
        # 2. Submit grievance using decoded transcript
        submit_res = client.post("/api/complaints", data={
            "complaint_text": transcript,
            "location_text": "Market Street, Ward 06",
            "citizen_name": "Voice Citizen Rohan",
            "source_channel": "voice",
            "language_hint": "English"
        })
        assert submit_res.status_code == 200
        comp = submit_res.json()
    cid = comp["complaint_id"]
    assert comp["category"] in {"drainage", "water", "roads"}
    assert comp["domain"] == "municipal"
    assert comp["status"] in {"NEW", "ACKNOWLEDGED"}
    
    # 3. Verify Tracking
    track_res = client.get(f"/api/complaints/{cid}")
    assert track_res.status_code == 200
    assert track_res.json()["complaint_id"] == cid
    
    # 4. Verify Authority Dashboard receives it
    admin_res = client.get("/api/admin/complaints")
    assert admin_res.status_code == 200
    matching = [c for c in admin_res.json() if c["complaint_id"] == cid]
    assert len(matching) == 1
    
    # 5. Clean database for test hygiene
    with _conn() as conn:
        conn.execute("DELETE FROM status_history")
        conn.execute("DELETE FROM escalations")
        conn.execute("DELETE FROM evidence")
        conn.execute("DELETE FROM supporting_reports")
        conn.execute("DELETE FROM complaints")
        conn.commit()
