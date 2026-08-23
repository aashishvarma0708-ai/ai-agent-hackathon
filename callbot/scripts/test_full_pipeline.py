import asyncio
from pathlib import Path

from app.agent import CallAgent
from app.deepgram_stt import DeepgramSTT
from app.deepgram_tts import DeepgramTTS


INPUT_AUDIO = Path("test_audio/test.mulaw")
OUTPUT_AUDIO = Path("test_audio/pipeline_reply.mulaw")

FRAME_SIZE = 160


async def transcribe_audio():
    stt = DeepgramSTT()

    final_transcript = ""
    transcript_ready = asyncio.Event()

    await stt.connect()

    async def receive_results():
        nonlocal final_transcript

        async for result in stt.receive():
            transcript = result["transcript"]

            if result["is_final"]:
                print(f"📝 FINAL STT: {transcript}")

                if transcript:
                    final_transcript = transcript

            else:
                print(f"… INTERIM: {transcript}")

            if result["speech_final"]:
                transcript_ready.set()
                break

    receiver = asyncio.create_task(
        receive_results()
    )

    try:
        audio = INPUT_AUDIO.read_bytes()

        print(
            f"🎤 Sending {len(audio)} bytes "
            "of test speech to Deepgram..."
        )

        for position in range(
            0,
            len(audio),
            FRAME_SIZE
        ):
            frame = audio[
                position:
                position + FRAME_SIZE
            ]

            await stt.send_audio(frame)

            # Approximate real Twilio timing.
            await asyncio.sleep(0.02)

        await stt.finalize()

        try:
            await asyncio.wait_for(
                transcript_ready.wait(),
                timeout=5
            )

        except asyncio.TimeoutError:
            print(
                "⚠️ Speech-final event timed out. "
                "Using latest final transcript."
            )

        # Give final result packets a moment to arrive.
        await asyncio.sleep(0.5)

    finally:
        if not receiver.done():
            receiver.cancel()

            try:
                await receiver
            except asyncio.CancelledError:
                pass

        await stt.close()

    return final_transcript


async def synthesize_response(text):
    tts = DeepgramTTS()

    await tts.connect()

    try:
        audio = await tts.synthesize(text)

        OUTPUT_AUDIO.parent.mkdir(
            exist_ok=True
        )

        OUTPUT_AUDIO.write_bytes(audio)

        print(
            f"🔊 Saved AI response: "
            f"{OUTPUT_AUDIO}"
        )

        print(
            f"🔊 TTS bytes: {len(audio)}"
        )

    finally:
        await tts.close()


async def main():
    print("\n==============================")
    print(" CIVICRESOLVE VOICE PIPELINE")
    print("==============================\n")

    # 1. Speech → text
    transcript = await transcribe_audio()

    if not transcript:
        print("❌ No transcript received.")
        return

    print(
        f"\n👤 CALLER: {transcript}"
    )

    # 2. Text → Groq agent
    print("\n🧠 Sending transcript to Groq...")

    agent = CallAgent()

    response = agent.respond(
        transcript
    )

    print(
        f"\n🤖 CIVICRESOLVE: {response}"
    )

    # 3. Groq response → speech
    print("\n🔊 Converting response to speech...")

    await synthesize_response(
        response
    )

    print("\n✅ FULL PIPELINE PASSED\n")


if __name__ == "__main__":
    asyncio.run(main())

