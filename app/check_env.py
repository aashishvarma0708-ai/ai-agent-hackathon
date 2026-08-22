import os
from dotenv import load_dotenv

load_dotenv()

keys = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "DEEPGRAM_API_KEY",
    "GROQ_API_KEY",
]

for key in keys:
    value = os.getenv(key)

    if value:
        print(f"✅ {key}: loaded")
    else:
        print(f"❌ {key}: missing")

public_host = os.getenv("PUBLIC_HOST")

if public_host:
    print("✅ PUBLIC_HOST: loaded")
else:
    print("ℹ️ PUBLIC_HOST: not set yet — expected at Stage 4")
