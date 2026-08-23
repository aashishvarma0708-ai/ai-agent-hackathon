export const SERVICE_DIRECTORY = {
  emergency: {
    name: "Emergency Response Support System (ERSS 112)",
    url: "https://112.gov.in/",
    badge: "112 Emergency Dispatch",
    instruction: "For immediate police, fire, rescue, or medical emergencies in India, use the official ERSS 112 service.",
    verified_scope: "National emergency fallback",
  },
  police: {
    name: "Emergency Response Support System (ERSS 112)",
    url: "https://112.gov.in/",
    badge: "Police / Crime Reporting",
    instruction: "If there is immediate danger or urgent police assistance is required, use ERSS 112. Non-emergency police complaints should be directed to the verified State/UT police portal or nearest police station.",
    verified_scope: "National emergency fallback",
  },
  fire: {
    name: "Emergency Response Support System (ERSS 112)",
    url: "https://112.gov.in/",
    badge: "Fire & Rescue Service",
    instruction: "For a fire or immediate rescue emergency, use the official ERSS 112 service.",
    verified_scope: "National emergency fallback",
  },
  medical: {
    name: "Emergency Response Support System (ERSS 112)",
    url: "https://112.gov.in/",
    badge: "Ambulance / Medical Emergency",
    instruction: "For an immediate medical emergency, use the official ERSS 112 service. Non-emergency health grievances should be routed to a verified local health authority.",
    verified_scope: "National emergency fallback",
  },
  legal: {
    name: "National Legal Services Authority (NALSA)",
    url: "https://nalsa.gov.in/",
    badge: "Free Legal Aid & Redressal",
    instruction: "For legal-aid information, use the official NALSA portal or the appropriate State Legal Services Authority.",
    verified_scope: "National legal-aid service",
  },
  consumer: {
    name: "National Consumer Helpline",
    url: "https://consumerhelpline.gov.in/",
    badge: "Consumer Rights & Grievance",
    instruction: "For consumer grievances against sellers, e-commerce, or service providers, use the official National Consumer Helpline portal.",
    verified_scope: "National consumer grievance service",
  },
  other: {
    name: "Public Service Helpdesk — Human Verification",
    url: "",
    badge: "Human Review",
    instruction: "The issue does not match a configured verified service. Assigned to municipal citizen desk for manual dispatch.",
    verified_scope: "Human review",
  },
};

export const ROUTING_RULES = {
  roads: {
    department: "Roads & Infrastructure Department",
    sla_hours: 24,
    icon: "Truck",
  },
  garbage: {
    department: "Sanitation & Solid Waste Management",
    sla_hours: 12,
    icon: "Trash2",
  },
  drainage: {
    department: "Drainage & Sewerage Department",
    sla_hours: 12,
    icon: "Waves",
  },
  water: {
    department: "Water Supply & Distribution Board",
    sla_hours: 8,
    icon: "Droplets",
  },
  streetlights: {
    department: "Electrical / Streetlight Maintenance",
    sla_hours: 24,
    icon: "Lightbulb",
  },
  public_infrastructure: {
    department: "Public Works & Infrastructure Department",
    sla_hours: 48,
    icon: "Building2",
  },
  unknown: {
    department: "Civic Helpdesk — Human Review",
    sla_hours: 24,
    icon: "HelpCircle",
  },
};
