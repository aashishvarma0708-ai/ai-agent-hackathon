import os
import json
import base64
import asyncio
import time

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.agent import CallAgent
from app.deepgram_stt import DeepgramSTT
from app.deepgram_tts import DeepgramTTS


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

PUBLIC_HOST = os.getenv("PUBLIC_HOST", "")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="CivicResolve Call Bot"
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "CivicResolve Call Bot"
    }


# ============================================================
# OPTIONAL TWILIO VOICE WEBHOOK
#
# You are currently using a TwiML Bin, but keeping this route
# allows you to switch back to webhook mode later.
# ============================================================

@app.post("/voice")
async def voice():

    twiml = f"""
<Response>
    <Connect>
        <Stream url="wss://{PUBLIC_HOST}/media-stream" />
    </Connect>
</Response>
""".strip()

    return Response(
        content=twiml,
        media_type="application/xml"
    )


# ============================================================
# SHORT ANSWER NORMALIZATION
#
# This is important for fast responses like:
# yes
# yes, there is
# correct
# no
#
# We do NOT want to wait unnecessarily for speech_final
# when Deepgram has already finalized one of these answers.
# ============================================================

def normalize_short_answer(text: str) -> str:

    text = text.lower().strip()

    punctuation = [
        ",",
        ".",
        "!",
        "?",
        ";",
        ":",
        "'",
        '"',
    ]

    for character in punctuation:
        text = text.replace(
            character,
            ""
        )

    # Collapse repeated spaces.
    return " ".join(
        text.split()
    )


SHORT_ANSWERS = {
    "yes",
    "yeah",
    "yep",
    "correct",
    "right",
    "exactly",

    "yes correct",
    "yes thats correct",
    "yes thats it",
    "thats it",

    "yes there is",
    "yes it is",

    "no",
    "nope",
    "no there isnt",
    "no there is not",
    "no it isnt",
    "no its not",
}


# ============================================================
# SEND TWILIO MARK
# ============================================================

async def send_mark(
    websocket: WebSocket,
    stream_sid: str,
    mark_name: str,
):

    await websocket.send_text(
        json.dumps({
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {
                "name": mark_name
            }
        })
    )


# ============================================================
# STREAM OPENING GREETING
#
# IMPORTANT:
# We stream each audio chunk immediately instead of waiting
# for Deepgram to generate the entire greeting.
# ============================================================

async def send_opening_greeting(
    websocket: WebSocket,
    stream_sid: str,
    tts: DeepgramTTS,
):

    # Shorter greeting = less call time wasted.
    greeting = (
        "CivicResolve. "
        "What would you like to report?"
    )

    print()
    print(
        f"🤖 GREETING: {greeting}"
    )

    start_time = (
        time.perf_counter()
    )

    first_audio = True
    total_audio_bytes = 0

    async for audio_chunk in (
        tts.stream_synthesize(
            greeting
        )
    ):

        if not audio_chunk:
            continue

        if first_audio:

            first_audio = False

            first_audio_ms = (
                time.perf_counter()
                - start_time
            ) * 1000

            print(
                f"⚡ Greeting first audio: "
                f"{first_audio_ms:.0f} ms"
            )

        total_audio_bytes += len(
            audio_chunk
        )

        payload = base64.b64encode(
            audio_chunk
        ).decode("ascii")

        await websocket.send_text(
            json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            })
        )

    await send_mark(
        websocket,
        stream_sid,
        "greeting_complete"
    )

    print(
        f"✅ Opening greeting streamed "
        f"({total_audio_bytes} bytes)"
    )


# ============================================================
# GROQ → STREAMING DEEPGRAM TTS → TWILIO
# ============================================================

async def generate_and_send_reply(
    websocket: WebSocket,
    stream_sid: str,
    agent: CallAgent,
    tts: DeepgramTTS,
    transcript: str,
):

    total_start = (
        time.perf_counter()
    )

    print()
    print(
        f"👤 CALLER: {transcript}"
    )

    # --------------------------------------------------------
    # GROQ
    # --------------------------------------------------------

    groq_start = (
        time.perf_counter()
    )

    # Groq SDK is synchronous.
    # Run it in a worker thread so FastAPI's event loop
    # doesn't freeze.
    reply = await asyncio.to_thread(
        agent.respond,
        transcript
    )

    groq_ms = (
        time.perf_counter()
        - groq_start
    ) * 1000

    print(
        f"🤖 CIVICRESOLVE: {reply}"
    )

    print(
        f"⏱️ Groq latency: "
        f"{groq_ms:.0f} ms"
    )

    # --------------------------------------------------------
    # STREAM TTS IMMEDIATELY
    # --------------------------------------------------------

    tts_start = (
        time.perf_counter()
    )

    first_audio = True
    total_audio_bytes = 0

    async for audio_chunk in (
        tts.stream_synthesize(
            reply
        )
    ):

        if not audio_chunk:
            continue

        if first_audio:

            first_audio = False

            first_tts_ms = (
                time.perf_counter()
                - tts_start
            ) * 1000

            speech_to_first_audio_ms = (
                time.perf_counter()
                - total_start
            ) * 1000

            print(
                f"⚡ First TTS audio: "
                f"{first_tts_ms:.0f} ms"
            )

            print(
                f"⚡ Speech-to-first-audio: "
                f"{speech_to_first_audio_ms:.0f} ms"
            )

        total_audio_bytes += len(
            audio_chunk
        )

        payload = base64.b64encode(
            audio_chunk
        ).decode("ascii")

        await websocket.send_text(
            json.dumps({
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            })
        )

    # --------------------------------------------------------
    # MARK END OF AI RESPONSE
    # --------------------------------------------------------

    await send_mark(
        websocket,
        stream_sid,
        "civicresolve_reply"
    )

    total_ms = (
        time.perf_counter()
        - total_start
    ) * 1000

    print(
        f"✅ Streamed "
        f"{total_audio_bytes} "
        f"TTS bytes to Twilio"
    )

    print(
        f"⏱️ Total reply pipeline: "
        f"{total_ms:.0f} ms"
    )


# ============================================================
# TWILIO MEDIA STREAM
# ============================================================

@app.websocket("/media-stream")
async def media_stream(
    websocket: WebSocket
):

    await websocket.accept()

    print()
    print(
        "====================================="
    )
    print(
        "📞 NEW CIVICRESOLVE CALL CONNECTION"
    )
    print(
        "====================================="
    )

    print(
        "✅ WebSocket connected"
    )

    # ========================================================
    # PER-CALL STATE
    # ========================================================

    stream_sid = None

    greeting_sent = False

    # Stores multiple finalized Deepgram chunks that belong
    # to the same caller utterance.
    utterance_parts = []

    # When we immediately process a short answer such as
    # "yes", Deepgram may still send more results belonging
    # to that SAME speech turn.
    #
    # This flag suppresses those duplicate results until
    # speech_final closes the turn.
    fast_turn_handled = False

    # Separate agent per phone call.
    # This preserves conversation memory for this caller
    # without mixing calls together.
    agent = CallAgent()

    stt = DeepgramSTT()
    tts = DeepgramTTS()

    deepgram_listener = None

    # Prevent overlapping AI responses.
    reply_lock = asyncio.Lock()

    try:

        # ====================================================
        # CONNECT TO DEEPGRAM
        # ====================================================

        await stt.connect()
        await tts.connect()

        # ====================================================
        # DEEPGRAM TRANSCRIPT LISTENER
        # ====================================================

        async def listen_to_deepgram():

            nonlocal stream_sid
            nonlocal utterance_parts
            nonlocal fast_turn_handled

            async for result in stt.receive():

                transcript = (
                    result.get(
                        "transcript",
                        ""
                    )
                    .strip()
                )

                is_final = result.get(
                    "is_final",
                    False
                )

                speech_final = result.get(
                    "speech_final",
                    False
                )

                # ------------------------------------------------
                # SUPPRESS DUPLICATE RESULTS AFTER FAST ANSWER
                # ------------------------------------------------

                if fast_turn_handled:

                    # We already processed this caller turn.
                    # Ignore everything until Deepgram tells us
                    # the speech boundary is complete.

                    if speech_final:

                        fast_turn_handled = False
                        utterance_parts = []

                        print(
                            "✅ Fast-turn boundary completed"
                        )

                    continue

                if not transcript:
                    continue

                # ------------------------------------------------
                # INTERIM TRANSCRIPT
                # ------------------------------------------------

                if not is_final:

                    print(
                        f"… STT: {transcript}"
                    )

                    continue

                # ------------------------------------------------
                # FINAL STT SEGMENT
                # ------------------------------------------------

                print(
                    f"📝 STT FINAL: "
                    f"{transcript}"
                )

                utterance_parts.append(
                    transcript
                )

                # ------------------------------------------------
                # FAST SHORT-ANSWER DETECTION
                # ------------------------------------------------

                normalized = (
                    normalize_short_answer(
                        transcript
                    )
                )

                if normalized in SHORT_ANSWERS:

                    full_utterance = " ".join(
                        utterance_parts
                    ).strip()

                    utterance_parts = []

                    print(
                        f"⚡ Fast short-answer "
                        f"detected: "
                        f"{full_utterance}"
                    )

                    # If Deepgram already marked this same
                    # packet as speech_final, we do NOT need
                    # to suppress future packets.
                    #
                    # Otherwise suppress results until the
                    # matching speech_final arrives.
                    if speech_final:
                        fast_turn_handled = False
                    else:
                        fast_turn_handled = True

                    if (
                        full_utterance
                        and stream_sid
                    ):

                        async with reply_lock:

                            await (
                                generate_and_send_reply(
                                    websocket,
                                    stream_sid,
                                    agent,
                                    tts,
                                    full_utterance
                                )
                            )

                    # IMPORTANT:
                    # Don't fall through into the normal
                    # speech_final handler and process it twice.
                    continue

                # ------------------------------------------------
                # NORMAL END-OF-SPEECH HANDLING
                # ------------------------------------------------

                if speech_final:

                    full_utterance = " ".join(
                        utterance_parts
                    ).strip()

                    utterance_parts = []

                    if (
                        full_utterance
                        and stream_sid
                    ):

                        async with reply_lock:

                            await (
                                generate_and_send_reply(
                                    websocket,
                                    stream_sid,
                                    agent,
                                    tts,
                                    full_utterance
                                )
                            )

        deepgram_listener = (
            asyncio.create_task(
                listen_to_deepgram()
            )
        )

        # ====================================================
        # TWILIO EVENT LOOP
        # ====================================================

        while True:

            message = (
                await websocket.receive_text()
            )

            data = json.loads(
                message
            )

            event = data.get(
                "event"
            )

            # ------------------------------------------------
            # CONNECTED
            # ------------------------------------------------

            if event == "connected":

                print(
                    "✅ Twilio protocol connected"
                )

            # ------------------------------------------------
            # START
            # ------------------------------------------------

            elif event == "start":

                start_data = data.get(
                    "start",
                    {}
                )

                stream_sid = (
                    start_data.get(
                        "streamSid"
                    )
                    or data.get(
                        "streamSid"
                    )
                )

                print(
                    f"✅ Stream started: "
                    f"{stream_sid}"
                )

                print(
                    "🎧 Media format:",
                    start_data.get(
                        "mediaFormat",
                        {}
                    )
                )

                # --------------------------------------------
                # OPENING GREETING
                # --------------------------------------------

                if not greeting_sent:

                    greeting_sent = True

                    await (
                        send_opening_greeting(
                            websocket,
                            stream_sid,
                            tts
                        )
                    )

            # ------------------------------------------------
            # INBOUND CALLER AUDIO
            # ------------------------------------------------

            elif event == "media":

                media = data.get(
                    "media",
                    {}
                )

                track = media.get(
                    "track"
                )

                # Ignore anything explicitly identified as
                # something other than inbound caller audio.
                if (
                    track is not None
                    and track != "inbound"
                ):
                    continue

                payload = media.get(
                    "payload"
                )

                if not payload:
                    continue

                try:

                    audio_bytes = (
                        base64.b64decode(
                            payload
                        )
                    )

                except Exception as exc:

                    print(
                        f"⚠️ Invalid audio payload: "
                        f"{exc}"
                    )

                    continue

                await stt.send_audio(
                    audio_bytes
                )

            # ------------------------------------------------
            # MARK RETURNED BY TWILIO
            # ------------------------------------------------

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
                    f"🔖 Twilio mark: "
                    f"{mark_name}"
                )

            # ------------------------------------------------
            # CALL ENDED
            # ------------------------------------------------

            elif event == "stop":

                print(
                    "🛑 Twilio stream stopped"
                )

                break

            # ------------------------------------------------
            # OTHER EVENT
            # ------------------------------------------------

            else:

                if event:

                    print(
                        f"ℹ️ Twilio event: "
                        f"{event}"
                    )


    # ========================================================
    # WEBSOCKET DISCONNECTED
    # ========================================================

    except WebSocketDisconnect:

        print(
            "📞 WebSocket disconnected"
        )


    # ========================================================
    # OTHER PIPELINE ERROR
    # ========================================================

    except Exception as exc:

        print(
            f"❌ Call pipeline error: "
            f"{type(exc).__name__}: "
            f"{exc}"
        )


    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if deepgram_listener is not None:

            deepgram_listener.cancel()

            try:

                await deepgram_listener

            except asyncio.CancelledError:

                pass

            except Exception:

                pass

        try:

            await stt.close()

        except Exception as exc:

            print(
                f"⚠️ STT cleanup error: "
                f"{exc}"
            )

        try:

            await tts.close()

        except Exception as exc:

            print(
                f"⚠️ TTS cleanup error: "
                f"{exc}"
            )

        print(
            "🧹 Call resources cleaned up"
        )

        print(
            "====================================="
        )

        print()
