SERVICE_DIRECTORY = {
    "emergency": {
        "name": "Emergency Response Support System (ERSS 112)",
        "url": "https://112.gov.in/",
        "instruction": "For immediate police, fire, rescue, or medical emergencies in India, use the official ERSS 112 service.",
        "verified_scope": "National emergency fallback",
    },
    "police": {
        "name": "Emergency Response Support System (ERSS 112)",
        "url": "https://112.gov.in/",
        "instruction": "If there is immediate danger or urgent police assistance is required, use ERSS 112. Non-emergency police complaints should be directed to the verified State/UT police portal or nearest police station.",
        "verified_scope": "National emergency fallback",
    },
    "fire": {
        "name": "Emergency Response Support System (ERSS 112)",
        "url": "https://112.gov.in/",
        "instruction": "For a fire or immediate rescue emergency, use the official ERSS 112 service.",
        "verified_scope": "National emergency fallback",
    },
    "medical": {
        "name": "Emergency Response Support System (ERSS 112)",
        "url": "https://112.gov.in/",
        "instruction": "For an immediate medical emergency, use the official ERSS 112 service. Non-emergency health grievances should be routed to a verified local health authority.",
        "verified_scope": "National emergency fallback",
    },
    "legal": {
        "name": "National Legal Services Authority (NALSA)",
        "url": "https://nalsa.gov.in/",
        "instruction": "For legal-aid information, use the official NALSA portal or the appropriate State Legal Services Authority.",
        "verified_scope": "National legal-aid service",
    },
    "consumer": {
        "name": "National Consumer Helpline",
        "url": "https://consumerhelpline.gov.in/",
        "instruction": "For consumer grievances, use the official National Consumer Helpline portal.",
        "verified_scope": "National consumer grievance service",
    },
    "other": {
        "name": "Public Service Helpdesk — Human Verification",
        "url": "",
        "instruction": "The issue does not match a configured verified service. Ask for clarification or route to a human operator rather than inventing an authority.",
        "verified_scope": "Human review",
    },
}


def get_external_service(service_type: str) -> dict:
    key = (service_type or "other").lower()
    return SERVICE_DIRECTORY.get(key, SERVICE_DIRECTORY["other"])
