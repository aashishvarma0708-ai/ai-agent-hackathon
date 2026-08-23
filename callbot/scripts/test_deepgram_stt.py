import asyncio
from pathlib import Path

from app.deepgram_stt import DeepgramSTT


AUDIO_FILE = Path(
    "test_audio/test.mulaw"
)

FRAME_SIZE = 160


async def send_audio(stt):
    audio = AUDIO_FILE.read_bytes()

    print(
        f"🎧 Loaded {len(audio)} bytes "
        "of μ-law test audio"
    )

    for position in range(
        0,
        len(audio),
        FRAME_SIZE,
    ):
        frame = audio[
            position:
            position + FRAME_SIZE
        ]

        await stt.send_audio(frame)

        # Approximate Twilio's 20 ms frame timing.
        await asyncio.sleep(0.02)

    print("✅ Finished sending audio")

    await stt.finalize()


async def receive_transcripts(stt):
    async for result in stt.receive():

        transcript = result["transcript"]

        if result["is_final"]:
            print(
                f"📝 FINAL: {transcript}"
            )

        else:
            print(
                f"… INTERIM: {transcript}"
            )

        if result["speech_final"]:
            print(
                "✅ Deepgram detected "
                "end of speech"
            )


async def main():
    stt = DeepgramSTT()

    await stt.connect()

    receiver = asyncio.create_task(
        receive_transcripts(stt)
    )

    try:
        await send_audio(stt)

        # Give Deepgram a moment
        # to send final results.
        await asyncio.sleep(2)

    finally:
        receiver.cancel()

        try:
            await receiver
        except asyncio.CancelledError:
            pass

        await stt.close()


if __name__ == "__main__":
    asyncio.run(main())
