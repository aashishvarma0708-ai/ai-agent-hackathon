import os
import json
import asyncio

from dotenv import load_dotenv
from websockets.asyncio.client import connect


load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()
DEEPGRAM_TTS_MODEL = os.getenv(
    "DEEPGRAM_TTS_MODEL",
    "flux-alexis-en",
).strip()

DEEPGRAM_TTS_URL = (
    "wss://api.deepgram.com/v2/speak"
    f"?model={DEEPGRAM_TTS_MODEL}"
    "&encoding=mulaw"
    "&sample_rate=8000"
)


class DeepgramTTS:
    def __init__(self):
        self.websocket = None
        self.turn_lock = asyncio.Lock()
        self.connection_lock = asyncio.Lock()
        self.closing = False

    async def connect(self):
        async with self.connection_lock:
            if self.websocket is not None:
                return

            if not DEEPGRAM_API_KEY:
                raise RuntimeError(
                    "DEEPGRAM_API_KEY is missing from .env"
                )

            print(
                f"🔊 Connecting to Deepgram TTS "
                f"({DEEPGRAM_TTS_MODEL})..."
            )

            self.websocket = await connect(
                DEEPGRAM_TTS_URL,
                additional_headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}"
                },
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
            )

            self.closing = False

            print("✅ Deepgram TTS connected")

    async def stream_synthesize(self, text: str):
        text = (text or "").strip()

        if not text:
            return

        await self.connect()

        async with self.turn_lock:
            websocket = self.websocket

            if websocket is None:
                raise RuntimeError(
                    "Deepgram TTS is not connected"
                )

            await websocket.send(
                json.dumps({
                    "type": "Speak",
                    "text": text,
                })
            )

            await websocket.send(
                json.dumps({
                    "type": "Flush",
                })
            )

            while True:
                message = await websocket.recv()

                if isinstance(message, bytes):
                    if message:
                        yield message
                    continue

                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue

                message_type = data.get("type")

                if message_type == "Error":
                    raise RuntimeError(
                        f"Deepgram TTS error: {data}"
                    )

                if message_type == "Warning":
                    print(
                        f"⚠️ Deepgram TTS warning: {data}"
                    )
                    continue

                # SpeechMetadata is the end-of-turn signal for
                # Flux TTS. All binary audio for this turn has
                # already arrived before this event.
                if message_type == "SpeechMetadata":
                    break

    async def synthesize(self, text: str) -> bytes:
        chunks = []

        async for chunk in self.stream_synthesize(text):
            chunks.append(chunk)

        return b"".join(chunks)

    async def abort_and_reconnect(self):
        """
        Hard-reset TTS after barge-in.

        Twilio's clear message stops buffered call playback.
        This method separately stops any in-progress Deepgram
        synthesis so old audio can't leak into the next turn.
        """
        async with self.connection_lock:
            websocket = self.websocket
            self.websocket = None

            if websocket is not None:
                try:
                    await websocket.close()
                except Exception:
                    pass

        await self.connect()

    async def close(self):
        async with self.connection_lock:
            websocket = self.websocket
            self.websocket = None

            if websocket is None:
                return

            self.closing = True

            try:
                await websocket.send(
                    json.dumps({"type": "Close"})
                )
            except Exception:
                pass

            try:
                await websocket.close()
            except Exception:
                pass

            self.closing = False

        print("🛑 Deepgram TTS closed")
