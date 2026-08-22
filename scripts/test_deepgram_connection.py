import asyncio

from app.deepgram_stt import DeepgramSTT


async def main():
    stt = DeepgramSTT()

    try:
        await stt.connect()

        print(
            "✅ Deepgram authentication "
            "and WebSocket connection successful"
        )

    finally:
        await stt.close()


if __name__ == "__main__":
    asyncio.run(main())
