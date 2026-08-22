import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class CallState:
    # Twilio identifiers
    call_sid: Optional[str] = None
    stream_sid: Optional[str] = None

    # Public-service routing
    route: str = "unknown"
    route_reason: Optional[str] = None

    # Municipal complaint information
    issue: Optional[str] = None
    location: Optional[str] = None
    severity: Optional[str] = None
    safety_risk: Optional[bool] = None

    # Confirmation protection
    awaiting_confirmation: bool = False
    confirmed: bool = False

    # Submission
    submitted: bool = False
    complaint_id: Optional[str] = None

    # Optional evidence flow
    evidence_opt_in: Optional[bool] = None
    evidence_link_sent: bool = False

    # Conversation metadata
    language: str = "en"
    turn_count: int = 0

    last_user_text: str = ""
    last_bot_text: str = ""

    history: list = field(
        default_factory=list
    )

    def add_history(
        self,
        role: str,
        text: str,
    ):
        if not text:
            return

        self.history.append(
            {
                "role": role,
                "content": text,
            }
        )

        # Keep phone-call context small and fast.
        self.history = self.history[-12:]

    def ready_for_confirmation(self) -> bool:
        """
        The bot may ask for submission confirmation only
        when enough civic complaint information exists.
        """

        return bool(
            self.route == "municipal"
            and self.issue
            and self.location
            and self.safety_risk is not None
        )

    def ready_to_submit(self) -> bool:
        """
        Python enforcement gate.

        Groq can NEVER bypass this.
        """

        return bool(
            self.ready_for_confirmation()
            and self.confirmed
            and not self.submitted
        )

    def complaint_summary(self) -> str:
        parts = []

        if self.issue:
            parts.append(
                f"issue: {self.issue}"
            )

        if self.location:
            parts.append(
                f"location: {self.location}"
            )

        if self.severity:
            parts.append(
                f"severity: {self.severity}"
            )

        if self.safety_risk is True:
            parts.append(
                "there is a safety risk"
            )

        elif self.safety_risk is False:
            parts.append(
                "no immediate safety risk was reported"
            )

        return ", ".join(parts)

    def prompt_context(self) -> str:
        """
        Safe compact state representation for the LLM.
        """

        data = {
            "route": self.route,
            "issue": self.issue,
            "location": self.location,
            "severity": self.severity,
            "safety_risk": self.safety_risk,
            "awaiting_confirmation":
                self.awaiting_confirmation,
            "confirmed": self.confirmed,
            "submitted": self.submitted,
            "evidence_opt_in":
                self.evidence_opt_in,
            "language": self.language,
        }

        return json.dumps(
            data,
            ensure_ascii=False,
        )

    def to_dict(self):
        return asdict(self)
