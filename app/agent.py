import os
from groq import Groq
from dotenv import load_dotenv


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# You can override this inside .env later.
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.6-27b"
)


SYSTEM_PROMPT = """
You are the voice intake assistant for CivicResolve.

Your job is to help a citizen report a civic/public infrastructure issue
through a short natural phone conversation.

Examples include:
- potholes
- damaged roads
- garbage accumulation
- drainage problems
- water leakage
- streetlight failures
- flooding
- damaged public infrastructure

CONVERSATION RULES:

1. Speak naturally like a helpful phone assistant.
2. Keep every response short.
3. Ask only ONE question at a time.
4. Do not give long explanations.
5. Never invent information.
6. Never assume a location.
7. Never claim a complaint was submitted unless the system confirms it.
8. Collect the following information:
   - what happened / issue
   - location
   - severity or immediate safety concern
9. Once enough information is collected, summarize it briefly.
10. Ask the caller to confirm before submission.
11. If the caller corrects something, update the information.
12. Do not repeatedly ask for information already provided.
13. The caller may speak English or Hindi.
14. If the caller speaks Hindi, you may answer naturally in Hindi.
15. Do not use markdown, bullet points, symbols or formatting because
    your response will eventually be spoken aloud.
16.For phone calls, speed is critical.Keep normal responses under 12 words whenever possible.Ask exactly one short question at a time.
Examples:
"Where is the pothole located?"
"Is anyone in immediate danger?"
"Is that correct?"

Never add filler such as:
"Sure, I can help."
"I understand."
"Thank you for providing that information."
Keep responses preferably under 30 words.
"""


class CallAgent:

    def __init__(self):
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing from .env"
            )

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

        self.history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    def reset(self):
        self.history = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    def respond(self, user_text: str) -> str:

        user_text = user_text.strip()

        if not user_text:
            return (
                "I didn't catch that. "
                "Could you please say that again?"
            )

        self.history.append(
            {
                "role": "user",
                "content": user_text
            }
        )

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=self.history,
            temperature=0.6,
            max_tokens=50,
            reasoning_effort="none",
            tool_choice="none",
        )

        assistant_text = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        self.history.append(
            {
                "role": "assistant",
                "content": assistant_text
            }
        )

        return assistant_text
