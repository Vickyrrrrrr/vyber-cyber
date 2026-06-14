import os
import time
import html
import re
import threading
import gradio as gr
import modal

# Premium minimalist grey-and-white developer stylesheet
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

/* ============================================================
   GLOBAL PALETTE LOCK — prevents ALL Gradio dark-mode bleed
   Applied to every selector Gradio uses for theming
   ============================================================ */
:root,
html,
body,
.gradio-container,
.dark,
html.dark,
.dark body,
.dark .gradio-container,
.dark .block,
.dark .form,
.dark .wrap,
[data-testid="block"],
.dark [data-testid="block"] {
    --body-background-fill:          #faf8f5 !important;
    --body-text-color:               #231f1d !important;
    --background-fill-primary:       #faf8f5 !important;
    --background-fill-secondary:     #f2ece4 !important;
    --border-color-primary:          #e6dfd5 !important;
    --border-color-secondary:        #e6dfd5 !important;
    --input-background-fill:         #ffffff !important;
    --input-border-color:            #e6dfd5 !important;
    --input-text-color:              #231f1d !important;
    --block-background-fill:         #ffffff !important;
    --block-border-color:            #e6dfd5 !important;
    --block-title-text-color:        #231f1d !important;
    --block-label-text-color:        #594c43 !important;
    --button-primary-background-fill:       #802f1a !important;
    --button-primary-background-fill-hover: #692412 !important;
    --button-primary-text-color:     #ffffff !important;
    --button-primary-border-color:   #802f1a !important;
    --button-secondary-background-fill: #ffffff !important;
    --button-secondary-text-color:   #231f1d !important;
    --button-secondary-border-color: #e6dfd5 !important;
    --color-accent:                  #802f1a !important;
    --link-text-color:               #802f1a !important;
    --link-text-color-hover:         #692412 !important;
    --shadow-drop:                   none !important;
    --shadow-drop-lg:                none !important;
    --shadow-inset:                  none !important;
    background-color: #faf8f5 !important;
    color: #231f1d !important;
}

/* ============================================================
   BASE ELEMENTS — no text shadows, no dark bleed
   ============================================================ */
*, *::before, *::after {
    text-shadow: none !important;
    box-shadow: none !important;
}

html, body {
    background-color: #faf8f5 !important;
    color: #231f1d !important;
    -webkit-text-fill-color: #231f1d !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.gradio-container {
    background-color: #faf8f5 !important;
    border: none !important;
    max-width: 95% !important;
    width: 95% !important;
    margin: 20px auto !important;
    padding: 24px !important;
    box-shadow: none !important;
}

/* Ensure dropdowns, select options, and textboxes remain clean white with dark text */
.gr-dropdown, .gr-input, .gr-box, select, input, textarea {
    background-color: #ffffff !important;
    border: 1px solid #e6dfd5 !important;
    border-radius: 4px !important;
    color: #231f1d !important;
}

.dark select, .dark input, .dark .gr-dropdown {
    background-color: #ffffff !important;
    color: #231f1d !important;
}

/* ── RED TEAM TERMINAL — warm dark crimson tint ── */
.red-terminal textarea,
.red-terminal textarea:focus,
.red-terminal textarea:disabled,
.red-terminal textarea[readonly],
.dark .red-terminal textarea,
.dark .red-terminal textarea:focus,
.dark .red-terminal textarea:disabled,
.dark .red-terminal textarea[readonly] {
    background-color: #1c1110 !important;
    background: #1c1110 !important;
    border: 1px solid #3d1c18 !important;
    border-left: 3px solid #802f1a !important;
    border-radius: 4px !important;
    color: #f5e6e0 !important;
    -webkit-text-fill-color: #f5e6e0 !important;
    opacity: 1 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.875rem !important;
    line-height: 1.7 !important;
    padding: 20px 20px 20px 18px !important;
    resize: none !important;
    text-shadow: none !important;
    box-shadow: none !important;
    caret-color: #f5e6e0 !important;
}
.red-terminal .wrap,
.dark .red-terminal .wrap {
    background-color: #1c1110 !important;
    border-color: #3d1c18 !important;
}
.red-terminal label, .red-terminal .block-label,
.dark .red-terminal label, .dark .red-terminal .block-label {
    color: #a06050 !important;
    -webkit-text-fill-color: #a06050 !important;
    background: transparent !important;
}
.red-terminal textarea::-webkit-scrollbar { width: 5px; }
.red-terminal textarea::-webkit-scrollbar-track { background: #1c1110; }
.red-terminal textarea::-webkit-scrollbar-thumb { background: #5a2018; border-radius: 3px; }

.operation-terminal {
    background: transparent !important;
    border: none !important;
    scroll-margin-top: 18px !important;
}

.operation-shell {
    background-color: #111312 !important;
    border: 1px solid #25221f !important;
    border-left: 3px solid #802f1a !important;
    border-radius: 4px !important;
    box-shadow: none !important;
    min-height: 520px !important;
    max-height: 68vh !important;
    overflow: auto !important;
    padding: 24px 28px !important;
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
}

.operation-shell pre {
    margin: 0 !important;
    white-space: pre-wrap !important;
    overflow-wrap: anywhere !important;
    color: #f0e7d8 !important;
    -webkit-text-fill-color: #f0e7d8 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    line-height: 1.62 !important;
    text-shadow: none !important;
    background: transparent !important;
}

.operation-terminal pre,
.operation-terminal code,
.operation-terminal div,
.operation-shell pre,
.dark .operation-terminal pre,
.dark .operation-shell pre {
    color: #f0e7d8 !important;
    -webkit-text-fill-color: #f0e7d8 !important;
}

.operation-shell,
.operation-shell *,
.operation-terminal,
.operation-terminal *,
.operation-terminal::before,
.operation-terminal::after,
.operation-terminal *::before,
.operation-terminal *::after {
    animation: none !important;
    transition: none !important;
    opacity: 1 !important;
    filter: none !important;
    box-shadow: none !important;
}

.operation-shell::-webkit-scrollbar { width: 6px; }
.operation-shell::-webkit-scrollbar-track { background: #111312; }
.operation-shell::-webkit-scrollbar-thumb { background: #3b3029; border-radius: 3px; }

/* ── BLUE TEAM TERMINAL — cool dark navy tint ── */
.blue-terminal textarea,
.blue-terminal textarea:focus,
.blue-terminal textarea:disabled,
.blue-terminal textarea[readonly],
.dark .blue-terminal textarea,
.dark .blue-terminal textarea:focus,
.dark .blue-terminal textarea:disabled,
.dark .blue-terminal textarea[readonly] {
    background-color: #0f1318 !important;
    background: #0f1318 !important;
    border: 1px solid #1a2a40 !important;
    border-left: 3px solid #2a6496 !important;
    border-radius: 4px !important;
    color: #d8eaf8 !important;
    -webkit-text-fill-color: #d8eaf8 !important;
    opacity: 1 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.875rem !important;
    line-height: 1.7 !important;
    padding: 20px 20px 20px 18px !important;
    resize: none !important;
    text-shadow: none !important;
    box-shadow: none !important;
    caret-color: #d8eaf8 !important;
}
.blue-terminal .wrap,
.dark .blue-terminal .wrap {
    background-color: #0f1318 !important;
    border-color: #1a2a40 !important;
}
.blue-terminal label, .blue-terminal .block-label,
.dark .blue-terminal label, .dark .blue-terminal .block-label {
    color: #5a8aaa !important;
    -webkit-text-fill-color: #5a8aaa !important;
    background: transparent !important;
}
.blue-terminal textarea::-webkit-scrollbar { width: 5px; }
.blue-terminal textarea::-webkit-scrollbar-track { background: #0f1318; }
.blue-terminal textarea::-webkit-scrollbar-thumb { background: #1e4a6e; border-radius: 3px; }

/* Premium Minimalist Button - Rust background */
.launch-button,
.launch-button button,
button.primary,
button.primary span,
.launch-button span,
#launch-duel-button,
#launch-duel-button button,
#launch-duel-button span {
    background-color: #802f1a !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #802f1a !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 24px !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
}

#launch-duel-button *,
.launch-button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.launch-button:hover,
.launch-button:hover button,
button.primary:hover {
    background-color: #692412 !important;
    border-color: #692412 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.launch-button:focus,
.launch-button button:focus,
button.primary:focus {
    outline: 2px solid #c99584 !important;
    outline-offset: 2px !important;
}

.launch-button:disabled,
.launch-button button:disabled,
button.primary:disabled {
    background-color: #a88478 !important;
    border-color: #a88478 !important;
    color: #fff8f3 !important;
    -webkit-text-fill-color: #fff8f3 !important;
}

.live-button,
.live-button button,
.live-button span {
    background-color: #ffffff !important;
    color: #802f1a !important;
    -webkit-text-fill-color: #802f1a !important;
    border: 1px solid #c99584 !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 24px !important;
}

.live-button *,
.live-button button *,
.live-button span {
    color: #802f1a !important;
    -webkit-text-fill-color: #802f1a !important;
}

.live-button:hover,
.live-button:hover button {
    background-color: #f7f2eb !important;
    border-color: #802f1a !important;
}

.live-button:focus,
.live-button button:focus {
    outline: 2px solid #c99584 !important;
    outline-offset: 2px !important;
}

.live-button:disabled,
.live-button button:disabled,
.live-button[aria-disabled="true"],
.live-button button[aria-disabled="true"],
.live-button.disabled,
.live-button .disabled {
    background-color: #f2ece4 !important;
    color: #594c43 !important;
    -webkit-text-fill-color: #594c43 !important;
    border-color: #d7cab9 !important;
    opacity: 1 !important;
}

.live-button:disabled *,
.live-button button:disabled *,
.live-button[aria-disabled="true"] *,
.live-button button[aria-disabled="true"] *,
.live-button.disabled *,
.live-button .disabled * {
    color: #594c43 !important;
    -webkit-text-fill-color: #594c43 !important;
}

.action-row {
    align-items: end !important;
    gap: 20px !important;
}

.action-row .scenario-selector {
    flex: 1 1 auto !important;
}

.action-row .launch-button,
.action-row .live-button {
    flex: 0 0 auto !important;
    min-width: 190px !important;
    max-width: 260px !important;
}

.action-row .launch-button button,
.action-row .live-button button {
    min-height: 48px !important;
    width: 100% !important;
    padding: 10px 18px !important;
}

@media (max-width: 900px) {
    .action-row .launch-button,
    .action-row .live-button {
        min-width: 100% !important;
        max-width: 100% !important;
    }
}

.hero {
    text-align: center !important;
    max-width: 860px !important;
    margin: 2px auto 30px auto !important;
    padding: 4px 0 0 0 !important;
}

.hero-eyebrow {
    color: #802f1a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0 !important;
    margin: 0 0 8px 0 !important;
    text-transform: uppercase !important;
}

.hero h1 {
    color: #231f1d !important;
    font-family: 'Playfair Display', 'Georgia', serif !important;
    font-size: 3rem !important;
    line-height: 1.05 !important;
    letter-spacing: 0 !important;
    margin: 0 0 14px 0 !important;
    font-weight: 700 !important;
}

.hero-lead {
    color: #3a332f !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 1.04rem !important;
    line-height: 1.62 !important;
    max-width: 720px !important;
    margin: 0 auto 18px auto !important;
}

.hero-meta {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
}

.hero-meta span {
    background: #f2ece4 !important;
    border: 1px solid #e6dfd5 !important;
    border-radius: 999px !important;
    color: #594c43 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    padding: 8px 11px !important;
}

/* Status Banner - Warm gray/beige banner with high contrast text */
#status-banner {
    background-color: #f2ece4 !important;
    border: 1px solid #e6dfd5 !important;
    border-radius: 4px !important;
    padding: 14px 20px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
}

#status-banner, #status-banner p, #status-banner span {
    color: #802f1a !important;
}

.lab-note {
    background-color: #f7f2eb !important;
    border: 1px solid #e6dfd5 !important;
    border-radius: 4px !important;
    padding: 12px 16px !important;
    margin: 4px 0 16px 0 !important;
    color: #594c43 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    line-height: 1.55 !important;
}

.lab-note strong {
    color: #802f1a !important;
    font-weight: 600 !important;
}

/* Labels and Markdown titles */
h3 {
    font-family: 'Playfair Display', serif !important;
    color: #231f1d !important;
    font-weight: 700 !important;
    margin-top: 10px !important;
}

.block-label, .gr-label {
    color: #594c43 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0 !important;
}
"""

SCENARIO_CHOICES = [
    "Scenario 1: Insecure Configuration File (Secret Leak)",
    "Scenario 2: Exposed Database Port (Global Binding)",
    "Scenario 3: Unencrypted Communication Pipeline (MITM)",
    "Lab Pack 4: DVWA-style SQL Injection & Weak Sessions",
    "Lab Pack 5: Juice Shop-style Broken Auth & API Policy",
    "Lab Pack 6: WebGoat-style Deserialization & Upload Risk"
]

SCENARIO_MAP = {
    "Scenario 1: Insecure Configuration File (Secret Leak)": 1,
    "Scenario 2: Exposed Database Port (Global Binding)": 2,
    "Scenario 3: Unencrypted Communication Pipeline (MITM)": 3,
    "Lab Pack 4: DVWA-style SQL Injection & Weak Sessions": 4,
    "Lab Pack 5: Juice Shop-style Broken Auth & API Policy": 5,
    "Lab Pack 6: WebGoat-style Deserialization & Upload Risk": 6
}

LIVE_GPU_LOCK = threading.Lock()

DEMO_SCENARIOS = {
    1: {
        "files": ["app_config.json", "server.env", "deploy.sh"],
        "cwes": ["CWE-312", "CWE-312", "CWE-732"],
        "issues": [
            "Hardcoded API key and database password",
            "Cloud and payment credentials committed to env file",
            "World-readable deploy script with embedded DB password",
        ],
        "fixes": [
            "Moved secrets to environment references and disabled debug",
            "Removed live keys and replaced them with secret-manager placeholders",
            "Removed embedded password and hardened deploy.sh to owner-only execution",
        ],
    },
    2: {
        "files": ["db_settings.yaml", "nginx.conf", "firewall_rules.json"],
        "cwes": ["CWE-306", "CWE-327", "CWE-284"],
        "issues": [
            "Database binds publicly without authentication",
            "Weak SSL protocols and ciphers enabled",
            "Inbound firewall allows all TCP/UDP ports from the internet",
        ],
        "fixes": [
            "Bound database to localhost and required authentication",
            "Restricted TLS to modern protocols and strong ciphers",
            "Replaced broad inbound rules with least-privilege allowlist",
        ],
    },
    3: {
        "files": ["pipeline_config.json", "traffic_stream.log", "api_gateway.json"],
        "cwes": ["CWE-319", "CWE-532", "CWE-306"],
        "issues": [
            "Billing stream sends data over HTTP",
            "Traffic log contains card data and CVV",
            "Admin API is public with no auth or rate limit",
        ],
        "fixes": [
            "Upgraded endpoint to HTTPS with certificate verification",
            "Scrubbed card data and CVV from logs",
            "Enabled auth, rate limiting, and private admin routes",
        ],
    },
    4: {
        "files": ["login_handler.py", "session_config.json", "access_audit.log"],
        "cwes": ["CWE-89", "CWE-352", "CWE-532"],
        "issues": [
            "Login flow builds SQL with string interpolation",
            "Session cookies are weak and CSRF is disabled",
            "Access logs expose password payloads and reset tokens",
        ],
        "fixes": [
            "Rewrote login query with parameterized inputs",
            "Rotated session secret and enabled secure cookies plus CSRF",
            "Removed credential payloads and reset tokens from audit logs",
        ],
    },
    5: {
        "files": ["auth_routes.js", "api_policy.json", "payment_debug.log"],
        "cwes": ["CWE-347", "CWE-942", "CWE-532"],
        "issues": [
            "JWT admin check trusts decoded unsigned tokens",
            "API policy allows wildcard CORS and public admin access",
            "Payment debug log leaks card data and JWT-like tokens",
        ],
        "fixes": [
            "Switched to verified JWTs with env-backed signing secret",
            "Scoped CORS, required auth, added rate limit, and privatized admin routes",
            "Scrubbed card data, CVV, and token values from debug logs",
        ],
    },
    6: {
        "files": ["profile_importer.py", "upload_policy.yaml", "worker_permissions.json"],
        "cwes": ["CWE-502", "CWE-434", "CWE-250"],
        "issues": [
            "Profile importer deserializes untrusted pickle data",
            "Upload policy accepts wildcard executable content",
            "Worker runs as root with shell and unrestricted egress",
        ],
        "fixes": [
            "Replaced pickle with JSON parsing and schema validation",
            "Restricted upload types, enabled scanning, and moved storage outside webroot",
            "Dropped root privileges, disabled shell spawning, and restricted egress",
        ],
    },
}

def clean_console(text):
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    replacements = {
        "✓": "PASS",
        "✗": "FAIL",
        "▶": "...",
        "—": "-",
        "–": "-",
        "→": "->",
        "─": "-",
        "━": "-",
        "╔": "+",
        "╗": "+",
        "╚": "+",
        "╝": "+",
        "║": "|",
        "├": "|",
        "│": "|",
        "└": "|",
        "\\n": "\n",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def format_operation_trace(red_out, blue_out, backend_label="Hugging Face Space UI -> Modal GPU worker"):
    red = clean_console(red_out or "").strip()
    blue = clean_console(blue_out or "").strip()

    lines = [
        "VYBER OPERATION TRACE",
        "mode        : autonomous cyber-range",
        "model       : vxkyyy/vyber-security-7b-gguf",
        f"backend     : {backend_label}",
        "workspace   : /tmp/sandbox",
        "",
        "PHASE 01 / RED TEAM DISCOVERY",
        "------------------------------------------------------------",
    ]

    if red:
        lines.append(red)
    else:
        lines.append("waiting for target initialization")

    blue_ready = any(marker in (red_out or "") for marker in [
        "EXPLOIT REPORT COMMITTED",
        "SCOREBOARD",
        "FINAL VERDICT"
    ]) or any(marker in (blue_out or "") for marker in [
        "BLUE AGENT",
        "PATCH_COMPLETE",
        "ACTION",
        "FINAL VERDICT"
    ])

    if blue_ready and blue:
        lines.extend([
            "",
            "PHASE 02 / BLUE TEAM REMEDIATION",
            "------------------------------------------------------------",
            blue,
        ])

    text = "\n".join(lines)
    return (
        "<div class='operation-shell'>"
        "<pre style='color:#f0e7d8 !important;-webkit-text-fill-color:#f0e7d8 !important;'>"
        + html.escape(text) +
        "</pre></div>"
    )

def run_demo_replay(scenario_name):
    scenario_id = SCENARIO_MAP.get(scenario_name, 1)
    demo = DEMO_SCENARIOS[scenario_id]
    ids = [f"S{scenario_id}-V{i}" for i in range(1, 4)]

    red = (
        "vyber-range v1.0  //  red-team agent shell\n"
        "----------------------------------------------\n"
        f"  [demo] scenario   : {scenario_id}\n"
        "  [demo] status     : target files deployed\n"
    )
    yield format_operation_trace(red, "", "Demo replay (no GPU)"), "Status: Demo replay started - no GPU credits used"
    time.sleep(0.4)

    red += "\n+--------------------------------------------+\n"
    red += "|  THREAT SURFACE  3 VULNERABILITIES PLANTED |\n"
    red += "+--------------------------------------------+\n"
    for vuln_id, cwe, filename, issue in zip(ids, demo["cwes"], demo["files"], demo["issues"]):
        red += f"  [OPEN]  {vuln_id}  {cwe}  {filename}\n"
        red += f"          {issue}\n"
    yield format_operation_trace(red, "", "Demo replay (no GPU)"), "Status: Demo Red Agent mapped the threat surface"
    time.sleep(0.5)

    red += "\n+--------------------------------------------+\n"
    red += "|  ROUND 1  EXPLOIT REPORT COMMITTED         |\n"
    red += "+--------------------------------------------+\n"
    for vuln_id, cwe, filename, issue in zip(ids, demo["cwes"], demo["files"], demo["issues"]):
        red += f"  FINDING {vuln_id}\n"
        red += f"  FILE: {filename}\n"
        red += f"  CWE: {cwe}\n"
        red += "  SEVERITY: High\n"
        red += f"  EVIDENCE: {issue}\n"
        red += f"  ATTACK_PATH: Red replays the lab exploit against {filename}.\n"
        red += f"  IMPACT: {issue}\n"
    yield format_operation_trace(red, "", "Demo replay (no GPU)"), "Status: Demo Red Agent committed exploit report"
    time.sleep(0.5)

    blue = (
        "vyber-range v1.0  //  blue-team SOC shell\n"
        "----------------------------------------------\n"
        "  [demo] telemetry  : active\n"
        "  [demo] watchdog   : monitoring /tmp/sandbox/\n"
        "  [demo] status     : exploit intel received\n"
        "\n+--------------------------------------------+\n"
        "|  ROUND 1  BLUE AGENT  VYBER HARNESS        |\n"
        "+--------------------------------------------+\n"
        "  [demo] launching Vyber patch harness\n"
    )
    for vuln_id, filename, fix in zip(ids, demo["files"], demo["fixes"]):
        blue += f"  [PATCHED] {vuln_id}  {filename}\n"
        blue += f"            {fix}\n"
    yield format_operation_trace(red, blue, "Demo replay (no GPU)"), "Status: Demo Blue Agent patched all findings"
    time.sleep(0.5)

    verdict = "\n+--------------------------------------------+\n"
    verdict += "|  ROUND 1  RED RE-ATTACK VERIFICATION       |\n"
    verdict += "+--------------------------------------------+\n"
    for vuln_id, cwe, filename in zip(ids, demo["cwes"], demo["files"]):
        verdict += f"  [BLOCKED]  {vuln_id}  {cwe}  {filename}\n"
    verdict += "\n  [demo] verdict : PASS ALL 3 EXPLOITS BLOCKED BY PATCHES\n"
    verdict += "  [demo] result  : SYSTEM SECURE\n"
    red += verdict
    blue += verdict
    yield format_operation_trace(red, blue, "Demo replay (no GPU)"), "Status: Demo complete - live GPU was not used"

def launch_duel(scenario_name):
    scenario_id = SCENARIO_MAP.get(scenario_name, 1)

    if not LIVE_GPU_LOCK.acquire(blocking=False):
        busy = (
            "vyber-range v1.0  //  live-gpu admission control\n"
            "----------------------------------------------\n"
            "  status     : live Modal GPU duel already running\n"
            "  action     : run the demo replay now, or retry live mode shortly\n"
        )
        yield format_operation_trace(busy, "", "Live Modal GPU worker"), "Status: Live GPU busy - demo replay is available"
        return

    try:
        # Immediately notify the user of real state
        yield format_operation_trace("", ""), "Status: Connecting to serverless GPU backend (provisioning node and loading weights)..."

        # Connect securely to active Modal application
        openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        try:
            # Lookup the remote function using modern from_name
            f = modal.Function.from_name("cyber-defense-range", "run_duel_stream")
            # Call generator to stream outputs character-by-character
            for red_out, blue_out, banner_txt in f.remote_gen(scenario_id, openai_api_key=openai_api_key):
                yield format_operation_trace(red_out, blue_out), f"Status: {clean_console(banner_txt)}"
        except Exception as e:
            print(f"Modal Remote Gen lookup failed: {e}. Falling back to local execution.")
            # Fallback to local import if Modal client is not fully authenticated/connected
            try:
                # We import here to avoid circular dependencies
                from backend import run_duel_stream
                # Execute generator locally (directly calls the function logic)
                for red_out, blue_out, banner_txt in run_duel_stream.local(scenario_id, openai_api_key=openai_api_key):
                    yield format_operation_trace(red_out, blue_out), f"Status: {clean_console(banner_txt)}"
            except Exception as local_err:
                print(f"Live GPU backend unavailable. Modal detail: {e}. Local fallback detail: {local_err}")
                error_msg = (
                    "Live GPU backend is currently paused to save compute cost.\n"
                    "Run Demo Replay now, or retry Live GPU Duel during the judging window."
                )
                yield format_operation_trace(clean_console(error_msg), ""), "Status: Live GPU paused - demo replay is available"
    finally:
        LIVE_GPU_LOCK.release()

# Build Gradio UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="zinc", secondary_hue="zinc"), css=css) as demo:
    gr.HTML(
        "<section class='hero'>"
        "<p class='hero-eyebrow'>Autonomous Cyber-Range</p>"
        "<h1>Vyber Duel</h1>"
        "<p class='hero-lead'>"
        "Red finds the exploit, Blue patches the code, and Red replays the same attack to verify the fix inside an isolated sandbox."
        "</p>"
        "<div class='hero-meta'>"
        "<span>Fine-tuned 7B security model</span>"
        "<span>llama.cpp on Modal GPU</span>"
        "<span>First run warms hardware and loads GGUF weights</span>"
        "</div>"
        "</section>"
    )
    
    with gr.Row(elem_classes=["action-row"]):
        scenario_dropdown = gr.Dropdown(
            choices=SCENARIO_CHOICES,
            value="Scenario 1: Insecure Configuration File (Secret Leak)",
            label="Target Cyber-Range Scenario",
            elem_classes=["scenario-selector"],
            scale=1
        )
        demo_btn = gr.Button("Run Demo Replay", variant="primary", elem_id="launch-duel-button", elem_classes=["launch-button"], scale=0, min_width=190)
        launch_btn = gr.Button("Launch Live GPU Duel", variant="secondary", elem_classes=["live-button"], scale=0, min_width=220)

    gr.HTML(
        "<div class='lab-note'>"
        "<strong>Public demo mode:</strong> Run Demo Replay is instant and uses no GPU credits. "
        "Live GPU may be paused to save compute and enabled during judging windows."
        "</div>"
    )
        
    status_banner = gr.Markdown("Status: Active sandbox waiting for execution command", elem_id="status-banner")
    
    gr.Markdown("### Operation Terminal")
    operation_terminal = gr.HTML(
        value=format_operation_trace("", ""),
        elem_id="operation-terminal",
        elem_classes=["operation-terminal"]
    )
            
    demo_btn.click(
        fn=run_demo_replay,
        inputs=scenario_dropdown,
        outputs=[operation_terminal, status_banner],
        scroll_to_output=True,
        concurrency_limit=20,
        concurrency_id="demo_replay"
    )

    launch_btn.click(
        fn=launch_duel,
        inputs=scenario_dropdown,
        outputs=[operation_terminal, status_banner],
        scroll_to_output=True,
        concurrency_limit=1,
        concurrency_id="live_gpu_duel"
    )

demo.queue(max_size=50, default_concurrency_limit=2)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
