import os
import json

from dotenv import load_dotenv
from websockets.asyncio.client import connect


load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

DEEPGRAM_TTS_URL = (
    "wss://api.deepgram.com/v2/speak"
    "?model=flux-alexis-en"
    "&encoding=mulaw"
    "&sample_rate=8000"
)


class DeepgramTTS:

    def __init__(self):
        self.websocket = None

    async def connect(self):

        if not DEEPGRAM_API_KEY:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is missing from .env"
            )

        print("🔊 Connecting to Deepgram TTS...")

        self.websocket = await connect(
            DEEPGRAM_TTS_URL,
            additional_headers={
                "Authorization":
                    f"Token {DEEPGRAM_API_KEY}"
            },
        )

        print("✅ Deepgram TTS connected")

    async def synthesize(self, text: str):

        if self.websocket is None:
            raise RuntimeError(
                "Deepgram TTS is not connected"
            )

        if not text.strip():
            return b""

        await self.websocket.send(
            json.dumps({
                "type": "Speak",
                "text": text
            })
        )

        await self.websocket.send(
            json.dumps({
                "type": "Flush"
            })
        )

        audio_chunks = []

        while True:

            message = await self.websocket.recv()

            if isinstance(message, bytes):
                audio_chunks.append(message)
                continue

            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "Error":
                raise RuntimeError(
                    f"Deepgram TTS error: {data}"
                )

            if message_type == "SpeechMetadata":
                break

        return b"".join(audio_chunks)

    async def stream_synthesize(self, text: str):

        if self.websocket is None:
            raise RuntimeError(
                "Deepgram TTS is not connected"
            )

        if not text.strip():
            return

        await self.websocket.send(
            json.dumps({
                "type": "Speak",
                "text": text
            })
        )

        await self.websocket.send(
            json.dumps({
                "type": "Flush"
            })
        )

        while True:

            message = await self.websocket.recv()

            if isinstance(message, bytes):
                yield message
                continue

            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "Error":
                raise RuntimeError(
                    f"Deepgram TTS error: {data}"
                )

            if message_type == "SpeechMetadata":
                break

    async def close(self):

        if self.websocket is None:
            return

        try:
            await self.websocket.send(
                json.dumps({
                    "type": "Close"
                })
            )
        except Exception:
            pass

        try:
            await self.websocket.close()
        except Exception:
            pass

        self.websocket = None

        print("🛑 Deepgram TTS closed")
