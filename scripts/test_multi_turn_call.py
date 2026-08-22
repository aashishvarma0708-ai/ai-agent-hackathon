import os
import json
import base64
import asyncio
import subprocess
from pathlib import Path

from websockets.asyncio.client import connect


# ============================================================
# CONFIGURATION
# ============================================================

URL = os.getenv(
    "TEST_WS_URL",
    "ws://127.0.0.1:9000/media-stream"
)

STREAM_SID = "MZ_MULTI_TURN_TEST"
CALL_SID = "CA_MULTI_TURN_TEST"
ACCOUNT_SID = "AC_MULTI_TURN_TEST"

FRAME_SIZE = 160

TEST_AUDIO_DIR = Path(
    "test_audio/multi_turn"
)

BOT_REPLY_DIR = Path(
    "test_audio/multi_turn/replies"
)


CALLER_TURNS = [
    "There is a large pothole on the road.",
    "Near University Gate.",
    "Yes, there is.",
    "Yes.",
]


# ============================================================
# CREATE MULAW TEST SPEECH USING MACOS SAY + FFMPEG
# ============================================================

def create_test_audio():

    TEST_AUDIO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    BOT_REPLY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    generated_files = []

    for index, text in enumerate(
        CALLER_TURNS,
        start=1
    ):

        aiff_file = (
            TEST_AUDIO_DIR
            / f"caller_{index}.aiff"
        )

        mulaw_file = (
            TEST_AUDIO_DIR
            / f"caller_{index}.mulaw"
        )

        print(
            f"🎙️ Creating caller turn "
            f"{index}: {text}"
        )

        subprocess.run(
            [
                "say",
                "-o",
                str(aiff_file),
                text,
            ],
            check=True
        )

        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(aiff_file),
                "-ac",
                "1",
                "-ar",
                "8000",
                "-c:a",
                "pcm_mulaw",
                "-f",
                "mulaw",
                str(mulaw_file),
            ],
            check=True
        )

        generated_files.append(
            mulaw_file
        )

    return generated_files


# ============================================================
# SEND JSON EVENT
# ============================================================

async def send_event(
    websocket,
    data
):

    await websocket.send(
        json.dumps(data)
    )


# ============================================================
# RECEIVE ONE BOT RESPONSE
# ============================================================

async def receive_bot_audio(
    websocket,
    expected_mark,
    output_file
):

    bot_audio = bytearray()

    print(
        f"👂 Waiting for bot mark: "
        f"{expected_mark}"
    )

    while True:

        raw = await asyncio.wait_for(
            websocket.recv(),
            timeout=30
        )

        data = json.loads(raw)

        event = data.get(
            "event"
        )

        if event == "media":

            payload = (
                data.get(
                    "media",
                    {}
                )
                .get(
                    "payload"
                )
            )

            if payload:

                bot_audio.extend(
                    base64.b64decode(
                        payload
                    )
                )

        elif event == "mark":

            mark_name = (
                data.get(
                    "mark",
                    {}
                )
                .get(
                    "name"
                )
            )

            print(
                f"🔖 Bot mark: "
                f"{mark_name}"
            )

            if (
                mark_name
                == expected_mark
            ):
                break

    output_file.write_bytes(
        bytes(bot_audio)
    )

    print(
        f"🔊 Bot audio received: "
        f"{len(bot_audio)} bytes"
    )

    print(
        f"💾 Saved: "
        f"{output_file}"
    )


# ============================================================
# SEND ONE CALLER TURN
# ============================================================

async def send_caller_turn(
    websocket,
    audio_file,
    sequence,
    turn_number
):

    audio = (
        audio_file
        .read_bytes()
    )

    print()
    print(
        "-----------------------------------"
    )

    print(
        f"🗣️ CALLER TURN {turn_number}: "
        f"{CALLER_TURNS[turn_number - 1]}"
    )

    print(
        f"🎤 Streaming "
        f"{len(audio)} bytes"
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

        payload = (
            base64.b64encode(
                frame
            )
            .decode("ascii")
        )

        await send_event(
            websocket,
            {
                "event": "media",
                "sequenceNumber":
                    str(sequence),
                "streamSid":
                    STREAM_SID,
                "media": {
                    "track":
                        "inbound",
                    "chunk":
                        str(chunk_number),
                    "timestamp":
                        str(timestamp),
                    "payload":
                        payload,
                },
            }
        )

        sequence += 1
        chunk_number += 1
        timestamp += 20

        await asyncio.sleep(
            0.02
        )

    # --------------------------------------------------------
    # SILENCE AFTER EACH UTTERANCE
    #
    # Enough silence for normal Deepgram endpointing.
    # Short-answer logic should trigger BEFORE needing all
    # of this silence on Yes/No turns.
    # --------------------------------------------------------

    silence_frame = bytes(
        [0xFF] * FRAME_SIZE
    )

    for _ in range(35):

        payload = (
            base64.b64encode(
                silence_frame
            )
            .decode("ascii")
        )

        await send_event(
            websocket,
            {
                "event": "media",
                "sequenceNumber":
                    str(sequence),
                "streamSid":
                    STREAM_SID,
                "media": {
                    "track":
                        "inbound",
                    "chunk":
                        str(chunk_number),
                    "timestamp":
                        str(timestamp),
                    "payload":
                        payload,
                },
            }
        )

        sequence += 1
        chunk_number += 1
        timestamp += 20

        await asyncio.sleep(
            0.02
        )

    return sequence


# ============================================================
# MAIN
# ============================================================

async def main():

    print()
    print(
        "========================================"
    )
    print(
        " CIVICRESOLVE FOUR-TURN CALL SIMULATION"
    )
    print(
        "========================================"
    )
    print()

    print(
        "🎙️ Generating caller test audio..."
    )

    caller_audio_files = (
        create_test_audio()
    )

    print()
    print(
        f"🔌 Connecting to: {URL}"
    )

    async with connect(
        URL
    ) as websocket:

        print(
            "✅ Fake Twilio connected"
        )

        # ====================================================
        # CONNECTED
        # ====================================================

        await send_event(
            websocket,
            {
                "event":
                    "connected",
                "protocol":
                    "Call",
                "version":
                    "1.0.0",
            }
        )

        # ====================================================
        # START
        # ====================================================

        await send_event(
            websocket,
            {
                "event":
                    "start",
                "sequenceNumber":
                    "1",
                "streamSid":
                    STREAM_SID,
                "start": {
                    "accountSid":
                        ACCOUNT_SID,
                    "callSid":
                        CALL_SID,
                    "streamSid":
                        STREAM_SID,
                    "tracks": [
                        "inbound"
                    ],
                    "mediaFormat": {
                        "encoding":
                            "audio/x-mulaw",
                        "sampleRate":
                            8000,
                        "channels":
                            1,
                    },
                    "customParameters":
                        {},
                },
            }
        )

        # ====================================================
        # RECEIVE GREETING
        # ====================================================

        greeting_output = (
            BOT_REPLY_DIR
            / "greeting.mulaw"
        )

        await receive_bot_audio(
            websocket,
            "greeting_complete",
            greeting_output
        )

        print()
        print(
            "✅ Greeting completed."
        )

        sequence = 2

        # ====================================================
        # RUN ALL FOUR TURNS
        # ====================================================

        for turn_number, audio_file in enumerate(
            caller_audio_files,
            start=1
        ):

            sequence = (
                await send_caller_turn(
                    websocket,
                    audio_file,
                    sequence,
                    turn_number
                )
            )

            reply_output = (
                BOT_REPLY_DIR
                / f"reply_{turn_number}.mulaw"
            )

            await receive_bot_audio(
                websocket,
                "civicresolve_reply",
                reply_output
            )

            print(
                f"✅ TURN {turn_number} "
                f"COMPLETED"
            )

            # Small natural pause before
            # next simulated caller response.
            await asyncio.sleep(
                0.4
            )

        # ====================================================
        # STOP
        # ====================================================

        await send_event(
            websocket,
            {
                "event":
                    "stop",
                "sequenceNumber":
                    str(sequence),
                "streamSid":
                    STREAM_SID,
                "stop": {
                    "accountSid":
                        ACCOUNT_SID,
                    "callSid":
                        CALL_SID,
                },
            }
        )

        print()
        print(
            "========================================"
        )

        print(
            "✅ FOUR-TURN SIMULATION COMPLETED"
        )

        print(
            "========================================"
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
