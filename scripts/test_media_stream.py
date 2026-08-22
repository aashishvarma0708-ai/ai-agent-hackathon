import asyncio
import base64
import json

from websockets.asyncio.client import connect


URL = "ws://127.0.0.1:9000/media-stream"

STREAM_SID = "MZ_LOCAL_TEST_001"
CALL_SID = "CA_LOCAL_TEST_001"
ACCOUNT_SID = "AC_LOCAL_TEST_001"


async def main():
    print("🔌 Connecting to local call bot...")

    async with connect(URL) as websocket:
        print("✅ Connected")

        # Mimic Twilio's initial connected event
        await websocket.send(
            json.dumps(
                {
                    "event": "connected",
                    "protocol": "Call",
                    "version": "1.0.0",
                }
            )
        )

        # Mimic Twilio's start event
        await websocket.send(
            json.dumps(
                {
                    "event": "start",
                    "sequenceNumber": "1",
                    "streamSid": STREAM_SID,
                    "start": {
                        "accountSid": ACCOUNT_SID,
                        "callSid": CALL_SID,
                        "streamSid": STREAM_SID,
                        "tracks": ["inbound"],
                        "mediaFormat": {
                            "encoding": "audio/x-mulaw",
                            "sampleRate": 8000,
                            "channels": 1,
                        },
                        "customParameters": {},
                    },
                }
            )
        )

        print("🎤 Sending simulated Twilio audio...")

        # 0xFF is μ-law silence.
        # 160 bytes represents roughly one 20 ms
        # telephony audio frame at 8 kHz.
        fake_audio = bytes([0xFF] * 160)

        for number in range(10):
            payload = base64.b64encode(
                fake_audio
            ).decode("ascii")

            message = {
                "event": "media",
                "sequenceNumber": str(number + 2),
                "streamSid": STREAM_SID,
                "media": {
                    "track": "inbound",
                    "chunk": str(number + 1),
                    "timestamp": str(number * 20),
                    "payload": payload,
                },
            }

            await websocket.send(
                json.dumps(message)
            )

            await asyncio.sleep(0.02)

        # Mimic end of call
        await websocket.send(
            json.dumps(
                {
                    "event": "stop",
                    "sequenceNumber": "12",
                    "streamSid": STREAM_SID,
                    "stop": {
                        "accountSid": ACCOUNT_SID,
                        "callSid": CALL_SID,
                    },
                }
            )
        )

        print("✅ Local Twilio simulation completed")


if __name__ == "__main__":
    asyncio.run(main())
