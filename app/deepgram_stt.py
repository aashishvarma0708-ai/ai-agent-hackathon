import os
import json
import time
import asyncio

from dotenv import load_dotenv
from websockets.asyncio.client import connect


load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()

DEEPGRAM_STT_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-3"
    "&language=multi"
    "&encoding=mulaw"
    "&sample_rate=8000"
    "&channels=1"
    "&interim_results=true"
    "&endpointing=300"
    "&utterance_end_ms=1000"
    "&vad_events=true"
    "&smart_format=true"
    "&punctuate=true"
)


class DeepgramSTT:
    def __init__(self):
        self.websocket = None
        self.send_lock = asyncio.Lock()
        self.keepalive_task = None
        self.last_audio_time = None
        self.closing = False

    async def connect(self):
        if not DEEPGRAM_API_KEY:
            raise RuntimeError(
                "DEEPGRAM_API_KEY is missing from .env"
            )

        if self.websocket is not None:
            return

        print("🧠 Connecting to Deepgram STT...")

        self.websocket = await connect(
            DEEPGRAM_STT_URL,
            additional_headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}"
            },
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
        )

        self.closing = False
        self.last_audio_time = time.monotonic()
        self.keepalive_task = asyncio.create_task(
            self._keepalive_loop()
        )

        print("✅ Deepgram STT connected")

    async def _keepalive_loop(self):
        try:
            while not self.closing:
                await asyncio.sleep(3.0)

                if self.websocket is None:
                    break

                idle_for = (
                    time.monotonic() - self.last_audio_time
                    if self.last_audio_time is not None
                    else 999.0
                )

                if idle_for >= 3.0:
                    async with self.send_lock:
                        if self.websocket is not None and not self.closing:
                            await self.websocket.send(
                                json.dumps({"type": "KeepAlive"})
                            )

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            if not self.closing:
                print(
                    f"⚠️ Deepgram STT keepalive error: {exc}"
                )

    async def send_audio(self, audio_bytes: bytes):
        if not audio_bytes:
            return

        if self.websocket is None:
            raise RuntimeError(
                "Deepgram STT websocket is not connected"
            )

        async with self.send_lock:
            if self.websocket is None or self.closing:
                return
            await self.websocket.send(audio_bytes)

        self.last_audio_time = time.monotonic()

    async def receive(self):
        if self.websocket is None:
            raise RuntimeError(
                "Deepgram STT websocket is not connected"
            )

        async for message in self.websocket:
            if isinstance(message, bytes):
                continue

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            message_type = data.get("type")

            if message_type == "SpeechStarted":
                yield {
                    "type": "speech_started",
                    "timestamp": data.get("timestamp"),
                }
                continue

            if message_type == "UtteranceEnd":
                yield {
                    "type": "utterance_end",
                    "last_word_end": data.get("last_word_end"),
                }
                continue

            if message_type == "Error":
                raise RuntimeError(
                    f"Deepgram STT error: {data}"
                )

            if message_type != "Results":
                continue

            alternatives = (
                data.get("channel", {})
                .get("alternatives", [])
            )

            if not alternatives:
                continue

            transcript = alternatives[0].get(
                "transcript",
                "",
            ).strip()

            if not transcript:
                continue

            yield {
                "type": "transcript",
                "transcript": transcript,
                "is_final": data.get("is_final", False),
                "speech_final": data.get("speech_final", False),
            }

    async def finalize(self):
        if self.websocket is None or self.closing:
            return

        async with self.send_lock:
            if self.websocket is not None and not self.closing:
                await self.websocket.send(
                    json.dumps({"type": "Finalize"})
                )

    async def close(self):
        if self.websocket is None:
            return

        self.closing = True

        if self.keepalive_task is not None:
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
            self.keepalive_task = None

        websocket = self.websocket
        self.websocket = None

        try:
            async with self.send_lock:
                await websocket.send(
                    json.dumps({"type": "CloseStream"})
                )
        except Exception:
            pass

        try:
            await websocket.close()
        except Exception:
            pass

        self.last_audio_time = None
        self.closing = False

        print("🛑 Deepgram STT closed")
