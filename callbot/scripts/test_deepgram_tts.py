import asyncio
from pathlib import Path

from app.deepgram_tts import DeepgramTTS


OUTPUT_FILE = Path(
    "test_audio/deepgram_reply.mulaw"
)


async def main():

    tts = DeepgramTTS()

    try:

        await tts.connect()

        text = (
            "Hello. This is CivicResolve. "
            "What issue would you like to report?"
        )

        print(f"🤖 Text: {text}")

        audio = await tts.synthesize(text)

        print(
            f"🔊 Received {len(audio)} "
            "bytes of audio"
        )

        OUTPUT_FILE.parent.mkdir(
            exist_ok=True
        )

        OUTPUT_FILE.write_bytes(audio)

        print(
            f"✅ Saved audio to {OUTPUT_FILE}"
        )

    finally:

        await tts.close()


if __name__ == "__main__":
    asyncio.run(main())
