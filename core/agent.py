import base64
import json
import re
from groq import Groq

from .config import GROQ_API_KEY, TEXT_MODEL, VISION_MODEL


SYSTEM_PROMPT = """
You are CivicResolve's complaint understanding and public-service triage model.

Your job is ONLY to interpret the citizen's evidence into structured facts.
Do NOT invent phone numbers, URLs, departments, laws, or emergency instructions.
Do NOT decide the final municipal risk score.
Do NOT claim that a government authority has received a complaint.

Return one JSON object with exactly these keys:
{
  "domain": "municipal|emergency|other_public_service|unknown",
  "service_type": "municipal|police|fire|medical|legal|consumer|other",
  "category": "roads|garbage|drainage|water|streetlights|public_infrastructure|unknown",
  "subcategory": "short snake_case label",
  "summary": "one-sentence factual summary",
  "location_text": "location extracted from complaint, empty if absent",
  "language": "language name if identifiable",
  "confidence": 0.0,
  "severity_indicators": ["short factual signals"],
  "needs_clarification": false,
  "clarification_question": ""
}

Rules:
1. Municipal domain is for roads, garbage, drainage, water supply, streetlights,
   and public infrastructure.
2. Emergency domain is for immediate danger requiring police/fire/medical emergency response.
3. Police, legal, consumer, or medical issues that are not municipal should not be forced
   into municipal categories.
4. If evidence is unclear, lower confidence and set needs_clarification=true.
5. category must be "unknown" for non-municipal issues.
6. Base decisions only on the supplied complaint and image.
"""


def _fallback(text: str) -> dict:
    t = (text or "").lower()

    emergency_terms = [
        "fire", "burning", "someone is attacking", "threatening me",
        "life danger", "unconscious", "severe bleeding", "accident now",
    ]
    police_terms = ["stolen", "theft", "robbery", "assault", "harassment", "crime", "threat"]
    legal_terms = ["legal aid", "lawyer", "court", "legal case", "property dispute"]
    consumer_terms = ["seller", "refund", "online order", "consumer", "defective product", "company complaint"]
    medical_terms = ["doctor", "hospital complaint", "medical complaint", "health complaint"]

    if any(x in t for x in emergency_terms):
        service = "fire" if "fire" in t or "burning" in t else "police"
        if any(x in t for x in ["unconscious", "bleeding", "medical"]):
            service = "medical"
        return {
            "domain": "emergency", "service_type": service, "category": "unknown",
            "subcategory": "urgent_public_safety", "summary": text[:180],
            "location_text": "", "language": "unknown", "confidence": 0.68,
            "severity_indicators": ["possible immediate danger"],
            "needs_clarification": False, "clarification_question": ""
        }

    if any(x in t for x in police_terms):
        return _external(text, "police", "police_or_crime")
    if any(x in t for x in legal_terms):
        return _external(text, "legal", "legal_help")
    if any(x in t for x in consumer_terms):
        return _external(text, "consumer", "consumer_grievance")
    if any(x in t for x in medical_terms):
        return _external(text, "medical", "health_service")

    category_map = [
        ("roads", ["pothole", "road", "footpath", "sidewalk", "street damaged"]),
        ("garbage", ["garbage", "trash", "waste", "rubbish", "dustbin"]),
        ("drainage", ["drain", "drainage", "sewage", "sewer", "waterlogging"]),
        ("water", ["water leak", "no water", "water supply", "pipe burst", "pipeline"]),
        ("streetlights", ["streetlight", "street light", "lamp post", "light not working"]),
        ("public_infrastructure", ["public building", "bus stop", "park", "bridge", "railing"]),
    ]

    for cat, words in category_map:
        if any(w in t for w in words):
            return {
                "domain": "municipal", "service_type": "municipal", "category": cat,
                "subcategory": cat, "summary": text[:180],
                "location_text": "", "language": "unknown", "confidence": 0.62,
                "severity_indicators": [],
                "needs_clarification": False, "clarification_question": ""
            }

    return {
        "domain": "unknown", "service_type": "other", "category": "unknown",
        "subcategory": "unknown", "summary": text[:180],
        "location_text": "", "language": "unknown", "confidence": 0.35,
        "severity_indicators": [], "needs_clarification": True,
        "clarification_question": "Please describe what happened and where it happened."
    }


def _external(text, service, subcategory):
    return {
        "domain": "other_public_service",
        "service_type": service,
        "category": "unknown",
        "subcategory": subcategory,
        "summary": text[:180],
        "location_text": "",
        "language": "unknown",
        "confidence": 0.66,
        "severity_indicators": [],
        "needs_clarification": False,
        "clarification_question": "",
    }


def _normalize(data: dict) -> dict:
    valid_domains = {"municipal", "emergency", "other_public_service", "unknown"}
    valid_services = {"municipal", "police", "fire", "medical", "legal", "consumer", "other"}
    valid_categories = {
        "roads", "garbage", "drainage", "water", "streetlights",
        "public_infrastructure", "unknown"
    }

    data["domain"] = data.get("domain") if data.get("domain") in valid_domains else "unknown"
    data["service_type"] = data.get("service_type") if data.get("service_type") in valid_services else "other"
    data["category"] = data.get("category") if data.get("category") in valid_categories else "unknown"

    if data["domain"] != "municipal":
        data["category"] = "unknown"

    try:
        data["confidence"] = float(data.get("confidence", 0))
    except Exception:
        data["confidence"] = 0.0
    data["confidence"] = max(0.0, min(1.0, data["confidence"]))

    data["severity_indicators"] = list(data.get("severity_indicators") or [])
    data["needs_clarification"] = bool(data.get("needs_clarification", False))
    data["clarification_question"] = str(data.get("clarification_question") or "")
    data["subcategory"] = str(data.get("subcategory") or "unknown")
    data["summary"] = str(data.get("summary") or "")
    data["location_text"] = str(data.get("location_text") or "")
    data["language"] = str(data.get("language") or "unknown")
    return data


def analyze_complaint(text: str, image_bytes=None, image_mime="image/jpeg") -> tuple[dict, bool]:
    """
    Returns (structured_result, used_ai).

    Groq handles text and image understanding.
    Deterministic fallback is used only if the AI request fails.
    """
    if not GROQ_API_KEY:
        return _normalize(_fallback(text)), False

    client = Groq(api_key=GROQ_API_KEY)

    try:
        if image_bytes:
            b64 = base64.b64encode(image_bytes).decode("utf-8")

            content = [
                {
                    "type": "text",
                    "text": (
                        f"{SYSTEM_PROMPT}\\n\\n"
                        f"Citizen complaint:\\n{text or '[No text supplied]'}\\n\\n"
                        "IMPORTANT: Analyze the attached image as visual evidence. "
                        "Return ONLY one valid JSON object. "
                        "Do not use markdown or code fences. "
                        "Do not add explanations before or after the JSON."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime};base64,{b64}"
                    },
                },
            ]

            model = VISION_MODEL

        else:
            content = (
                f"{SYSTEM_PROMPT}\\n\\n"
                f"Citizen complaint:\\n{text}"
            )
            model = TEXT_MODEL

        print(
            f"AI DEBUG | model={model} | "
            f"image_present={bool(image_bytes)} | "
            f"mime={image_mime} | "
            f"bytes={len(image_bytes) if image_bytes else 0}",
            flush=True,
        )

        request_args = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_completion_tokens": 900,
        }

        # Text model can safely use Groq JSON Object Mode.
        # Vision avoids response_format because Qwen vision was returning
        # Groq json_validate_failed before the response reached our parser.
        if not image_bytes:
            request_args["response_format"] = {"type": "json_object"}
        else:
            # Qwen 3.6 defaults to reasoning mode. For civic image
            # classification we want the final structured answer directly.
            request_args["reasoning_effort"] = "none"

        completion = client.chat.completions.create(**request_args)

        raw = (completion.choices[0].message.content or "").strip()

        # Remove optional markdown fences.
        if raw.startswith("```"):
            lines = raw.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            raw = "\\n".join(lines).strip()

        # First try normal JSON parsing.
        try:
            data = json.loads(raw)

        except json.JSONDecodeError:
            # If the model added a small amount of surrounding text,
            # recover the JSON object itself.
            start = raw.find("{")
            end = raw.rfind("}")

            if start == -1 or end == -1 or end <= start:
                raise

            data = json.loads(raw[start:end + 1])

        print(
            f"AI SUCCESS | model={model} | "
            f"image_present={bool(image_bytes)} | "
            f"domain={data.get('domain')} | "
            f"category={data.get('category')} | "
            f"subcategory={data.get('subcategory')}",
            flush=True,
        )

        return _normalize(data), True

    except Exception as e:
        print(
            f"AI ERROR | model={locals().get('model', 'unknown')} | "
            f"image_present={bool(image_bytes)} | "
            f"error={repr(e)}",
            flush=True,
        )

        return _normalize(_fallback(text)), False

