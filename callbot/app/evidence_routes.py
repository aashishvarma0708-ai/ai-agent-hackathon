import html
import os

import httpx

from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
)

from fastapi.responses import (
    HTMLResponse,
)

from app.evidence_links import (
    EvidenceLinkError,
    EvidenceLinkStore,
)


router = APIRouter()


def page_shell(
    title: str,
    body: str,
) -> str:
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
    
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 22px;
    --radius-full: 9999px;
    
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
    --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.02), 0 16px 36px -4px rgba(114, 47, 55, 0.07);
    --shadow-btn: 0 4px 14px rgba(114, 47, 55, 0.22);
    --shadow-btn-hover: 0 6px 20px rgba(114, 47, 55, 0.30);
}}

html {{
    -webkit-text-size-adjust: 100%;
    font-size: 16px;
    background-color: var(--bg-page);
}}

body {{
    min-height: 100vh;
    padding: 32px 16px 44px;
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
    -moz-osx-font-smoothing: grayscale;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
}}

/* Brand Shell */
.brand-shell {{
    width: 100%;
    max-width: 520px;
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
    background: var(--accent);
    background: linear-gradient(135deg, #7A333B 0%, #63262E 100%);
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: -0.3px;
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
    letter-spacing: -0.2px;
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
    letter-spacing: 0.2px;
}}

.secure-badge svg {{
    width: 12px;
    height: 12px;
    flex-shrink: 0;
}}

/* Main Card */
.card {{
    width: 100%;
    max-width: 520px;
    margin: 0 auto;
    background: var(--surface-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 32px 28px;
    box-shadow: var(--shadow-card);
}}

/* Eyebrow & Headings */
.eyebrow {{
    display: inline-block;
    color: var(--accent);
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

h1 {{
    margin: 0 0 10px;
    color: #1A1718;
    font-size: 24px;
    line-height: 1.25;
    font-weight: 750;
    letter-spacing: -0.5px;
}}

.intro-desc {{
    color: var(--text-secondary);
    font-size: 14px;
    line-height: 1.55;
    margin-bottom: 20px;
}}

/* Complaint Reference Box */
.complaint-pill-box {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 14px;
    background: var(--surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    margin-bottom: 22px;
}}

.complaint-meta {{
    display: flex;
    flex-direction: column;
}}

.complaint-label {{
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--text-muted);
    line-height: 1.2;
}}

.complaint-code {{
    font-size: 14px;
    font-weight: 700;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: var(--text-primary);
    letter-spacing: -0.2px;
    margin-top: 2px;
}}

.complaint-status-chip {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 8px;
    background: #FFFFFF;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-full);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
}}

.complaint-status-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
}}

/* Action Cards Group */
.action-cards-stack {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
}}

/* Matched Action Cards (Photo & Location) */
.action-card {{
    width: 100%;
    min-height: 76px;
    background: #FFFFFF;
    border: 1.5px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 14px 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    cursor: pointer;
    text-align: left;
    outline: none;
    text-decoration: none;
    font-family: inherit;
    transition: 
        border-color 0.18s ease,
        background-color 0.18s ease,
        box-shadow 0.18s ease,
        transform 0.12s ease;
    box-shadow: var(--shadow-sm);
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    position: relative;
}}

.action-card:hover {{
    border-color: var(--border-strong);
    background-color: var(--surface-subtle);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}}

.action-card:active {{
    transform: translateY(0) scale(0.992);
}}

.action-card:focus-visible {{
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-light);
}}

/* Icon Box inside Action Card */
.action-icon-box {{
    width: 44px;
    height: 44px;
    flex-shrink: 0;
    border-radius: var(--radius-md);
    background: var(--accent-light);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease, color 0.2s ease;
}}

.action-icon-box svg {{
    width: 22px;
    height: 22px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.85;
    stroke-linecap: round;
    stroke-linejoin: round;
}}

/* Text within Action Card */
.action-content {{
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
}}

.action-title {{
    font-size: 14.5px;
    font-weight: 650;
    color: var(--text-primary);
    line-height: 1.3;
    letter-spacing: -0.2px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.action-sub {{
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.4;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

/* Right affordance indicator */
.action-affordance {{
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-tertiary);
    transition: color 0.18s ease, transform 0.18s ease;
}}

.action-affordance svg {{
    width: 16px;
    height: 16px;
    stroke-width: 2;
    stroke: currentColor;
    fill: none;
}}

.action-card:hover .action-affordance {{
    color: var(--accent);
    transform: translateX(1px);
}}

/* Success State for Action Cards */
.action-card.is-success {{
    border-color: var(--success-border);
    background-color: var(--success-bg);
}}

.action-card.is-success:hover {{
    border-color: #A3D8BD;
    background-color: #EBF6EF;
}}

.action-card.is-success .action-icon-box {{
    background-color: #E2F2E9;
    color: var(--success-accent);
}}

.action-card.is-success .action-title {{
    color: #124D31;
    font-weight: 700;
}}

.action-card.is-success .action-sub {{
    color: #2D6A4F;
}}

.action-card.is-success .action-affordance {{
    color: var(--success-accent);
}}

/* Warning / Notice State */
.action-card.is-warning {{
    border-color: var(--warning-border);
    background-color: var(--warning-bg);
}}

.action-card.is-warning .action-icon-box {{
    background-color: #FEEAD8;
    color: var(--warning-accent);
}}

.action-card.is-warning .action-title {{
    color: var(--warning-accent);
}}

.action-card.is-warning .action-sub {{
    color: #7C2D12;
}}

/* Loading pulse */
@keyframes spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}

.spinner-icon {{
    animation: spin 0.9s linear infinite;
}}

/* Privacy / Trust Note */
.privacy-note {{
    margin: 18px 0 22px;
    padding: 12px 14px;
    background: var(--surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    display: flex;
    align-items: flex-start;
    gap: 10px;
}}

.privacy-icon {{
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    margin-top: 1px;
    color: var(--accent);
}}

.privacy-text {{
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-secondary);
}}

/* Section Divider */
.form-divider {{
    height: 1px;
    background: var(--border-subtle);
    margin: 20px 0;
    border: 0;
}}

/* Primary Submit CTA */
.primary-btn {{
    width: 100%;
    min-height: 52px;
    padding: 14px 20px;
    border: 0;
    border-radius: var(--radius-lg);
    background: var(--accent);
    background: linear-gradient(180deg, #7A333B 0%, #682930 100%);
    color: #FFFFFF;
    font-family: inherit;
    font-size: 15.5px;
    font-weight: 650;
    letter-spacing: 0.15px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    box-shadow: var(--shadow-btn);
    transition: 
        background 0.18s ease,
        box-shadow 0.18s ease,
        transform 0.12s ease,
        opacity 0.18s ease;
    -webkit-tap-highlight-color: transparent;
}}

.primary-btn:hover {{
    background: linear-gradient(180deg, #682930 0%, #57232A 100%);
    box-shadow: var(--shadow-btn-hover);
    transform: translateY(-1px);
}}

.primary-btn:active {{
    transform: translateY(0) scale(0.992);
    box-shadow: var(--shadow-btn);
}}

.primary-btn:focus-visible {{
    outline: none;
    box-shadow: 0 0 0 3px rgba(114, 47, 55, 0.28);
}}

.primary-btn:disabled {{
    opacity: 0.65;
    cursor: not-allowed;
    transform: none;
}}

/* Secondary Action Button (Back / Retry) */
.secondary-btn {{
    width: 100%;
    min-height: 48px;
    padding: 12px 18px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    background: #FFFFFF;
    color: var(--text-primary);
    font-family: inherit;
    font-size: 14.5px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: background-color 0.16s ease, border-color 0.16s ease, transform 0.12s ease;
    margin-top: 18px;
}}

.secondary-btn:hover {{
    background-color: var(--surface-subtle);
    border-color: var(--text-muted);
    transform: translateY(-1px);
}}

.secondary-btn:active {{
    transform: translateY(0);
}}

/* Validation Alert Banner */
.validation-banner {{
    margin-bottom: 16px;
    padding: 11px 14px;
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    border-radius: var(--radius-md);
    color: var(--error-accent);
    font-size: 13px;
    font-weight: 550;
    line-height: 1.4;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: fadeIn 0.2s ease-out;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(-4px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* State Cards (Success / Error pages) */
.state-center {{
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
}}

.state-badge-icon {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 18px;
}}

.state-badge-icon.success {{
    background: #EAF6EE;
    color: #1E6B47;
    border: 1px solid #C4E7D2;
}}

.state-badge-icon.error {{
    background: #FDF2F2;
    color: #B91C1C;
    border: 1px solid #FACDCD;
}}

.state-badge-icon svg {{
    width: 28px;
    height: 28px;
    stroke-width: 2.2;
}}

.state-desc {{
    color: var(--text-secondary);
    font-size: 14.5px;
    line-height: 1.55;
    margin-bottom: 14px;
}}

.state-card-info {{
    width: 100%;
    padding: 14px;
    background: var(--surface-subtle);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    margin: 14px 0 6px;
    font-size: 13px;
    color: var(--text-secondary);
    text-align: center;
}}

/* Footer */
.secure-footer {{
    width: 100%;
    max-width: 520px;
    margin: 20px auto 0;
    text-align: center;
    color: #8C8580;
    font-size: 11.5px;
    line-height: 1.5;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}}

.secure-dot {{
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--success-accent);
}}

/* Responsive Breakpoints */
@media (max-width: 540px) {{
    body {{
        padding: 16px 12px 32px;
    }}

    .card {{
        padding: 24px 18px;
        border-radius: var(--radius-lg);
    }}

    h1 {{
        font-size: 21px;
    }}

    .brand-mark {{
        width: 36px;
        height: 36px;
        border-radius: 10px;
        font-size: 13px;
    }}

    .brand-name {{
        font-size: 14.5px;
    }}

    .action-card {{
        min-height: 72px;
        padding: 12px 14px;
        gap: 12px;
    }}

    .action-icon-box {{
        width: 40px;
        height: 40px;
    }}

    .action-icon-box svg {{
        width: 20px;
        height: 20px;
    }}

    .action-title {{
        font-size: 14px;
    }}

    .action-sub {{
        font-size: 11.5px;
    }}

    .primary-btn {{
        min-height: 50px;
        font-size: 15px;
    }}
}}
</style>
</head>

<body>
<header class="brand-shell">
    <div class="brand-left">
        <div class="brand-mark">CR</div>
        <div class="brand-text">
            <div class="brand-name">CivicResolve AI</div>
            <div class="brand-sub">Secure citizen evidence portal</div>
        </div>
    </div>
    <div class="secure-badge">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
        <span>Verified Portal</span>
    </div>
</header>

<main class="card">
{body}
</main>

<footer class="secure-footer">
    <span class="secure-dot"></span>
    <span>Official encrypted evidence portal · CivicResolve AI</span>
</footer>
</body>
</html>""".strip()


def error_page(
    message: str,
) -> HTMLResponse:
    return HTMLResponse(
        page_shell(
            "Evidence Link Expired",
            f"""
<div class="state-center">
    <div class="state-badge-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    
    <div class="eyebrow">Link Status</div>
    <h1>Link unavailable</h1>
    <p class="state-desc">{html.escape(message)}</p>
    
    <div class="state-card-info">
        <strong>Important:</strong> Your original report is securely registered and active in the system.
    </div>
</div>
""",
        ),
        status_code=410,
    )


@router.get(
    "/evidence/{token}",
    response_class=HTMLResponse,
)
async def evidence_page(
    token: str,
):
    store = EvidenceLinkStore()

    try:
        record = store.resolve(
            token
        )
    except EvidenceLinkError as exc:
        return error_page(
            str(exc)
        )

    complaint_id = html.escape(
        record["complaint_id"]
    )

    body = f"""
<div class="eyebrow">Evidence Submission</div>
<h1>Add evidence to your report</h1>

<p class="intro-desc">
Help the civic response team verify and resolve your issue faster. You can attach a photo, your current location, or both.
</p>

<div class="complaint-pill-box">
    <div class="complaint-meta">
        <span class="complaint-label">Complaint Reference</span>
        <span class="complaint-code">{complaint_id}</span>
    </div>
    <div class="complaint-status-chip">
        <span class="complaint-status-dot"></span>
        <span>Active Case</span>
    </div>
</div>

<form
    id="evidenceForm"
    method="post"
    action="/evidence/{html.escape(token)}/submit"
    enctype="multipart/form-data"
>

    <!-- Hidden Native File Input -->
    <input
        id="image"
        name="image"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        capture="environment"
        style="position: absolute; width: 0.1px; height: 0.1px; opacity: 0; pointer-events: none; overflow: hidden;"
        onchange="handlePhotoSelect(this)"
    >

    <!-- Hidden GPS Form Fields -->
    <input
        id="latitude"
        name="latitude"
        type="hidden"
    >
    <input
        id="longitude"
        name="longitude"
        type="hidden"
    >
    <input
        id="gps_accuracy"
        name="gps_accuracy"
        type="hidden"
    >
    <input
        id="location_confirmed"
        name="location_confirmed"
        type="hidden"
        value="false"
    >

    <!-- Matched Action Cards -->
    <div class="action-cards-stack">
        <!-- Photo Action Card -->
        <div 
            id="photoCard"
            class="action-card"
            onclick="triggerPhotoUpload()"
            role="button"
            tabindex="0"
            aria-label="Add a photo"
            onkeydown="if(event.key==='Enter'||event.key===' '){{event.preventDefault();triggerPhotoUpload();}}"
        >
            <div id="photoIconBox" class="action-icon-box">
                <!-- Camera Icon -->
                <svg id="photoIconSvg" viewBox="0 0 24 24">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                </svg>
            </div>
            <div class="action-content">
                <div id="photoTitle" class="action-title">Add Photo</div>
                <div id="photoSub" class="action-sub">Take a photo or upload from your device</div>
            </div>
            <div class="action-affordance">
                <svg viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </div>

        <!-- Location Action Card -->
        <button
            id="locationCard"
            type="button"
            class="action-card"
            onclick="getLocation()"
            aria-label="Use current location"
        >
            <div id="locationIconBox" class="action-icon-box">
                <!-- Location Pin Icon -->
                <svg id="locationIconSvg" viewBox="0 0 24 24">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
            </div>
            <div class="action-content">
                <div id="locationTitle" class="action-title">Use Current Location</div>
                <div id="locationSub" class="action-sub">Share the precise location of this issue</div>
            </div>
            <div class="action-affordance">
                <svg viewBox="0 0 24 24">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
        </button>
    </div>

    <!-- Hidden compatibility status element if queried -->
    <div id="locationStatus" style="display:none;"></div>

    <!-- Reassuring Privacy / Optional Message -->
    <div class="privacy-note">
        <svg class="privacy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
        <div class="privacy-text">
            Photo and precise location are optional and are only shared when you choose to provide them.
        </div>
    </div>

    <!-- Validation Banner (shown if user clicks submit without any evidence) -->
    <div id="validationBanner" class="validation-banner" style="display: none;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span>Please add a photo, your current location, or both before submitting.</span>
    </div>

    <!-- Primary Submit CTA -->
    <button
        id="submitBtn"
        type="submit"
        class="primary-btn"
    >
        <span>Submit Evidence</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
        </svg>
    </button>

</form>

<script>
function triggerPhotoUpload() {{
    document.getElementById('image').click();
}}

function formatFileSize(bytes) {{
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}}

function handlePhotoSelect(input) {{
    const photoCard = document.getElementById('photoCard');
    const photoTitle = document.getElementById('photoTitle');
    const photoSub = document.getElementById('photoSub');
    const photoIconBox = document.getElementById('photoIconBox');
    const validationBanner = document.getElementById('validationBanner');

    if (input.files && input.files[0]) {{
        const file = input.files[0];
        const sizeStr = formatFileSize(file.size);

        photoCard.classList.add('is-success');
        photoIconBox.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        photoTitle.innerHTML = '✓ Photo Selected';
        photoSub.textContent = file.name + ' (' + sizeStr + ')';

        if (validationBanner) {{
            validationBanner.style.display = 'none';
        }}
    }}
}}

function getLocation() {{
    const locationCard = document.getElementById('locationCard');
    const locationTitle = document.getElementById('locationTitle');
    const locationSub = document.getElementById('locationSub');
    const locationIconBox = document.getElementById('locationIconBox');
    const legacyStatus = document.getElementById('locationStatus');
    const validationBanner = document.getElementById('validationBanner');

    if (!navigator.geolocation) {{
        locationCard.classList.add('is-warning');
        locationTitle.textContent = 'Location Unsupported';
        locationSub.textContent = 'GPS is not supported by your browser.';
        if (legacyStatus) {{
            legacyStatus.textContent = 'Location is not supported by this browser.';
        }}
        return;
    }}

    locationCard.classList.remove('is-success', 'is-warning');
    locationTitle.textContent = 'Requesting GPS...';
    locationSub.textContent = 'Please allow location permission when prompted.';
    locationIconBox.innerHTML = '<svg class="spinner-icon" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>';

    if (legacyStatus) {{
        legacyStatus.textContent = 'Requesting location permission...';
    }}

    navigator.geolocation.getCurrentPosition(
        function(position) {{
            document.getElementById('latitude').value = position.coords.latitude;
            document.getElementById('longitude').value = position.coords.longitude;
            document.getElementById('gps_accuracy').value = position.coords.accuracy || '';
            document.getElementById('location_confirmed').value = 'true';

            const accuracy = Math.round(position.coords.accuracy || 0);
            const accuracyText = accuracy > 0 
                ? 'Accurate to approximately ±' + accuracy + ' m'
                : 'Precise coordinates captured';

            locationCard.classList.remove('is-warning');
            locationCard.classList.add('is-success');
            locationIconBox.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            locationTitle.innerHTML = '✓ Location Captured';
            locationSub.textContent = accuracyText;

            if (legacyStatus) {{
                legacyStatus.textContent = '✓ Current location added. Accuracy: approximately ' + accuracy + ' meters.';
            }}

            if (validationBanner) {{
                validationBanner.style.display = 'none';
            }}
        }},
        function(error) {{
            document.getElementById('location_confirmed').value = 'false';
            
            locationCard.classList.remove('is-success');
            locationCard.classList.add('is-warning');
            locationIconBox.innerHTML = '<svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>';
            locationTitle.textContent = 'Location Not Added';
            locationSub.textContent = 'Permission denied or timed out. You can still submit a photo.';

            if (legacyStatus) {{
                legacyStatus.textContent = 'Location was not added. You can still submit a photo.';
            }}
        }},
        {{
            enableHighAccuracy: true,
            timeout: 12000,
            maximumAge: 0
        }}
    );
}}

document.getElementById('evidenceForm').addEventListener('submit', function(event) {{
    const image = document.getElementById('image');
    const confirmed = document.getElementById('location_confirmed').value === 'true';
    const hasImage = image.files && image.files.length > 0;
    const validationBanner = document.getElementById('validationBanner');
    const submitBtn = document.getElementById('submitBtn');

    if (!hasImage && !confirmed) {{
        event.preventDefault();
        if (validationBanner) {{
            validationBanner.style.display = 'flex';
            validationBanner.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }} else {{
            alert('Please add a photo, your current location, or both.');
        }}
        return;
    }}

    if (submitBtn) {{
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Uploading evidence...</span><svg class="spinner-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>';
    }}
}});
</script>
"""

    return HTMLResponse(
        page_shell(
            "CivicResolve Evidence",
            body,
        )
    )


@router.post(
    "/evidence/{token}/submit",
    response_class=HTMLResponse,
)
async def submit_evidence(
    token: str,
    image: UploadFile | None = File(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    gps_accuracy: float | None = Form(None),
    location_confirmed: bool = Form(False),
):
    store = EvidenceLinkStore()

    try:
        record = store.resolve(
            token
        )
    except EvidenceLinkError as exc:
        return error_page(
            str(exc)
        )

    complaint_id = (
        record["complaint_id"]
    )

    has_image = bool(
        image
        and image.filename
    )

    if (
        not has_image
        and not location_confirmed
    ):
        return HTMLResponse(
            page_shell(
                "Evidence Required",
                """
<div class="state-center">
    <div class="state-badge-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    
    <div class="eyebrow">Submission Incomplete</div>
    <h1>No evidence provided</h1>
    <p class="state-desc">Please attach a photo or confirm your current location before submitting.</p>
    
    <button class="secondary-btn" onclick="history.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>Return to Form</span>
    </button>
</div>
""",
            ),
            status_code=400,
        )

    data = {
        "location_confirmed": (
            "true"
            if location_confirmed
            else "false"
        ),
    }

    if latitude is not None:
        data["latitude"] = str(
            latitude
        )

    if longitude is not None:
        data["longitude"] = str(
            longitude
        )

    if gps_accuracy is not None:
        data["gps_accuracy"] = str(
            gps_accuracy
        )

    files = None

    if has_image:
        image_bytes = await image.read()

        if len(image_bytes) > (
            8 * 1024 * 1024
        ):
            return HTMLResponse(
                page_shell(
                    "Image Too Large",
                    """
<div class="state-center">
    <div class="state-badge-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
    </div>
    
    <div class="eyebrow">File Size Limit</div>
    <h1>Photo is too large</h1>
    <p class="state-desc">Please choose an image smaller than 8 MB to ensure fast and reliable upload.</p>
    
    <button class="secondary-btn" onclick="history.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>Choose a Different Photo</span>
    </button>
</div>
""",
                ),
                status_code=413,
            )

        files = {
            "image": (
                image.filename,
                image_bytes,
                image.content_type
                or "image/jpeg",
            )
        }

    base_url = os.getenv(
        "CIVICRESOLVE_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    endpoint = (
        f"{base_url}"
        f"/api/complaints/"
        f"{complaint_id}"
        f"/evidence"
    )

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                endpoint,
                data=data,
                files=files,
            )
    except Exception:
        return HTMLResponse(
            page_shell(
                "Temporary Error",
                """
<div class="state-center">
    <div class="state-badge-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    
    <div class="eyebrow">Connection Notice</div>
    <h1>Could not upload evidence</h1>
    <p class="state-desc">We encountered a temporary connection issue. Your original complaint remains safely registered.</p>
    
    <button class="secondary-btn" onclick="history.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>Try Again</span>
    </button>
</div>
""",
            ),
            status_code=502,
        )

    if response.status_code >= 400:
        try:
            message = (
                response.json().get(
                    "detail",
                    "Evidence upload failed.",
                )
            )
        except Exception:
            message = (
                "Evidence upload failed."
            )

        return HTMLResponse(
            page_shell(
                "Upload Failed",
                f"""
<div class="state-center">
    <div class="state-badge-icon error">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    
    <div class="eyebrow">Upload Status</div>
    <h1>Could not attach evidence</h1>
    <p class="state-desc">{html.escape(str(message))}</p>
    
    <div class="state-card-info">
        Your original complaint remains registered and active.
    </div>
    
    <button class="secondary-btn" onclick="history.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
        <span>Try Again</span>
    </button>
</div>
""",
            ),
            status_code=502,
        )

    store.mark_used(
        token
    )

    return HTMLResponse(
        page_shell(
            "Evidence Attached",
            f"""
<div class="state-center">
    <div class="state-badge-icon success">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
    </div>
    
    <div class="eyebrow">Submission Complete</div>
    <h1>Evidence submitted ✓</h1>
    
    <p class="state-desc">
        Your evidence has been securely attached to complaint <strong>{html.escape(complaint_id)}</strong>.
    </p>

    <div class="state-card-info">
        Our civic teams have received your update. You may safely close this browser window.
    </div>
</div>
""",
        )
    )
