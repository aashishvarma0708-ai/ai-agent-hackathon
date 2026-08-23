import re


VALID_ROUTES = {
    "municipal",
    "emergency",
    "other",
    "unknown",
}


EMERGENCY_PATTERNS = [
    r"\bheart attack\b",
    r"\bnot breathing\b",
    r"\bunconscious\b",
    r"\bsevere bleeding\b",
    r"\bmedical emergency\b",

    r"\bhouse on fire\b",
    r"\bbuilding on fire\b",
    r"\bfire spreading\b",

    r"\bperson trapped\b",
    r"\bsomeone trapped\b",
    r"\bpeople trapped\b",

    r"\bbuilding collapse\b",
    r"\bcollapsed building\b",

    r"\bgas leak\b",
    r"\belectrocuted\b",
    r"\belectric shock\b",

    r"\bassault happening\b",
    r"\brobbery in progress\b",
    r"\bweapon\b",
    r"\bgun\b",

    # Hindi safety signals
    r"आग लगी",
    r"बेहोश",
    r"खून बह",
    r"फंस",
    r"हथियार",
]


MUNICIPAL_PATTERNS = [
    r"\bpothole\b",
    r"\broad damage\b",
    r"\bbroken road\b",

    r"\bgarbage\b",
    r"\bwaste\b",
    r"\btrash\b",

    r"\bstreetlight\b",
    r"\bstreet light\b",

    r"\bdrainage\b",
    r"\bdrain blocked\b",
    r"\bblocked drain\b",

    r"\bsewage\b",
    r"\bsewer\b",

    r"\bwater leak\b",
    r"\bwaterlogging\b",

    r"\bmanhole\b",

    r"\bflooded road\b",
    r"\broad flooding\b",

    r"\bdamaged infrastructure\b",

    # Common Hindi civic words
    r"गड्ढा",
    r"कचरा",
    r"नाली",
    r"सड़क",
]


def _matches(
    patterns: list[str],
    text: str,
) -> bool:

    normalized = (
        text
        .lower()
        .strip()
    )

    return any(
        re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def resolve_route(
    llm_route: str,
    caller_text: str,
):
    """
    AI interprets.
    Python enforces.

    Clear emergency language overrides the LLM.
    Clear municipal language can also recover a bad
    model route.
    """

    proposed = (
        llm_route
        or "unknown"
    ).strip().lower()

    if proposed not in VALID_ROUTES:
        proposed = "unknown"

    if _matches(
        EMERGENCY_PATTERNS,
        caller_text,
    ):
        return (
            "emergency",
            "deterministic emergency safety rule",
        )

    if _matches(
        MUNICIPAL_PATTERNS,
        caller_text,
    ):
        if proposed != "emergency":
            return (
                "municipal",
                "deterministic civic issue signal",
            )

    return (
        proposed,
        "Groq public-service classification",
    )

