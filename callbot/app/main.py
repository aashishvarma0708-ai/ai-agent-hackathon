import os
import json
import base64
import asyncio
import time

from app.browser_phone import router as browser_phone_router
from app.evidence_routes import router as evidence_router
from dotenv import load_dotenv
from app.civicresolve_client import CivicResolveClient, CivicResolveError
from app.sms_sender import CivicResolveSMS
from app.evidence_links import EvidenceLinkStore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response

from app.agent import CallAgent
from app.call_state import CallState
from app.deepgram_stt import DeepgramSTT
from app.deepgram_tts import DeepgramTTS


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


def get_public_host() -> str:
    host = os.getenv("PUBLIC_HOST", "").strip()

    for prefix in (
        "https://",
        "http://",
        "wss://",
        "ws://",
    ):
        if host.startswith(prefix):
            host = host[len(prefix):]

    return host.rstrip("/")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="CivicResolve Call Bot",
    version="0.3.0",
)
app.include_router(
    browser_phone_router
)

app.include_router(
    evidence_router
)


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "CivicResolve Call Bot",
    }


@app.get("/health")
async def health():
    public_host = get_public_host()

    return {
        "status": "ok",
        "service": "CivicResolve Call Bot",
        "public_host_configured": bool(public_host),
        "public_host": public_host,
    }


@app.post("/voice")
async def voice(
    request: Request,
):

    public_host = get_public_host()

    try:
        form = await request.form()

        caller_number = str(
            form.get("From")
            or ""
        ).strip()

    except Exception:
        caller_number = ""

    print("\n📞 Incoming Twilio voice webhook", flush=True)

    if not public_host:
        twiml = """
<Response>
    <Say>Voice service configuration is incomplete.</Say>
</Response>
""".strip()

        return Response(
            content=twiml,
            media_type="application/xml",
        )

    websocket_url = f"wss://{public_host}/media-stream"

    print(
        f"🔗 WebSocket URL: {websocket_url}",
        flush=True,
    )

    twiml = f"""
<Response>
    <Connect>
        <Stream
            url="{websocket_url}"
            statusCallback="https://{public_host}/stream-status"
            statusCallbackMethod="POST"
        >
            <Parameter
                name="caller_number"
                value="{caller_number}"
            />
        </Stream>
    </Connect>
</Response>
""".strip()

    return Response(
        content=twiml,
        media_type="application/xml",
    )


# ============================================================
# SHORT ANSWERS
# ============================================================


def normalize_short_answer(text: str) -> str:
    text = (text or "").lower().strip()

    for character in (
        ",",
        ".",
        "!",
        "?",
        ";",
        ":",
        "'",
        '"',
    ):
        text = text.replace(character, "")

    return " ".join(text.split())


SHORT_ANSWERS = {
    "yes",
    "yeah",
    "yep",
    "correct",
    "right",
    "exactly",
    "true",
    "yes correct",
    "yes thats correct",
    "yes thats it",
    "thats it",
    "yes there is",
    "yes it is",
    "sure",
    "okay",
    "ok",
    "fine",
    "alright",
    "all right",
    "sounds good",
    "yeah sure",
    "yeah fine",
    "yeah okay",
    "yeah ok",
    "yes sure",
    "yes fine",
    "yes okay",
    "yes ok",
    "okay sure",
    "ok sure",
    "sure yeah",
    "go ahead",
    "go for it",
    "do it",
    "please do",
    "please do it",
    "absolutely",
    "of course",
    "no",
    "nope",
    "false",
    "no there isnt",
    "no there is not",
    "no it isnt",
    "no its not",
    "haan",
    "han",
    "ji",
    "haan ji",
    "nahi",
    "nahin",
}


# ============================================================
# TWILIO OUTPUT HELPERS
# ============================================================


async def send_twilio_json(
    websocket: WebSocket,
    send_lock: asyncio.Lock,
    payload: dict,
):
    async with send_lock:
        await websocket.send_text(
            json.dumps(payload)
        )


async def send_twilio_media(
    websocket: WebSocket,
    send_lock: asyncio.Lock,
    stream_sid: str,
    audio_bytes: bytes,
):
    if not audio_bytes:
        return

    payload = base64.b64encode(
        audio_bytes
    ).decode("ascii")

    await send_twilio_json(
        websocket,
        send_lock,
        {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": payload,
            },
        },
    )


async def send_twilio_mark(
    websocket: WebSocket,
    send_lock: asyncio.Lock,
    stream_sid: str,
    mark_name: str,
):
    await send_twilio_json(
        websocket,
        send_lock,
        {
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {
                "name": mark_name,
            },
        },
    )


async def send_twilio_clear(
    websocket: WebSocket,
    send_lock: asyncio.Lock,
    stream_sid: str,
):
    await send_twilio_json(
        websocket,
        send_lock,
        {
            "event": "clear",
            "streamSid": stream_sid,
        },
    )


# ============================================================
# TWILIO MEDIA STREAM
# ============================================================



# ============================================================
# TWILIO MEDIA STREAM STATUS CALLBACK
# ============================================================

@app.post("/stream-status")
async def stream_status(request: Request):
    """
    Receives lifecycle/error information directly from Twilio
    for the bidirectional Media Stream.
    """
    try:
        form = await request.form()

        stream_event = str(
            form.get("StreamEvent") or ""
        ).strip()

        stream_error = str(
            form.get("StreamError") or ""
        ).strip()

        stream_sid = str(
            form.get("StreamSid") or ""
        ).strip()

        call_sid = str(
            form.get("CallSid") or ""
        ).strip()

        print()
        print("=====================================")
        print("📡 TWILIO STREAM STATUS")
        print("=====================================")
        print(f"Event: {stream_event}")
        print(f"Stream SID: {stream_sid}")
        print(f"Call SID: {call_sid}")

        if stream_error:
            print(f"❌ StreamError: {stream_error}")
        else:
            print("✅ No StreamError reported")

        print("=====================================")
        print()

    except Exception as exc:
        print(
            f"⚠️ Stream status callback error: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

    return Response(status_code=204)


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()

    print()
    print("=====================================")
    print("📞 NEW CIVICRESOLVE CALL CONNECTION")
    print("=====================================")
    print("✅ Twilio WebSocket connected")

    stream_sid = None
    call_sid = None
    caller_number = ""

    # Per-call deterministic state. Never shared across calls.
    state = CallState()
    agent = CallAgent()

    stt = DeepgramSTT()
    tts = DeepgramTTS()

    twilio_send_lock = asyncio.Lock()

    stt_listener_task = None
    reply_task = None

    utterance_parts = []
    fast_turn_handled = False

    # Deepgram occasionally sends good interim text but fails
    # to emit a final boundary on telephone audio. This task
    # forces finalization after a short period without transcript
    # updates so the caller is never left waiting indefinitely.
    interim_finalize_task = None

    bot_playback_pending = False
    current_mark_name = None
    tts_active = False
    reply_counter = 0

    call_stopping = False

    # --------------------------------------------------------
    # SPEAK TEXT TO THE CALLER
    # --------------------------------------------------------

    async def speak_text(
        text: str,
        mark_prefix: str,
    ):
        nonlocal bot_playback_pending
        nonlocal current_mark_name
        nonlocal tts_active
        nonlocal reply_counter

        if not stream_sid:
            return

        text = (text or "").strip()
        if not text:
            return

        reply_counter += 1
        mark_name = f"{mark_prefix}_{reply_counter}"

        start_time = time.perf_counter()
        first_audio = True
        total_audio_bytes = 0

        print(f"🤖 SPEAK: {text}")

        tts_active = True

        try:
            async for audio_chunk in tts.stream_synthesize(text):
                if not audio_chunk:
                    continue

                if first_audio:
                    first_audio = False
                    first_audio_ms = (
                        time.perf_counter() - start_time
                    ) * 1000
                    print(
                        f"⚡ First TTS audio: "
                        f"{first_audio_ms:.0f} ms"
                    )

                total_audio_bytes += len(audio_chunk)
                bot_playback_pending = True

                await send_twilio_media(
                    websocket,
                    twilio_send_lock,
                    stream_sid,
                    audio_chunk,
                )

            # A mark is sent after the full response. Twilio sends
            # the same mark back when playback finishes (or is
            # cleared), which lets us track buffered call audio.
            current_mark_name = mark_name

            await send_twilio_mark(
                websocket,
                twilio_send_lock,
                stream_sid,
                mark_name,
            )

            print(
                f"✅ Sent {total_audio_bytes} TTS bytes "
                f"to Twilio (mark={mark_name})"
            )

        except asyncio.CancelledError:
            print("🛑 Bot speech task cancelled")
            raise

        finally:
            tts_active = False

    # --------------------------------------------------------
    # STOP BOT OUTPUT / BARGE-IN
    # --------------------------------------------------------

    async def interrupt_bot(reason: str):
        nonlocal reply_task
        nonlocal bot_playback_pending
        nonlocal current_mark_name

        task = reply_task
        was_tts_active = tts_active

        if stream_sid and bot_playback_pending:
            try:
                await send_twilio_clear(
                    websocket,
                    twilio_send_lock,
                    stream_sid,
                )
                print(
                    f"🧹 Cleared Twilio audio buffer: {reason}"
                )
            except Exception as exc:
                print(
                    f"⚠️ Twilio clear failed: {exc}"
                )

        bot_playback_pending = False
        current_mark_name = None

        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                print(
                    f"⚠️ Cancelled reply task ended with: {exc}"
                )

        reply_task = None

        # If cancellation happened during Flux synthesis, reset
        # the TTS WebSocket so no stale frames from the cancelled
        # turn can leak into the next caller turn.
        if was_tts_active and not call_stopping:
            try:
                await tts.abort_and_reconnect()
                print("🔄 Deepgram TTS reset after barge-in")
            except Exception as exc:
                print(
                    f"⚠️ TTS reset after barge-in failed: {exc}"
                )

    # --------------------------------------------------------
    # AGENT TURN
    # --------------------------------------------------------

    async def run_agent_turn(transcript: str):
        total_start = time.perf_counter()

        print()
        print(f"👤 CALLER: {transcript}")

        try:
            groq_start = time.perf_counter()

            complaint_submitted_now = False

            # -------------------------------------------------
            # MANUAL LOCATION FALLBACK
            # -------------------------------------------------
            # If the citizen declined the photo/GPS link,
            # the next spoken turn is treated as the exact
            # complaint location or nearest landmark.

            if getattr(
                state,
                "awaiting_manual_location",
                False,
            ):
                manual_location = (
                    transcript
                    .strip()
                    .strip(" .,")
                )

                lower_location = manual_location.lower()

                invalid_location_answers = {
                    "yes",
                    "yes yes",
                    "yeah",
                    "yep",
                    "no",
                    "no no",
                    "nope",
                    "i don't know",
                    "i dont know",
                    "not sure",
                }

                if (
                    not manual_location
                    or lower_location
                    in invalid_location_answers
                ):
                    result = {
                        "spoken_reply": (
                            "Please tell me the exact location, "
                            "street, address, or nearest landmark "
                            "for the civic issue."
                        )
                    }

                else:
                    # Remove a few common conversational prefixes
                    # while preserving the actual location.
                    prefixes = [
                        "my location is ",
                        "the location is ",
                        "it is located at ",
                        "it is at ",
                        "it's at ",
                        "located at ",
                    ]

                    cleaned_location = manual_location

                    for prefix in prefixes:
                        if cleaned_location.lower().startswith(
                            prefix
                        ):
                            cleaned_location = (
                                cleaned_location[
                                    len(prefix):
                                ].strip()
                            )
                            break

                    if cleaned_location:
                        state.location = cleaned_location
                    else:
                        state.location = manual_location

                    state.awaiting_manual_location = False
                    state.awaiting_confirmation = True

                    result = {
                        "spoken_reply": (
                            f"Thanks. I have the location as "
                            f"{state.location}. "
                            "Would you like me to submit this "
                            "civic complaint now?"
                        )
                    }

            else:
                result = await agent.handle_turn(
                    state,
                    transcript,
                )

            groq_ms = (
                time.perf_counter() - groq_start
            ) * 1000

            reply = (
                result.get("spoken_reply", "")
                if isinstance(result, dict)
                else ""
            ).strip()

            ready_to_submit = bool(
                result.get("ready_to_submit", False)
                if isinstance(result, dict)
                else False
            )

            # =================================================
            # REAL CIVICRESOLVE SUBMISSION
            # =================================================

            if ready_to_submit:
                print(
                    "🚦 Python submission gate OPEN — "
                    "caller explicitly confirmed",
                    flush=True,
                )

                try:
                    civicresolve = CivicResolveClient()

                    backend_start = time.perf_counter()

                    backend_result = (
                        await civicresolve.submit_complaint(
                            state
                        )
                    )

                    backend_ms = (
                        time.perf_counter()
                        - backend_start
                    ) * 1000

                    complaint_id = (
                        state.complaint_id
                        or backend_result.get(
                            "complaint_id"
                        )
                    )

                    if not complaint_id:
                        raise CivicResolveError(
                            "Submission succeeded but "
                            "no complaint ID was returned."
                        )

                    # Complaint now genuinely exists.
                    state.submitted = True
                    state.complaint_id = str(
                        complaint_id
                    )

                    complaint_submitted_now = True

                    # Evidence permission was already collected
                    # before registration.
                    state.awaiting_evidence_permission = False

                    if state.evidence_opt_in is True:
                        reply = (
                            "Done. Your complaint has been "
                            "registered successfully. "
                            f"Your complaint ID is "
                            f"{state.complaint_id}. "
                            "I am sending your secure evidence "
                            "link to your phone now."
                        )
                    else:
                        reply = (
                            "Done. Your complaint has been "
                            "registered successfully. "
                            f"Your complaint ID is "
                            f"{state.complaint_id}."
                        )

                    print(
                        "✅ REAL CIVICRESOLVE "
                        "SUBMISSION COMPLETE",
                        flush=True,
                    )

                    print(
                        "🎫 REAL COMPLAINT ID:",
                        state.complaint_id,
                        flush=True,
                    )

                    print(
                        f"🏛️ CivicResolve latency: "
                        f"{backend_ms:.0f} ms",
                        flush=True,
                    )

                except CivicResolveError as exc:
                    print(
                        "❌ CIVICRESOLVE SUBMISSION FAILED:",
                        str(exc),
                        flush=True,
                    )

                    # Never falsely tell the citizen that
                    # the complaint was registered.
                    state.submitted = False
                    state.complaint_id = None

                    # Let caller explicitly retry.
                    state.confirmed = False
                    state.awaiting_confirmation = True
                    state.awaiting_evidence_permission = False
                    state.evidence_opt_in = None

                    reply = (
                        "I'm having trouble registering "
                        "your complaint right now. "
                        "It has not been submitted. "
                        "Would you like me to try again?"
                    )

                except Exception as exc:
                    print(
                        "❌ UNEXPECTED SUBMISSION ERROR:",
                        f"{type(exc).__name__}: {exc}",
                        flush=True,
                    )

                    state.submitted = False
                    state.complaint_id = None
                    state.confirmed = False
                    state.awaiting_confirmation = True
                    state.awaiting_evidence_permission = False
                    state.evidence_opt_in = None

                    reply = (
                        "I'm having trouble registering "
                        "your complaint right now. "
                        "It has not been submitted. "
                        "Would you like me to try again?"
                    )

            # =================================================
            # SECURE EVIDENCE LINK SMS
            # =================================================

            if (
                complaint_submitted_now
                and state.evidence_opt_in is True
                and state.submitted
                and state.complaint_id
                and not state.evidence_link_sent
            ):
                recipient = (
                    caller_number
                    or os.getenv(
                        "BROWSER_TEST_SMS_TO",
                        "",
                    ).strip()
                )

                if recipient:
                    token = None
                    link_store = None

                    try:
                        link_store = EvidenceLinkStore()

                        token = link_store.issue(
                            state.complaint_id
                        )

                        public_host = get_public_host()

                        if not public_host:
                            raise RuntimeError(
                                "PUBLIC_HOST is not configured"
                            )

                        evidence_url = (
                            f"https://{public_host}"
                            f"/evidence/{token}"
                        )

                        print(
                            f"🔗 Evidence links use: "
                            f"https://{public_host}/evidence/<token>",
                            flush=True,
                        )

                        sms = CivicResolveSMS()

                        await asyncio.to_thread(
                            sms.send_evidence_link,
                            recipient,
                            state.complaint_id,
                            evidence_url,
                        )

                        state.evidence_link_sent = True

                        reply = (
                            f"Done. Your complaint "
                            f"{state.complaint_id} is registered, "
                            "and I sent the secure evidence link "
                            "to your phone. You can use it to add "
                            "a photo and your current location."
                        )

                        print(
                            "✅ SECURE EVIDENCE SMS SENT",
                            flush=True,
                        )

                    except Exception as exc:
                        if token and link_store:
                            try:
                                link_store.revoke(token)
                            except Exception:
                                pass

                        state.evidence_link_sent = False

                        # Complaint is already registered.
                        # Do not return to the pre-submission
                        # evidence-permission state.
                        state.awaiting_evidence_permission = False

                        print(
                            "❌ EVIDENCE SMS FAILED:",
                            f"{type(exc).__name__}: {exc}",
                            flush=True,
                        )

                        reply = (
                            f"Your complaint {state.complaint_id} "
                            "is registered, but I could not send "
                            "the evidence link right now."
                        )

                else:
                    print(
                        "⚠️ No SMS recipient available",
                        flush=True,
                    )

                    reply = (
                        "Your complaint is registered, "
                        "but I do not have a mobile number "
                        "to send the evidence link to. "
                        "Your complaint is not affected."
                    )

            print(f"🤖 CIVICRESOLVE: {reply}")
            print(
                f"⏱️ Agent latency: "
                f"{groq_ms:.0f} ms"
            )

            await speak_text(
                reply,
                "civicresolve_reply",
            )

            total_ms = (
                time.perf_counter()
                - total_start
            ) * 1000

            print(
                f"⏱️ Total turn pipeline: "
                f"{total_ms:.0f} ms"
            )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(
                f"❌ Agent reply pipeline error: "
                f"{type(exc).__name__}: {exc}"
            )

    async def start_agent_turn(transcript: str):
        nonlocal reply_task

        transcript = (transcript or "").strip()
        if not transcript:
            return

        # A completed new caller turn supersedes any unfinished
        # bot work from the previous turn.
        if reply_task is not None and not reply_task.done():
            await interrupt_bot(
                "new caller utterance"
            )

        reply_task = asyncio.create_task(
            run_agent_turn(transcript)
        )

    # --------------------------------------------------------
    # STT FINALIZATION WATCHDOG
    # --------------------------------------------------------

    async def force_stt_finalize_after_pause():
        """
        Deepgram normally emits a final result automatically.
        On some phone calls it can keep returning only interim
        transcripts. If no transcript update arrives for a short
        time, force the current utterance to finalize.
        """
        try:
            await asyncio.sleep(1.6)

            if call_stopping:
                return

            print(
                "⏱️ STT pause detected — forcing transcript finalize",
                flush=True,
            )

            await stt.finalize()

        except asyncio.CancelledError:
            pass

        except Exception as exc:
            print(
                f"⚠️ STT forced-finalize error: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )


    def reset_stt_finalize_watchdog():
        nonlocal interim_finalize_task

        if (
            interim_finalize_task is not None
            and not interim_finalize_task.done()
        ):
            interim_finalize_task.cancel()

        interim_finalize_task = asyncio.create_task(
            force_stt_finalize_after_pause()
        )


    def cancel_stt_finalize_watchdog():
        nonlocal interim_finalize_task

        if (
            interim_finalize_task is not None
            and not interim_finalize_task.done()
        ):
            interim_finalize_task.cancel()

        interim_finalize_task = None


    # --------------------------------------------------------
    # DEEPGRAM STT LISTENER
    # --------------------------------------------------------

    async def listen_to_deepgram():
        nonlocal utterance_parts
        nonlocal fast_turn_handled

        async for result in stt.receive():
            result_type = result.get("type")

            # Deepgram SpeechStarted is intentionally NOT used
            # to interrupt bot playback by itself. Telephone line
            # noise and DTMF tones can trigger VAD even when the
            # caller has not spoken. We wait for a non-empty
            # transcript before treating this as real barge-in.
            if result_type == "speech_started":
                if (
                    bot_playback_pending
                    or (
                        reply_task is not None
                        and not reply_task.done()
                    )
                ):
                    print(
                        "🎙️ Possible caller speech detected "
                        "— waiting for transcript confirmation"
                    )
                continue

            if result_type == "utterance_end":
                cancel_stt_finalize_watchdog()

                if utterance_parts and not fast_turn_handled:
                    full_utterance = " ".join(
                        utterance_parts
                    ).strip()
                    utterance_parts = []

                    if full_utterance:
                        await start_agent_turn(
                            full_utterance
                        )
                continue

            if result_type != "transcript":
                continue

            transcript = result.get(
                "transcript",
                "",
            ).strip()

            is_final = bool(
                result.get("is_final", False)
            )

            speech_final = bool(
                result.get("speech_final", False)
            )

            # If a short answer was already handled from a final
            # segment, suppress duplicate segments belonging to
            # that same caller speech turn until speech_final.
            if fast_turn_handled:
                if speech_final:
                    fast_turn_handled = False
                    utterance_parts = []
                    print("✅ Fast-turn boundary completed")
                continue

            if not transcript:
                continue

            # Confirm barge-in only when Deepgram has recognized
            # actual speech text. This prevents DTMF/line-noise
            # VAD events from clearing the greeting or a reply.
            if (
                bot_playback_pending
                or (
                    reply_task is not None
                    and not reply_task.done()
                )
            ):
                print(
                    f"🗣️ Confirmed caller barge-in: {transcript}"
                )
                await interrupt_bot(
                    "caller transcript detected"
                )

            if not is_final:
                print(f"… STT: {transcript}")

                # Every new interim transcript restarts the timer.
                # If the caller stops speaking and Deepgram fails
                # to send a final boundary, finalize it ourselves.
                reset_stt_finalize_watchdog()

                continue

            cancel_stt_finalize_watchdog()

            print(f"📝 STT FINAL: {transcript}")
            utterance_parts.append(transcript)

            normalized = normalize_short_answer(
                transcript
            )

            if normalized in SHORT_ANSWERS:
                full_utterance = " ".join(
                    utterance_parts
                ).strip()
                utterance_parts = []

                print(
                    f"⚡ Fast short-answer detected: "
                    f"{full_utterance}"
                )

                fast_turn_handled = not speech_final

                await start_agent_turn(
                    full_utterance
                )
                continue

            if speech_final:
                full_utterance = " ".join(
                    utterance_parts
                ).strip()
                utterance_parts = []

                if full_utterance:
                    await start_agent_turn(
                        full_utterance
                    )

    # --------------------------------------------------------
    # CALL LIFECYCLE
    # --------------------------------------------------------

    try:
        await stt.connect()
        await tts.connect()

        stt_listener_task = asyncio.create_task(
            listen_to_deepgram()
        )

        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                print("✅ Twilio protocol connected")
                continue

            if event == "start":
                start_data = data.get("start", {})

                stream_sid = (
                    start_data.get("streamSid")
                    or data.get("streamSid")
                )
                call_sid = start_data.get("callSid")

                custom_parameters = (
                    start_data.get(
                        "customParameters",
                        {}
                    )
                    or {}
                )

                caller_number = str(
                    custom_parameters.get(
                        "caller_number",
                        ""
                    )
                    or ""
                ).strip()

                state.stream_sid = stream_sid
                state.call_sid = call_sid

                print(f"✅ Stream started: {stream_sid}")
                print(f"📞 Call SID: {call_sid}")
                print(
                    "🎧 Media format:",
                    start_data.get("mediaFormat", {}),
                )

                # Delay the opening greeting very slightly so
                # startup DTMF/line transients settle before we
                # begin playback. The receive loop remains fully
                # responsive during this delay.
                async def play_opening_greeting():
                    await asyncio.sleep(0.6)
                    if call_stopping:
                        return
                    await speak_text(
                        "CivicResolve. What would you like to report?",
                        "greeting",
                    )

                if reply_task is None or reply_task.done():
                    reply_task = asyncio.create_task(
                        play_opening_greeting()
                    )

                continue

            if event == "media":
                media = data.get("media", {})
                track = media.get("track")

                if track is not None and track != "inbound":
                    continue

                payload = media.get("payload")
                if not payload:
                    continue

                try:
                    audio_bytes = base64.b64decode(payload)
                except Exception as exc:
                    print(
                        f"⚠️ Invalid Twilio audio payload: {exc}"
                    )
                    continue

                await stt.send_audio(audio_bytes)
                continue

            if event == "mark":
                mark_name = (
                    data.get("mark", {})
                    .get("name")
                )

                print(f"🔖 Twilio mark: {mark_name}")

                if (
                    mark_name
                    and mark_name == current_mark_name
                ):
                    bot_playback_pending = False
                    current_mark_name = None
                    print("✅ Bot playback completed")

                continue

            if event == "dtmf":
                digit = (
                    data.get("dtmf", {})
                    .get("digit")
                )
                print(f"☎️ DTMF: {digit}")
                continue

            if event == "stop":
                print("🛑 Twilio stream stopped", flush=True)
                break

            if event:
                print(f"ℹ️ Twilio event: {event}")

    except WebSocketDisconnect:
        print("📞 Twilio WebSocket disconnected", flush=True)

    except Exception as exc:
        print(
            f"❌ Call pipeline error: "
            f"{type(exc).__name__}: {exc}"
        )

    finally:
        call_stopping = True

        if (
            interim_finalize_task is not None
            and not interim_finalize_task.done()
        ):
            interim_finalize_task.cancel()

            try:
                await interim_finalize_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if reply_task is not None and not reply_task.done():
            reply_task.cancel()
            try:
                await reply_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if stt_listener_task is not None:
            stt_listener_task.cancel()
            try:
                await stt_listener_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        try:
            await stt.close()
        except Exception as exc:
            print(f"⚠️ STT cleanup error: {exc}")

        try:
            await tts.close()
        except Exception as exc:
            print(f"⚠️ TTS cleanup error: {exc}")

        print("🧹 Call resources cleaned up")
        print("=====================================")
        print()
