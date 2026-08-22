import os
import json

from dotenv import load_dotenv
from websockets.asyncio.client import connect


load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

DEEPGRAM_STT_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3"
    "&language=multi"
    "&encoding=mulaw"
    "&sample_rate=8000"
    "&channels=1"
    "&interim_results=true"
    "&endpointing=150"
    "&vad_events=true"
    "&smart_format=true"
)


class DeepgramSTT:
    def __init__(self):
        self.websocket = None

    async def connect(self):
        if not DEEPGRAM_API_KEY:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is missing from .env"
            )

        print("🧠 Connecting to Deepgram STT...")

        self.websocket = await connect(
            DEEPGRAM_STT_URL,
            additional_headers={
                "Authorization":
                    f"Token {DEEPGRAM_API_KEY}"
            },
        )

        print("✅ Deepgram STT connected")

    async def send_audio(self, audio_bytes: bytes):
        if self.websocket is None:
            raise RuntimeError(
                "Deepgram websocket is not connected"
            )

        await self.websocket.send(audio_bytes)

    async def receive(self):
        if self.websocket is None:
            raise RuntimeError(
                "Deepgram websocket is not connected"
            )

        async for message in self.websocket:
            if isinstance(message, bytes):
                continue

            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "Results":
                alternatives = (
                    data.get("channel", {})
                    .get("alternatives", [])
                )

                if not alternatives:
                    continue

                transcript = alternatives[0].get(
                    "transcript",
                    ""
                ).strip()

                if not transcript:
                    continue

                is_final = data.get(
                    "is_final",
                    False
                )

                speech_final = data.get(
                    "speech_final",
                    False
                )

                yield {
                    "transcript": transcript,
                    "is_final": is_final,
                    "speech_final": speech_final,
                }

    async def finalize(self):
        if self.websocket is not None:
            await self.websocket.send(
                json.dumps({
                    "type": "Finalize"
                })
            )

    async def close(self):
        if self.websocket is not None:

            try:
                await self.websocket.send(
                    json.dumps({
                        "type": "CloseStream"
                    })
                )
            except Exception:
                pass

            await self.websocket.close()

            self.websocket = None

            print("🛑 Deepgram STT closed")
