import html
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


def page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)} · CivicResolve</title>

<style>
/* CSS Reset & Tokens */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

:root {{
    --bg-page: #FAF8F5;
    --surface-card: #FFFFFF;
    --surface-subtle: #FBF9F7;
    --surface-tint: #F7EFEF;
    --surface-success: #F2F8F4;
    
    --text-primary: #212529;
    --text-secondary: #57524E;
    --text-muted: #79716B;
    --text-tertiary: #A8A29E;
    
    --accent: #722F37;
    --accent-hover: #57232A;
    --accent-light: #F9F0F2;
    --accent-border: rgba(114, 47, 55, 0.16);
    
    --border-subtle: #EBE4DF;
    --border-strong: #D6CBC4;
    
    --success-accent: #1E6B47;
    --success-border: #C6E4D4;
    --success-bg: #F2F8F4;
    
    --warning-accent: #9A3412;
    --warning-bg: #FFF7ED;
    --warning-border: #FED7AA;
    
    --error-accent: #B91C1C;
    --error-bg: #FEF2F2;
    --error-border: #FECACA;

    --blue-accent: #1E40AF;
    --blue-bg: #EFF6FF;
    --blue-border: #BFDBFE;
    
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 22px;
    --radius-full: 9999px;
    
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.02), 0 16px 36px -4px rgba(114, 47, 55, 0.07);
    --shadow-btn: 0 4px 14px rgba(114, 47, 55, 0.22);
}}

html {{
    -webkit-text-size-adjust: 100%;
    font-size: 16px;
    background-color: var(--bg-page);
}}

body {{
    min-height: 100vh;
    padding: 32px 16px 48px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-page);
    background-image: 
        radial-gradient(ellipse at 85% 0%, rgba(114, 47, 55, 0.06) 0%, transparent 45%),
        radial-gradient(ellipse at 15% 100%, rgba(114, 47, 55, 0.03) 0%, transparent 40%);
    background-repeat: no-repeat;
    background-attachment: fixed;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
}}

/* Brand Header */
.brand-shell {{
    width: 100%;
    max-width: 540px;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 4px;
}}

.brand-left {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.brand-mark {{
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    background: linear-gradient(135deg, #7A333B 0%, #63262E 100%);
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 800;
    box-shadow: 0 3px 10px rgba(114, 47, 55, 0.22);
}}

.brand-text {{
    display: flex;
    flex-direction: column;
}}

.brand-name {{
    font-size: 15px;
    line-height: 1.25;
    font-weight: 750;
    color: var(--text-primary);
}}

.brand-sub {{
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 450;
    line-height: 1.2;
    margin-top: 2px;
}}

.secure-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 9px;
    border-radius: var(--radius-full);
    background: rgba(114, 47, 55, 0.05);
    border: 1px solid rgba(114, 47, 55, 0.12);
    color: var(--accent);
    font-size: 11px;
    font-weight: 600;
}}

/* Main Card */
.card {{
    width: 100%;
    max-width: 540px;
    margin: 0 auto;
    background: var(--surface-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 28px 24px;
    box-shadow: var(--shadow-card);
}}

.eyebrow {{
    display: inline-block;
    color: var(--accent);
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

h1 {{
    margin: 0 0 8px;
    color: #1A1718;
    font-size: 22px;
    line-height: 1.25;
    font-weight: 750;
    letter-spacing: -0.4px;
}}

.intro-desc {{
    color: var(--text-secondary);
    font-size: 13.5px;
    line-height: 1.5;
    margin-bottom: 20px;
}}

/* Ticket Header Box */
.ticket-box {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    background: var(--surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    margin-bottom: 20px;
}}

.ticket-id-label {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-muted);
}}

.ticket-id-val {{
    font-size: 15px;
    font-weight: 750;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: var(--text-primary);
    margin-top: 1px;
}}

.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: var(--radius-full);
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}

.status-pill.new {{
    background: var(--blue-bg);
    color: var(--blue-accent);
    border: 1px solid var(--blue-border);
}}

.status-pill.progress {{
    background: var(--warning-bg);
    color: var(--warning-accent);
    border: 1px solid var(--warning-border);
}}

.status-pill.resolved {{
    background: var(--success-bg);
    color: var(--success-accent);
    border: 1px solid var(--success-border);
}}

.status-pill.reopened {{
    background: var(--error-bg);
    color: var(--error-accent);
    border: 1px solid var(--error-border);
}}

/* Lifecycle Timeline */
.timeline-section {{
    margin: 24px 0;
    padding: 18px 16px;
    background: #FFFFFF;
    border: 1.5px solid var(--border-subtle);
    border-radius: var(--radius-lg);
}}

.timeline-title {{
    font-size: 12px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-muted);
    margin-bottom: 16px;
}}

.timeline-track {{
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
    padding-left: 28px;
}}

.timeline-track::before {{
    content: '';
    position: absolute;
    left: 9px;
    top: 12px;
    bottom: 12px;
    width: 2px;
    background: var(--border-subtle);
}}

.timeline-step {{
    position: relative;
    padding-bottom: 20px;
}}

.timeline-step:last-child {{
    padding-bottom: 0;
}}

.step-node {{
    position: absolute;
    left: -28px;
    top: 2px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #FFFFFF;
    border: 2px solid var(--border-strong);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: var(--text-muted);
    z-index: 2;
}}

.timeline-step.completed .step-node {{
    background: var(--accent);
    border-color: var(--accent);
    color: #FFFFFF;
}}

.timeline-step.current .step-node {{
    background: #FFFFFF;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(114, 47, 55, 0.18);
}}

.timeline-step.reopened .step-node {{
    background: var(--error-accent);
    border-color: var(--error-accent);
    color: #FFFFFF;
}}

.step-label {{
    font-size: 13.5px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.3;
}}

.timeline-step.pending .step-label {{
    color: var(--text-tertiary);
    font-weight: 500;
}}

.step-desc {{
    font-size: 11.5px;
    color: var(--text-secondary);
    margin-top: 2px;
}}

/* Details Grid */
.details-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 20px;
}}

.detail-item {{
    padding: 10px 12px;
    background: var(--surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
}}

.detail-label {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--text-muted);
    margin-bottom: 2px;
}}

.detail-val {{
    font-size: 12.5px;
    font-weight: 650;
    color: var(--text-primary);
}}

/* Resolution Note Box */
.resolution-box {{
    padding: 14px 16px;
    border-radius: var(--radius-lg);
    background: var(--surface-success);
    border: 1.5px solid var(--success-border);
    margin-top: 16px;
}}

.resolution-box.reopened-box {{
    background: var(--error-bg);
    border-color: var(--error-border);
}}

.resolution-box-title {{
    font-size: 12px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: var(--success-accent);
    margin-bottom: 4px;
}}

.resolution-box.reopened-box .resolution-box-title {{
    color: var(--error-accent);
}}

.resolution-box-desc {{
    font-size: 13px;
    color: var(--text-primary);
    line-height: 1.45;
}}

/* Error / Empty States */
.state-center {{
    text-align: center;
    padding: 24px 8px;
}}

.state-icon {{
    width: 52px;
    height: 52px;
    border-radius: 16px;
    margin: 0 auto 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.state-icon.error {{
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    color: var(--error-accent);
}}

.state-icon svg {{
    width: 26px;
    height: 26px;
}}

.footer-notice {{
    margin-top: 24px;
    text-align: center;
    font-size: 11.5px;
    color: var(--text-muted);
}}
</style>
</head>
<body>

<div class="brand-shell">
    <div class="brand-left">
        <div class="brand-mark">CR</div>
        <div class="brand-text">
            <span class="brand-name">CivicResolve AI</span>
            <span class="brand-sub">Citizen Complaint Portal</span>
        </div>
    </div>
    <div class="secure-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
        <span>Secure Tracking</span>
    </div>
</div>

<main class="card">
{body}
</main>

<div class="footer-notice">
    CivicResolve AI · Powered by Municipal Autonomous Triage
</div>

</body>
</html>
"""


def _compute_timeline_steps(status: str) -> list:
    status_upper = (status or "NEW").upper()

    # Base steps
    steps = [
        {"key": "NEW", "label": "Complaint Registered", "desc": "Logged and AI prioritized"},
        {"key": "ACKNOWLEDGED", "label": "Acknowledged", "desc": "Validated by Municipal AI"},
        {"key": "ASSIGNED", "label": "Department Assigned", "desc": "Dispatched to field authority"},
        {"key": "WORK_STARTED", "label": "Work Started", "desc": "Field crew active on site"},
        {"key": "COMPLETED", "label": "Resolution & Verification", "desc": "Repairs verified & closed"},
    ]

    status_ranks = {
        "NEW": 1,
        "ACKNOWLEDGED": 2,
        "ASSIGNED": 3,
        "WORK_STARTED": 4,
        "RESOLUTION_SUBMITTED": 4,
        "AI_VERIFICATION_PENDING": 4,
        "RESOLVED_PENDING_CITIZEN": 5,
        "CLOSED": 5,
        "COMPLETED": 5,
        "EMERGENCY_DISPATCHED": 5,
        "EXTERNALLY_ROUTED": 5,
        "REOPENED": 3,  # Sent back for reassignment/work
    }

    current_rank = status_ranks.get(status_upper, 1)

    timeline_items = []
    for idx, s in enumerate(steps, 1):
        if status_upper == "REOPENED":
            if idx <= 2:
                state_class = "completed"
            elif idx == 3:
                state_class = "reopened"
            else:
                state_class = "pending"
        elif idx < current_rank:
            state_class = "completed"
        elif idx == current_rank:
            state_class = "current completed" if (current_rank == 5) else "current"
        else:
            state_class = "pending"

        timeline_items.append({
            "idx": idx,
            "label": s["label"],
            "desc": s["desc"],
            "state_class": state_class,
        })

    return timeline_items


@router.get("/track/{tracking_token}", response_class=HTMLResponse)
async def view_public_tracking_page(tracking_token: str):
    """
    Publicly accessible, unguessable token-based complaint tracking page.
    """
    token_clean = (tracking_token or "").strip()

    base_url = (
        os.getenv("CIVICRESOLVE_API_BASE_URL", "")
        or os.getenv("CIVICRESOLVE_API_URL", "http://127.0.0.1:8000")
    ).rstrip("/")

    endpoint = f"{base_url}/api/public/track/{token_clean}"

    data = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(endpoint)
            if res.status_code == 200:
                data = res.json()
    except Exception as exc:
        print(f"⚠️ Tracking backend request failed: {exc}", flush=True)

    if not data:
        error_html = """
<div class="state-center">
    <div class="state-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    <div class="eyebrow">Tracking Notice</div>
    <h1>Complaint Not Found</h1>
    <p class="intro-desc">This tracking link is invalid or has expired. Please verify your reference link or contact municipal helpline.</p>
</div>
"""
        return HTMLResponse(
            content=page_shell("Tracking Not Found", error_html),
            status_code=404,
        )

    cid = html.escape(str(data.get("complaint_id", "")))
    status = str(data.get("status", "NEW")).upper()
    summary = html.escape(str(data.get("summary", "Civic grievance registered.")))
    category = html.escape(str(data.get("category", "General")).upper())
    dept = html.escape(str(data.get("department", "Municipal Works")))
    loc = html.escape(str(data.get("location_text", "Ward Jurisdiction")))
    priority = html.escape(str(data.get("priority", "LOW")).upper())
    res_summary = data.get("resolution_summary")
    created_at = html.escape(str(data.get("created_at", ""))[:16].replace("T", " "))
    updated_at = html.escape(str(data.get("updated_at", ""))[:16].replace("T", " "))

    # Status badge styling
    if status in {"CLOSED", "RESOLVED_PENDING_CITIZEN", "COMPLETED"}:
        pill_class = "resolved"
        pill_label = "Resolved ✓"
    elif status == "REOPENED":
        pill_class = "reopened"
        pill_label = "Reopened ⚠️"
    elif status in {"ASSIGNED", "WORK_STARTED", "RESOLUTION_SUBMITTED", "AI_VERIFICATION_PENDING"}:
        pill_class = "progress"
        pill_label = status.replace("_", " ").title()
    else:
        pill_class = "new"
        pill_label = "Registered"

    # Timeline steps
    steps = _compute_timeline_steps(status)
    steps_html = []
    for s in steps:
        check_icon = "✓" if "completed" in s["state_class"] else str(s["idx"])
        if "reopened" in s["state_class"]:
            check_icon = "!"

        steps_html.append(f"""
        <div class="timeline-step {s['state_class']}">
            <div class="step-node">{check_icon}</div>
            <div class="step-label">{html.escape(s['label'])}</div>
            <div class="step-desc">{html.escape(s['desc'])}</div>
        </div>
        """)

    timeline_rendered = "".join(steps_html)

    # Resolution box if present
    resolution_html = ""
    if status == "REOPENED":
        resolution_html = """
        <div class="resolution-box reopened-box">
            <div class="resolution-box-title">Reopened for Field Action</div>
            <div class="resolution-box-desc">This issue was marked as still persisting on site and has been re-escalated to the supervisor.</div>
        </div>
        """
    elif res_summary:
        resolution_html = f"""
        <div class="resolution-box">
            <div class="resolution-box-title">Field Resolution Update</div>
            <div class="resolution-box-desc">{html.escape(str(res_summary))}</div>
        </div>
        """

    content_html = f"""
<div class="eyebrow">Public Grievance Status</div>
<h1>Live Ticket Tracking</h1>
<p class="intro-desc">Real-time status updates and department accountability timeline.</p>

<div class="ticket-box">
    <div>
        <div class="ticket-id-label">Complaint Reference</div>
        <div class="ticket-id-val">{cid}</div>
    </div>
    <div class="status-pill {pill_class}">{pill_label}</div>
</div>

<div class="details-grid">
    <div class="detail-item">
        <div class="detail-label">Category</div>
        <div class="detail-val">{category}</div>
    </div>
    <div class="detail-item">
        <div class="detail-label">Priority</div>
        <div class="detail-val">{priority}</div>
    </div>
    <div class="detail-item">
        <div class="detail-label">Department</div>
        <div class="detail-val">{dept}</div>
    </div>
    <div class="detail-item">
        <div class="detail-label">Location</div>
        <div class="detail-val">{loc}</div>
    </div>
</div>

<div class="timeline-section">
    <div class="timeline-title">Lifecycle Progress</div>
    <div class="timeline-track">
        {timeline_rendered}
    </div>
</div>

{resolution_html}

<div class="details-grid" style="margin-top: 16px;">
    <div class="detail-item">
        <div class="detail-label">Submitted</div>
        <div class="detail-val">{created_at} UTC</div>
    </div>
    <div class="detail-item">
        <div class="detail-label">Last Updated</div>
        <div class="detail-val">{updated_at} UTC</div>
    </div>
</div>
"""

    return HTMLResponse(
        content=page_shell(f"Tracking {cid}", content_html),
        status_code=200,
    )
