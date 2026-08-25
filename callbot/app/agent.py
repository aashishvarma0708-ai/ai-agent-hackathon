import os
import re
import json
import asyncio

from groq import AsyncGroq

from app.call_state import CallState
from app.router import resolve_route


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are the language-understanding layer for CivicResolve,
a friendly public-service phone assistant.

The caller should feel like they are speaking with a helpful
human civic-service operator.

Python controls:
- safety
- routing
- required information
- question order
- confirmation
- complaint submission
- evidence permission
- SMS/link sending

You interpret what the caller says.

Do not try to control the workflow yourself.

Extract these fields:

1. route

municipal
emergency
other
unknown


2. issue

A short description of the civic/public-service issue.

Examples:
- pothole
- garbage accumulation
- blocked drainage
- broken streetlight
- water leakage
- road damage
- sewage overflow


3. location

ONLY a location actually spoken by the caller.

Never invent or expand the location.


4. severity

low
medium
high
null

Only provide a severity if the caller actually gives enough
information to support it.

Do not automatically classify an ordinary complaint as low.


5. safety_risk

true ONLY when the caller explicitly describes an immediate
public or road-safety danger.

Examples:
- vehicles are swerving
- someone could get hurt
- pedestrians are in danger
- exposed electrical wires
- dangerous open drain
- road is causing accidents

false ONLY when the caller explicitly says there is no
immediate safety risk, OR the current Python state shows that
the safety question was asked and the caller clearly answers no.

null when safety has not yet been established.

IMPORTANT:

Never infer safety_risk=false merely because the caller did
not mention danger.

Silence about safety means null, not false.


6. language

en
hi
mixed


ROUTING

Municipal examples:
- potholes
- damaged roads
- garbage
- drainage
- sewage
- streetlights
- water leaks
- local flooding
- damaged municipal infrastructure

Emergency examples:
- active fire
- serious medical emergency
- violent crime in progress
- person trapped
- building collapse involving people
- immediate danger to life

Other:
Something that is neither a municipal civic complaint nor an
immediate emergency.


BEHAVIOR

Understand English, Hindi and Hinglish.

Never invent:
- complaint IDs
- locations
- departments
- authorities
- emergency numbers
- evidence URLs

Never claim a complaint has already been submitted.

Never claim an SMS or evidence link was sent.

Python performs those actions.

Keep spoken_reply very short and natural.

Python may replace spoken_reply with the correct next question.
"""


# =========================================================
# STRICT STRUCTURED OUTPUT
# =========================================================

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name":
            "civicresolve_call_turn",

        "strict":
            True,

        "schema": {
            "type":
                "object",

            "properties": {
                "spoken_reply": {
                    "type":
                        "string",
                },

                "route": {
                    "type":
                        "string",

                    "enum": [
                        "municipal",
                        "emergency",
                        "other",
                        "unknown",
                    ],
                },

                "issue": {
                    "type": [
                        "string",
                        "null",
                    ],
                },

                "location": {
                    "type": [
                        "string",
                        "null",
                    ],
                },

                "severity": {
                    "type": [
                        "string",
                        "null",
                    ],

                    "enum": [
                        "low",
                        "medium",
                        "high",
                        None,
                    ],
                },

                "safety_risk": {
                    "type": [
                        "boolean",
                        "null",
                    ],
                },

                "language": {
                    "type":
                        "string",

                    "enum": [
                        "en",
                        "hi",
                        "mixed",
                    ],
                },
            },

            "required": [
                "spoken_reply",
                "route",
                "issue",
                "location",
                "severity",
                "safety_risk",
                "language",
            ],

            "additionalProperties":
                False,
        },
    },
}


# =========================================================
# SHORT YES / NO DETECTION
# =========================================================

YES_PHRASES = {
    "yes",
    "yes please",
    "yeah",
    "yep",
    "sure",
    "correct",
    "confirm",
    "confirmed",
    "submit",
    "submit it",
    "please submit",
    "go ahead",
    "do it",
    "true",
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
    "yes fine",
    "yes okay",
    "yes ok",
    "okay sure",
    "ok sure",
    "sure yeah",
    "go for it",
    "please do",
    "please do it",

    "haan",
    "han",
    "ha",
    "haan ji",
    "ji",
    "kar do",
    "submit kar do",

    "हाँ",
    "हां",
    "जी",
}


NO_PHRASES = {
    "no",
    "nope",
    "false",
    "don't",
    "do not",
    "cancel",
    "not yet",
    "change it",

    "nahi",
    "nahin",
    "mat karo",

    "नहीं",
}


def normalize_answer(
    text: str,
) -> str:

    text = (
        text
        or ""
    ).strip().lower()

    text = re.sub(
        r"[^\w\s\u0900-\u097f']",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def is_yes(
    text: str,
) -> bool:
    normalized = normalize_answer(text)

    if normalized in YES_PHRASES:
        return True

    natural_yes = {
        "yes i do",
        "yes do it",
        "yeah do it",
        "yep do it",
        "do it",
        "yes go ahead",
        "sure do it",
        "ok do it",
        "okay do it",
        "yes please",
        "yes sure",
        "sure",
        "sure please",
        "please do",
        "go ahead",
        "absolutely",
        "of course",
        "yes send it",
        "send it",
        "send me the link",
    }

    return normalized in natural_yes


def is_no(
    text: str,
) -> bool:
    normalized = normalize_answer(text)

    if normalized in NO_PHRASES:
        return True

    natural_no = {
        "no thanks",
        "no thank you",
        "not now",
        "please dont",
        "please don't",
        "dont send it",
        "don't send it",
        "do not send it",
        "i dont want it",
        "i don't want it",
        "skip it",
    }

    return normalized in natural_no


# =========================================================
# SAFETY LANGUAGE
# =========================================================

def explicitly_says_no_risk(
    text: str,
) -> bool:

    normalized = normalize_answer(
        text
    )

    phrases = [
        "no safety risk",
        "not a safety risk",
        "not dangerous",
        "no danger",
        "nobody is in danger",
        "no one is in danger",
        "not causing danger",
        "no immediate risk",
        "safe right now",
        "there is no risk",
        "there is no danger",
    ]

    return any(
        phrase in normalized
        for phrase in phrases
    )


def explicitly_describes_risk(
    text: str,
) -> bool:

    normalized = normalize_answer(
        text
    )

    phrases = [
        "swerving",
        "swerve",
        "accident",
        "accidents",
        "danger",
        "dangerous",
        "could get hurt",
        "can get hurt",
        "someone may get hurt",
        "someone could get hurt",
        "pedestrian",
        "pedestrians",
        "exposed wire",
        "exposed wires",
        "electric shock",
        "people are falling",
        "people could fall",
        "vehicles are avoiding",
        "cars are avoiding",
        "bikes are avoiding",
        "immediate risk",
        "safety risk",
    ]

    return any(
        phrase in normalized
        for phrase in phrases
    )


# =========================================================
# CALL AGENT
# =========================================================

class CallAgent:
    def __init__(
        self,
    ):
        api_key = os.getenv(
            "GROQ_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing"
            )

        self.model = (
            os.getenv(
                "GROQ_MODEL",
                "",
            ).strip()
            or
            "openai/gpt-oss-20b"
        )

        self.emergency_number = os.getenv(
            "EMERGENCY_NUMBER",
            "",
        ).strip()

        self.client = AsyncGroq(
            api_key=api_key,
            timeout=15.0,
            max_retries=1,
        )


    # =====================================================
    # GROQ
    # =====================================================

    async def _ask_groq(
        self,
        state: CallState,
        caller_text: str,
    ) -> dict:

        messages = [
            {
                "role":
                    "system",

                "content":
                    SYSTEM_PROMPT,
            },

            {
                "role":
                    "system",

                "content":
                    (
                        "CURRENT PYTHON CALL STATE:\n"
                        + state.prompt_context()
                    ),
            },
        ]

        messages.extend(
            state.history[-8:]
        )

        messages.append(
            {
                "role":
                    "user",

                "content":
                    caller_text,
            }
        )

        last_error = None

        for attempt in range(2):
            try:
                token_limit = (
                    1200
                    if attempt == 0
                    else 1800
                )

                response = await (
                    self.client
                    .chat
                    .completions
                    .create(
                        model=
                            self.model,

                        messages=
                            messages,

                        response_format=
                            RESPONSE_SCHEMA,

                        temperature=
                            0.1,

                        max_completion_tokens=
                            token_limit,

                        stream=
                            False,
                    )
                )

                if not response.choices:
                    raise ValueError(
                        "Groq returned no choices"
                    )

                choice = (
                    response.choices[0]
                )

                content = (
                    choice.message.content
                    or ""
                ).strip()

                if not content:
                    finish_reason = getattr(
                        choice,
                        "finish_reason",
                        None,
                    )

                    raise ValueError(
                        "Groq returned empty "
                        "structured content; "
                        f"finish_reason="
                        f"{finish_reason!r}"
                    )

                data = json.loads(
                    content
                )

                if not isinstance(
                    data,
                    dict,
                ):
                    raise ValueError(
                        "Structured Groq output "
                        "was not an object"
                    )

                return data

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                last_error = exc

                print(
                    f"⚠️ Groq attempt "
                    f"{attempt + 1}/2 failed:",
                    repr(exc),
                    flush=True,
                )

                if attempt == 0:
                    await asyncio.sleep(
                        0.2
                    )

        raise RuntimeError(
            "Groq failed after 2 attempts: "
            f"{last_error!r}"
        )


    # =====================================================
    # APPLY LLM EXTRACTION TO PYTHON STATE
    # =====================================================

    def _update_state(
        self,
        state: CallState,
        data: dict,
        caller_text: str,
    ):
        issue = data.get(
            "issue"
        )

        if (
            isinstance(issue, str)
            and issue.strip()
        ):
            state.issue = (
                issue.strip()
            )

        location = data.get(
            "location"
        )

        if (
            isinstance(location, str)
            and location.strip()
        ):
            state.location = (
                location.strip()
            )

        severity = data.get(
            "severity"
        )

        if severity in {
            "low",
            "medium",
            "high",
        }:
            state.severity = (
                severity
            )

        safety_risk = data.get(
            "safety_risk"
        )

        # Do not blindly trust a TRUE generated
        # from an ordinary complaint.
        if safety_risk is True:

            if (
                state.awaiting_safety_answer
                or explicitly_describes_risk(
                    caller_text
                )
            ):
                state.safety_risk = True
                state.awaiting_safety_answer = False

        # FALSE is even more tightly controlled.
        # "The caller didn't mention danger"
        # never means False.
        elif safety_risk is False:

            if (
                state.awaiting_safety_answer
                or explicitly_says_no_risk(
                    caller_text
                )
            ):
                state.safety_risk = False
                state.awaiting_safety_answer = False

        language = data.get(
            "language"
        )

        if language in {
            "en",
            "hi",
            "mixed",
        }:
            state.language = (
                language
            )


    # =====================================================
    # MUNICIPAL CONVERSATION
    # =====================================================

    def _municipal_next_reply(
        self,
        state: CallState,
    ) -> str:

        if not state.issue:
            return (
                "Sure, I can help with that. "
                "What civic issue would you "
                "like to report?"
            )

        if not state.location:
            return (
                "Got it. Where exactly is "
                "the issue located?"
            )

        if state.safety_risk is None:
            state.awaiting_safety_answer = True

            return (
                "Thanks. Is this creating any "
                "immediate safety risk, like "
                "vehicles swerving, pedestrians "
                "being in danger, or someone "
                "getting hurt?"
            )

        state.awaiting_safety_answer = False

        # Ask for optional evidence permission BEFORE
        # the final complaint submission confirmation.
        state.awaiting_confirmation = False
        state.awaiting_evidence_permission = True

        summary = (
            state.natural_summary()
        )

        return (
            f"Okay. I have a report of "
            f"{summary}. "
            "Before I submit it, would you like me "
            "to send you a secure link after registration "
            "so you can add a photo and your current location?"
        )


    # =====================================================
    # FALLBACK
    # =====================================================

    def _fallback_reply(
        self,
        state: CallState,
    ) -> str:

        if state.route == "municipal":
            return (
                self._municipal_next_reply(
                    state
                )
            )

        return (
            "Sorry, I didn't catch that clearly. "
            "Could you say it again briefly?"
        )


    # =====================================================
    # EMERGENCY
    # =====================================================

    def _emergency_reply(
        self,
    ) -> str:

        if self.emergency_number:
            return (
                "This sounds like an emergency. "
                f"Please contact "
                f"{self.emergency_number} "
                "immediately. I won't create a "
                "municipal complaint for this."
            )

        return (
            "This sounds like an emergency. "
            "Please contact your local emergency "
            "services immediately. I won't create "
            "a municipal complaint for this."
        )


    # =====================================================
    # STANDARD RESPONSE OBJECT
    # =====================================================

    def _result(
        self,
        state: CallState,
        reply: str,
        ready_to_submit: bool = False,
    ) -> dict:

        state.last_bot_text = reply

        return {
            "spoken_reply":
                reply,

            "route":
                state.route,

            "ready_to_submit":
                ready_to_submit,

            "state":
                state.to_dict(),
        }


    # =====================================================
    # MAIN TURN HANDLER
    # =====================================================

    async def handle_turn(
        self,
        state: CallState,
        caller_text: str,
    ) -> dict:

        caller_text = (
            caller_text
            or ""
        ).strip()

        if not caller_text:
            return self._result(
                state,
                (
                    "I didn't catch that. "
                    "Could you say that again?"
                ),
                False,
            )

        state.turn_count += 1

        state.last_user_text = (
            caller_text
        )


        # =================================================
        # PHOTO + LOCATION LINK PERMISSION
        # =================================================

        if (
            state.awaiting_evidence_permission
            and state.route == "municipal"
        ):

            if is_yes(
                caller_text
            ):
                state.evidence_opt_in = True
                state.awaiting_evidence_permission = False
                state.awaiting_confirmation = True

                reply = (
                    "Great. I will send the secure evidence "
                    "link after the complaint is registered. "
                    "Would you like me to submit this civic "
                    "complaint now?"
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    False,
                )

            if is_no(
                caller_text
            ):
                state.evidence_opt_in = False
                state.awaiting_evidence_permission = False

                # Without the secure link we cannot obtain GPS,
                # so collect a precise spoken location instead.
                state.awaiting_confirmation = False
                state.awaiting_manual_location = True

                reply = (
                    "No problem. I will not send an evidence "
                    "link. Before I submit the complaint, "
                    "please tell me the exact location, address, "
                    "or nearest landmark."
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    False,
                )

            reply = (
                "Would you like me to send you "
                "a secure link for adding a photo "
                "and your current location? "
                "Please say yes or no."
            )

            return self._result(
                state,
                reply,
                False,
            )


        # =================================================
        # COMPLETED CALL GUARD
        # =================================================
        #
        # Once the real complaint has been registered and
        # evidence consent has been resolved, never fall back
        # into complaint extraction / confirmation again.

        if (
            state.submitted
            and not state.awaiting_evidence_permission
        ):
            complaint_id = (
                state.complaint_id
                or "your complaint"
            )

            if state.evidence_link_sent:
                reply = (
                    "You're welcome. "
                    f"Your complaint {complaint_id} "
                    "is registered, and the secure "
                    "evidence link has been sent to "
                    "your phone. Goodbye."
                )

            elif state.evidence_opt_in is False:
                reply = (
                    "You're welcome. "
                    f"Your complaint {complaint_id} "
                    "is registered. No evidence link "
                    "was requested. Goodbye."
                )

            else:
                reply = (
                    "You're welcome. "
                    f"Your complaint {complaint_id} "
                    "is registered. Goodbye."
                )

            state.add_history(
                "user",
                caller_text,
            )

            state.add_history(
                "assistant",
                reply,
            )

            return self._result(
                state,
                reply,
                False,
            )


        # =================================================
        # FINAL COMPLAINT SUBMISSION CONFIRMATION
        # =================================================

        if (
            state.awaiting_confirmation
            and state.route == "municipal"
        ):

            if is_yes(
                caller_text
            ):
                state.confirmed = True
                state.awaiting_confirmation = False

                # Evidence consent was already collected
                # before this final submission confirmation.
                state.awaiting_evidence_permission = False

                reply = (
                    "Okay. I have your permission. "
                    "I am submitting the civic complaint now."
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    state.ready_to_submit(),
                )

            if is_no(
                caller_text
            ):
                state.confirmed = False
                state.awaiting_confirmation = False

                reply = (
                    "Of course. Tell me what "
                    "you'd like to change in "
                    "the complaint."
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    False,
                )

            reply = (
                "Just to confirm, would you like "
                "me to submit this civic complaint? "
                "Please say yes or no."
            )

            return self._result(
                state,
                reply,
                False,
            )


        # =================================================
        # SAFETY QUESTION
        # =================================================

        if (
            state.awaiting_safety_answer
            and state.route == "municipal"
        ):

            # Short "yes"
            if is_yes(
                caller_text
            ):
                state.safety_risk = True
                state.awaiting_safety_answer = False

                reply = (
                    self._municipal_next_reply(
                        state
                    )
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    False,
                )

            # Short "no"
            if is_no(
                caller_text
            ):
                state.safety_risk = False
                state.awaiting_safety_answer = False

                reply = (
                    self._municipal_next_reply(
                        state
                    )
                )

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return self._result(
                    state,
                    reply,
                    False,
                )

            # Longer answers like:
            #
            # "Yes, cars are swerving around it"
            #
            # continue to Groq below.


        # =================================================
        # GROQ INTERPRETATION
        # =================================================

        try:
            data = await self._ask_groq(
                state,
                caller_text,
            )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(
                "❌ Groq agent error:",
                repr(exc),
                flush=True,
            )

            reply = (
                self._fallback_reply(
                    state
                )
            )

            return self._result(
                state,
                reply,
                False,
            )


        # =================================================
        # UPDATE STATE
        # =================================================

        self._update_state(
            state,
            data,
            caller_text,
        )


        # =================================================
        # PUBLIC-SERVICE ROUTING
        # =================================================

        proposed_route = (
            data.get("route")
            or "unknown"
        )

        route, reason = resolve_route(
            proposed_route,
            caller_text,
        )

        # When a municipal conversation is already
        # underway, a simple location or follow-up
        # answer should not accidentally reset the
        # route to unknown.
        if (
            route == "unknown"
            and state.route == "municipal"
        ):
            route = "municipal"

            reason = (
                "Preserved active municipal "
                "conversation"
            )

        state.route = route
        state.route_reason = reason


        # =================================================
        # EMERGENCY
        # =================================================

        if route == "emergency":
            state.confirmed = False
            state.awaiting_confirmation = False
            state.awaiting_safety_answer = False
            state.awaiting_evidence_permission = False

            reply = (
                self._emergency_reply()
            )


        # =================================================
        # OUT OF SCOPE
        # =================================================

        elif route == "other":
            state.confirmed = False
            state.awaiting_confirmation = False
            state.awaiting_safety_answer = False
            state.awaiting_evidence_permission = False

            reply = (
                data.get(
                    "spoken_reply"
                )
                or
                (
                    "That doesn't appear to be "
                    "a municipal civic complaint."
                )
            )


        # =================================================
        # MUNICIPAL
        # =================================================

        elif route == "municipal":

            reply = (
                self._municipal_next_reply(
                    state
                )
            )


        # =================================================
        # UNKNOWN
        # =================================================

        else:
            reply = (
                data.get(
                    "spoken_reply"
                )
                or
                (
                    "Tell me briefly what "
                    "problem you'd like to report."
                )
            )


        # =================================================
        # SAVE HISTORY
        # =================================================

        reply = str(
            reply
        ).strip()

        state.add_history(
            "user",
            caller_text,
        )

        state.add_history(
            "assistant",
            reply,
        )

        return self._result(
            state,
            reply,
            state.ready_to_submit(),
        )
