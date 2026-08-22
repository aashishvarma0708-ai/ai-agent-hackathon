import os
import re
import json
import asyncio

from groq import AsyncGroq

from app.call_state import CallState
from app.router import resolve_route


SYSTEM_PROMPT = """
You are the language-understanding layer for CivicResolve,
a public-service phone assistant.

Python controls:
- safety
- routing enforcement
- what question is asked next
- confirmation
- complaint submission

You only interpret what the caller said.

Extract:

1. route
   municipal
   emergency
   other
   unknown

2. issue
   Short civic/public-service issue description.

3. location
   ONLY a location actually stated by the caller.

4. severity
   low
   medium
   high
   null

5. safety_risk
   true if the caller describes an immediate road/public safety risk
   false if they explicitly say there is no immediate safety risk
   null if this has not yet been established

6. language
   en
   hi
   mixed

Municipal examples:
- potholes
- broken roads
- garbage
- drainage
- sewage
- streetlights
- water leaks
- flooding
- damaged municipal infrastructure

Emergency examples:
- active fire
- serious medical emergency
- violent crime in progress
- person trapped
- building collapse involving people
- immediate danger to life

Never invent:
- location
- complaint ID
- authority
- emergency number
- department

Understand English, Hindi and Hinglish.

spoken_reply should be a very short natural acknowledgement.
Python may ignore it and generate the actual next question.
"""


RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "civicresolve_call_turn",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "spoken_reply": {
                    "type": "string",
                },
                "route": {
                    "type": "string",
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
                    "type": "string",
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
            "additionalProperties": False,
        },
    },
}


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


def normalize_answer(text: str) -> str:
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


def is_yes(text: str) -> bool:
    return normalize_answer(text) in YES_PHRASES


def is_no(text: str) -> bool:
    return normalize_answer(text) in NO_PHRASES


class CallAgent:
    def __init__(self):
        api_key = os.getenv(
            "GROQ_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is missing"
            )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        ).strip()

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
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content":
                    "CURRENT CALL STATE:\n"
                    + state.prompt_context(),
            },
        ]

        # Keep only recent conversation turns.
        messages.extend(
            state.history[-8:]
        )

        messages.append(
            {
                "role": "user",
                "content": caller_text,
            }
        )

        last_error = None

        for attempt in range(2):
            try:
                token_limit = (
                    1600
                    if attempt == 0
                    else 2400
                )

                response = await (
                    self.client
                    .chat
                    .completions
                    .create(
                        model=self.model,
                        messages=messages,
                        response_format=RESPONSE_SCHEMA,
                        reasoning_effort="low",
                        temperature=0.1,
                        max_completion_tokens=token_limit,
                        stream=False,
                    )
                )

                if not response.choices:
                    raise ValueError(
                        "Groq returned no choices"
                    )

                choice = response.choices[0]

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
                        "Groq returned empty structured "
                        f"content; finish_reason="
                        f"{finish_reason!r}"
                    )

                data = json.loads(content)

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
    # STATE UPDATES
    # =====================================================

    def _update_state(
        self,
        state: CallState,
        data: dict,
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
            state.severity = severity

        safety_risk = data.get(
            "safety_risk"
        )

        if isinstance(
            safety_risk,
            bool,
        ):
            state.safety_risk = (
                safety_risk
            )

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
    # DETERMINISTIC NEXT QUESTION
    # =====================================================

    def _municipal_next_reply(
        self,
        state: CallState,
    ) -> str:

        if not state.issue:
            return (
                "What civic issue would you "
                "like to report?"
            )

        if not state.location:
            return (
                "Where is the issue located?"
            )

        if state.safety_risk is None:
            return (
                "Is this causing an immediate "
                "safety risk, such as vehicles "
                "swerving or people being in danger?"
            )

        state.awaiting_confirmation = True

        summary = (
            state.complaint_summary()
        )

        return (
            f"I have {summary}. "
            "Should I submit this civic complaint?"
        )


    def _fallback_reply(
        self,
        state: CallState,
    ) -> str:

        if state.route == "municipal":
            return self._municipal_next_reply(
                state
            )

        return (
            "I didn't understand that clearly. "
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
                f"Please call "
                f"{self.emergency_number} "
                "immediately. I will not create "
                "a civic complaint for this."
            )

        return (
            "This sounds like an emergency. "
            "Please contact your local emergency "
            "services immediately. I will not "
            "create a civic complaint for this."
        )


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
            return {
                "spoken_reply":
                    "I didn't catch that. "
                    "Could you say that again?",
                "route":
                    state.route,
                "ready_to_submit":
                    False,
                "state":
                    state.to_dict(),
            }

        state.turn_count += 1
        state.last_user_text = (
            caller_text
        )

        # =================================================
        # FINAL SUBMISSION CONFIRMATION
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

                reply = (
                    "Confirmed. I have your "
                    "permission to submit the "
                    "civic complaint."
                )

                state.last_bot_text = reply

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return {
                    "spoken_reply":
                        reply,
                    "route":
                        state.route,
                    "ready_to_submit":
                        state.ready_to_submit(),
                    "state":
                        state.to_dict(),
                }

            if is_no(
                caller_text
            ):
                state.confirmed = False
                state.awaiting_confirmation = False

                reply = (
                    "Okay. Tell me what you "
                    "would like to change."
                )

                state.last_bot_text = reply

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return {
                    "spoken_reply":
                        reply,
                    "route":
                        state.route,
                    "ready_to_submit":
                        False,
                    "state":
                        state.to_dict(),
                }

            reply = (
                "Please say yes to submit, "
                "or no if you want to change "
                "the complaint."
            )

            state.last_bot_text = reply

            return {
                "spoken_reply":
                    reply,
                "route":
                    state.route,
                "ready_to_submit":
                    False,
                "state":
                    state.to_dict(),
            }


        # =================================================
        # SAFETY-RISK YES/NO
        #
        # If we already know the issue and location,
        # a simple yes/no now refers to the safety-risk
        # question, NOT complaint submission.
        # =================================================

        if (
            state.route == "municipal"
            and state.issue
            and state.location
            and state.safety_risk is None
        ):

            if is_yes(
                caller_text
            ):
                state.safety_risk = True

                reply = (
                    self._municipal_next_reply(
                        state
                    )
                )

                state.last_bot_text = reply

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return {
                    "spoken_reply":
                        reply,
                    "route":
                        state.route,
                    "ready_to_submit":
                        False,
                    "state":
                        state.to_dict(),
                }

            if is_no(
                caller_text
            ):
                state.safety_risk = False

                reply = (
                    self._municipal_next_reply(
                        state
                    )
                )

                state.last_bot_text = reply

                state.add_history(
                    "user",
                    caller_text,
                )

                state.add_history(
                    "assistant",
                    reply,
                )

                return {
                    "spoken_reply":
                        reply,
                    "route":
                        state.route,
                    "ready_to_submit":
                        False,
                    "state":
                        state.to_dict(),
                }


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

            state.last_bot_text = reply

            return {
                "spoken_reply":
                    reply,
                "route":
                    state.route,
                "ready_to_submit":
                    False,
                "state":
                    state.to_dict(),
            }


        # =================================================
        # APPLY EXTRACTED INFORMATION
        # =================================================

        self._update_state(
            state,
            data,
        )

        proposed_route = (
            data.get("route")
            or "unknown"
        )

        route, reason = resolve_route(
            proposed_route,
            caller_text,
        )

        state.route = route
        state.route_reason = reason


        # =================================================
        # ROUTING
        # =================================================

        if route == "emergency":
            state.confirmed = False
            state.awaiting_confirmation = False

            reply = (
                self._emergency_reply()
            )

        elif route == "other":
            state.confirmed = False
            state.awaiting_confirmation = False

            reply = (
                data.get(
                    "spoken_reply"
                )
                or
                "This does not appear to be "
                "a municipal civic complaint."
            )

        elif route == "municipal":
            # Python decides the next question.
            reply = (
                self._municipal_next_reply(
                    state
                )
            )

        else:
            reply = (
                data.get(
                    "spoken_reply"
                )
                or
                "Please briefly describe the "
                "problem you are calling about."
            )


        # =================================================
        # HISTORY
        # =================================================

        reply = str(
            reply
        ).strip()

        state.last_bot_text = reply

        state.add_history(
            "user",
            caller_text,
        )

        state.add_history(
            "assistant",
            reply,
        )

        return {
            "spoken_reply":
                reply,
            "route":
                state.route,
            "ready_to_submit":
                state.ready_to_submit(),
            "state":
                state.to_dict(),
        }
