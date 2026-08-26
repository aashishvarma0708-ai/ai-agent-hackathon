import base64
import json
import re
from groq import Groq

from .config import GROQ_API_KEY, TEXT_MODEL, VISION_MODEL
from .routing import is_explicit_emergency, detect_municipal_category, detect_external_service


SYSTEM_PROMPT = """
You are CivicResolve's complaint understanding and public-service triage model.

Your ONLY job is to interpret the citizen's supplied text and visual evidence
into structured public-service facts.

CRITICAL ARCHITECTURAL RULE:
Domain classification and safety-risk classification are INDEPENDENT.
1. The type of physical/civic issue determines the domain:
   - Streetlights, public lights, roads, potholes, garbage, drainage, manholes,
     water pipes, public infrastructure are ALL domain="municipal".
2. Safety concerns, danger, or hazards (e.g., "immediate safety risk",
   "dangerous", "people may get hurt", "cars are swerving", "someone may fall"):
   - Must be listed in "severity_indicators".
   - MUST NOT convert a municipal complaint into domain="emergency".
   - Safety risk is handled independently by the deterministic risk engine.
3. Domain="emergency" is reserved ONLY for explicit life-threatening non-maintenance
   crises: active fires, heart attacks/unconscious medical crises, violent crime in progress.

IMPORTANT VISUAL RULES:

- When an image is supplied, inspect the IMAGE CONTENT carefully.
- If the citizen text is generic, such as "analyze this image", the IMAGE is
  the primary evidence.
- Identify the main PHYSICAL civic problem visible in the image before
  selecting a category.
- If the image is a screenshot or contains browser/phone/computer interface
  elements, ignore the interface and analyze the physical scene shown inside it.
- Do NOT classify an image as software, deployment, programming, computer,
  configuration, website, application, or technology merely because it is
  displayed as a screenshot or uploaded from a computer.
- Do NOT infer categories from filenames, image metadata, EXIF data,
  upload instructions, or surrounding UI.
- If no recognizable civic/public-service issue is visible, use domain
  "unknown" rather than inventing a category.

Do NOT invent phone numbers, URLs, departments, laws, authorities,
government actions, or emergency instructions.

Do NOT decide the final municipal risk score.

Return ONLY one valid JSON object with exactly these keys:

{
  "domain": "municipal|emergency|other_public_service|unknown",
  "service_type": "municipal|police|fire|medical|legal|consumer|other",
  "category": "roads|garbage|drainage|water|streetlights|public_infrastructure|unknown",
  "subcategory": "allowed label described below",
  "summary": "one-sentence factual description of the evidence",
  "location_text": "location extracted from complaint text, empty if absent",
  "language": "language name if identifiable",
  "confidence": 0.0,
  "severity_indicators": ["short factual signals"],
  "needs_clarification": false,
  "clarification_question": ""
}

DOMAIN RULES:

1. municipal:
   Roads, potholes, damaged streets, garbage, waste, drainage, sewage,
   manholes, waterlogging, water supply, leaking pipes, streetlights,
   broken public lights, and damaged public infrastructure.

2. emergency:
   Immediate danger requiring police, fire or medical emergency response
   (e.g., active house fire, cardiac arrest, armed robbery).

3. other_public_service:
   Police/crime (theft, disputes), legal aid, consumer grievances, or non-emergency
   medical-service matters that are not municipal infrastructure complaints.

4. unknown:
   Evidence does not clearly identify a supported public-service issue.

CATEGORY RULES:

- pothole, broken road, road crack, damaged road, damaged footpath, crater
  -> category="roads"

- garbage pile, overflowing bin, dumped waste, rubbish, litter
  -> category="garbage"

- blocked drain, sewage overflow, open drain, manhole, open manhole, waterlogging
  -> category="drainage"

- leaking water pipe, burst pipe, water supply problem, pipeline leak
  -> category="water"

- broken streetlight, damaged lamp post, non-working street lamp, broken light, dark street
  -> category="streetlights"

- damaged bridge, railing, bus stop, park asset, public structure, fallen tree
  -> category="public_infrastructure"

SUBCATEGORY RULES:

For municipal complaints, subcategory MUST be one of:

pothole
road_crack
damaged_road
footpath_damage
road_obstruction
garbage_accumulation
overflowing_bin
illegal_dumping
blocked_drain
open_drain
sewage_overflow
waterlogging
water_leak
pipe_burst
no_water_supply
broken_streetlight
damaged_light_pole
damaged_public_infrastructure
structural_damage
unknown

For emergency or other-public-service complaints use only:

fire
accident
immediate_danger
police_or_crime
legal_help
consumer_grievance
health_service
unknown

Never invent a different subcategory.

CONSISTENCY RULES:

- If domain="municipal":
    service_type MUST be "municipal".
    category MUST NOT be "unknown" when a supported municipal defect
    is clearly visible.

- If domain is not "municipal":
    category MUST be "unknown".

- A clearly visible broken light/streetlight MUST be classified:
    domain="municipal"
    service_type="municipal"
    category="streetlights"

- A clearly visible pothole MUST be classified:
    domain="municipal"
    service_type="municipal"
    category="roads"
    subcategory="pothole"

- Base every decision only on supplied complaint evidence.

- If evidence is genuinely unclear:
    lower confidence,
    set needs_clarification=true,
    and use unknown rather than hallucinating another domain.

Do not output reasoning, markdown, code fences or explanatory text.
Return only the JSON object.
"""


def _fallback(text: str) -> dict:
    # 1. Check for explicit non-municipal life-threatening emergency
    emerg = is_explicit_emergency(text)
    if emerg:
        dom, service = emerg
        return {
            "domain": dom,
            "service_type": service,
            "category": "unknown",
            "subcategory": service if service in ["fire"] else "immediate_danger",
            "summary": text[:180],
            "location_text": "",
            "language": "unknown",
            "confidence": 0.90,
            "severity_indicators": ["possible immediate danger"],
            "needs_clarification": False,
            "clarification_question": "",
        }

    # 2. Check for municipal issues using deterministic taxonomy
    muni = detect_municipal_category(text)
    if muni:
        cat, subcat = muni
        sev = []
        t = (text or "").lower()
        if any(w in t for w in ["safety risk", "dangerous", "danger", "hazard", "fall", "injury", "accident", "swerve", "swerving", "hurt", "open manhole"]):
            sev.append("immediate safety hazard reported")
        return {
            "domain": "municipal",
            "service_type": "municipal",
            "category": cat,
            "subcategory": subcat,
            "summary": text[:180],
            "location_text": "",
            "language": "unknown",
            "confidence": 0.85,
            "severity_indicators": sev,
            "needs_clarification": False,
            "clarification_question": "",
        }

    # 3. Check for external non-emergency public service
    ext = detect_external_service(text)
    if ext:
        dom, service, subcat = ext
        return _external(text, service, subcat)

    # 4. Unknown / requires clarification
    return {
        "domain": "unknown",
        "service_type": "other",
        "category": "unknown",
        "subcategory": "unknown",
        "summary": text[:180],
        "location_text": "",
        "language": "unknown",
        "confidence": 0.35,
        "severity_indicators": [],
        "needs_clarification": True,
        "clarification_question": "Please describe what happened and where it happened.",
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
        "confidence": 0.75,
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

