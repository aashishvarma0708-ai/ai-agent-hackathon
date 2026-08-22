import os
import json
import base64
import asyncio
from pathlib import Path

from websockets.asyncio.client import connect


# ============================================================
# CONFIGURATION
# ============================================================

URL = os.getenv(
    "TEST_WS_URL",
    "ws://127.0.0.1:9000/media-stream"
)

STREAM_SID = "MZ_LOCAL_FULL_TEST"
CALL_SID = "CA_LOCAL_FULL_TEST"
ACCOUNT_SID = "AC_LOCAL_FULL_TEST"

INPUT_AUDIO = Path(
    "test_audio/test.mulaw"
)

OUTPUT_AUDIO = Path(
    "test_audio/websocket_bot_reply.mulaw"
)

FRAME_SIZE = 160


# ============================================================
# SEND A TWILIO-LIKE EVENT
# ============================================================

async def send_event(websocket, data):
    await websocket.send(
        json.dumps(data)
    )


# ============================================================
# WAIT FOR OPENING GREETING
# ============================================================

async def wait_for_greeting(websocket):
    print("👂 Waiting for opening greeting...")

    greeting_bytes = 0

    while True:
        raw = await asyncio.wait_for(
            websocket.recv(),
            timeout=20
        )

        data = json.loads(raw)

        event = data.get("event")

        if event == "media":
            payload = (
                data.get("media", {})
                .get("payload")
            )

            if payload:
                greeting_bytes += len(
                    base64.b64decode(payload)
                )

        elif event == "mark":
            mark_name = (
                data.get("mark", {})
                .get("name")
            )

            print(
                f"🔖 Mark received: {mark_name}"
            )

            if mark_name == "greeting_complete":
                print(
                    f"✅ Greeting completed "
                    f"({greeting_bytes} bytes)"
                )
                return


# ============================================================
# SEND CALLER SPEECH
# ============================================================

async def send_caller_audio(
    websocket,
    sequence
):
    if not INPUT_AUDIO.exists():
        raise FileNotFoundError(
            f"Missing test audio: {INPUT_AUDIO}"
        )

    audio = INPUT_AUDIO.read_bytes()

    print(
        f"🎤 Sending caller speech "
        f"({len(audio)} bytes)..."
    )

    chunk_number = 1
    timestamp = 0

    for position in range(
        0,
        len(audio),
        FRAME_SIZE
    ):
        frame = audio[
            position:
            position + FRAME_SIZE
        ]

        payload = base64.b64encode(
            frame
        ).decode("ascii")

        await send_event(
            websocket,
            {
                "event": "media",
                "sequenceNumber": str(sequence),
                "streamSid": STREAM_SID,
                "media": {
                    "track": "inbound",
                    "chunk": str(chunk_number),
                    "timestamp": str(timestamp),
                    "payload": payload
                }
            }
        )

        sequence += 1
        chunk_number += 1
        timestamp += 20

        # Approximate Twilio's real 20 ms audio timing.
        await asyncio.sleep(0.02)

    print(
        "🤫 Sending silence to trigger "
        "end-of-speech detection..."
    )

    # μ-law silence
    silence_frame = bytes(
        [0xFF] * FRAME_SIZE
    )

    # Around 1 second of silence.
    for _ in range(50):
        payload = base64.b64encode(
            silence_frame
        ).decode("ascii")

        await send_event(
            websocket,
            {
                "event": "media",
                "sequenceNumber": str(sequence),
                "streamSid": STREAM_SID,
                "media": {
                    "track": "inbound",
                    "chunk": str(chunk_number),
                    "timestamp": str(timestamp),
                    "payload": payload
                }
            }
        )

        sequence += 1
        chunk_number += 1
        timestamp += 20

        await asyncio.sleep(0.02)

    return sequence


# ============================================================
# RECEIVE AI RESPONSE
# ============================================================

async def receive_ai_reply(websocket):
    print("👂 Waiting for CivicResolve reply...")

    bot_audio = bytearray()

    while True:
        raw = await asyncio.wait_for(
            websocket.recv(),
            timeout=30
        )

        data = json.loads(raw)

        event = data.get("event")

        if event == "media":
            payload = (
                data.get("media", {})
                .get("payload")
            )

            if payload:
                audio_chunk = base64.b64decode(
                    payload
                )

                bot_audio.extend(
                    audio_chunk
                )

        elif event == "mark":
            mark_name = (
                data.get("mark", {})
                .get("name")
            )

            print(
                f"🔖 Mark received: {mark_name}"
            )

            if mark_name == "greeting_complete":
                print(
                    "ℹ️ Ignoring greeting mark."
                )
                continue

            if mark_name == "civicresolve_reply":
                print(
                    "✅ AI reply completed"
                )
                break

    return bytes(bot_audio)


# ============================================================
# MAIN FAKE CALL
# ============================================================

async def main():
    print()
    print("==============================")
    print(" CIVICRESOLVE FAKE TWILIO CALL")
    print("==============================")
    print()

    print(
        f"🔌 Connecting to: {URL}"
    )

    async with connect(URL) as websocket:
        print("✅ Fake Twilio connected")

        # ----------------------------------------------------
        # CONNECTED
        # ----------------------------------------------------

        await send_event(
            websocket,
            {
                "event": "connected",
                "protocol": "Call",
                "version": "1.0.0"
            }
        )

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        await send_event(
            websocket,
            {
                "event": "start",
                "sequenceNumber": "1",
                "streamSid": STREAM_SID,
                "start": {
                    "accountSid": ACCOUNT_SID,
                    "callSid": CALL_SID,
                    "streamSid": STREAM_SID,
                    "tracks": [
                        "inbound"
                    ],
                    "mediaFormat": {
                        "encoding":
                            "audio/x-mulaw",
                        "sampleRate": 8000,
                        "channels": 1
                    },
                    "customParameters": {}
                }
            }
        )

        # ----------------------------------------------------
        # WAIT UNTIL BOT FINISHES GREETING
        # ----------------------------------------------------

        await wait_for_greeting(
            websocket
        )

        print()
        print(
            "🗣️ Simulated caller now speaks..."
        )

        # ----------------------------------------------------
        # SEND CALLER AUDIO
        # ----------------------------------------------------

        sequence = 2

        sequence = await send_caller_audio(
            websocket,
            sequence
        )

        # ----------------------------------------------------
        # RECEIVE AI RESPONSE
        # ----------------------------------------------------

        bot_audio = await receive_ai_reply(
            websocket
        )

        OUTPUT_AUDIO.parent.mkdir(
            exist_ok=True
        )

        OUTPUT_AUDIO.write_bytes(
            bot_audio
        )

        print(
            f"🔊 Received "
            f"{len(bot_audio)} bytes "
            f"of AI speech"
        )

        print(
            f"✅ Saved reply to: "
            f"{OUTPUT_AUDIO}"
        )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        await send_event(
            websocket,
            {
                "event": "stop",
                "sequenceNumber":
                    str(sequence),
                "streamSid":
                    STREAM_SID,
                "stop": {
                    "accountSid":
                        ACCOUNT_SID,
                    "callSid":
                        CALL_SID
                }
            }
        )

        print()
        print(
            "✅ Fake Twilio call completed"
        )


if __name__ == "__main__":
    asyncio.run(main())
