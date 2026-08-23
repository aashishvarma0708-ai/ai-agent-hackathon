import os
import json
import base64
import asyncio
from pathlib import Path

from websockets.asyncio.client import connect


URL = os.getenv(
    "TEST_WS_URL",
    "ws://127.0.0.1:9000/media-stream"
)

OUTPUT_FILE = Path(
    "test_audio/websocket_greeting.mulaw"
)

STREAM_SID = "MZ_GREETING_TEST"


async def main():

    print("🔌 Connecting fake Twilio...")

    audio = bytearray()

    async with connect(URL) as websocket:

        print("✅ Connected")

        await websocket.send(
            json.dumps({
                "event": "connected",
                "protocol": "Call",
                "version": "1.0.0",
            })
        )

        await websocket.send(
            json.dumps({
                "event": "start",
                "sequenceNumber": "1",
                "streamSid": STREAM_SID,
                "start": {
                    "accountSid":
                        "AC_LOCAL_TEST",
                    "callSid":
                        "CA_LOCAL_TEST",
                    "streamSid":
                        STREAM_SID,
                    "tracks": [
                        "inbound"
                    ],
                    "mediaFormat": {
                        "encoding":
                            "audio/x-mulaw",
                        "sampleRate": 8000,
                        "channels": 1,
                    },
                    "customParameters": {},
                },
            })
        )

        print("👂 Waiting for greeting...")

        while True:

            raw = await asyncio.wait_for(
                websocket.recv(),
                timeout=20,
            )

            data = json.loads(raw)

            if data.get("event") == "media":

                payload = (
                    data.get("media", {})
                    .get("payload")
                )

                if payload:
                    audio.extend(
                        base64.b64decode(payload)
                    )

            elif data.get("event") == "mark":

                name = (
                    data.get("mark", {})
                    .get("name")
                )

                print(
                    f"🔖 Mark received: {name}"
                )

                if name == "greeting_complete":
                    break

        OUTPUT_FILE.write_bytes(
            bytes(audio)
        )

        print(
            f"🔊 Received "
            f"{len(audio)} greeting bytes"
        )

        print(
            f"✅ Saved: {OUTPUT_FILE}"
        )

        await websocket.send(
            json.dumps({
                "event": "stop",
                "streamSid": STREAM_SID,
                "stop": {
                    "accountSid":
                        "AC_LOCAL_TEST",
                    "callSid":
                        "CA_LOCAL_TEST",
                },
            })
        )


if __name__ == "__main__":
    asyncio.run(main())
