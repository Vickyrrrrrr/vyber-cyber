import os
import time
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

.operation-terminal textarea,
.operation-terminal textarea:focus,
.operation-terminal textarea:disabled,
.operation-terminal textarea[readonly],
.dark .operation-terminal textarea,
.dark .operation-terminal textarea:focus,
.dark .operation-terminal textarea:disabled,
.dark .operation-terminal textarea[readonly] {
    background-color: #0d0f10 !important;
    background: #0d0f10 !important;
    border: 1px solid #28231f !important;
    border-left: 3px solid #802f1a !important;
    border-radius: 4px !important;
    color: #eee7dc !important;
    -webkit-text-fill-color: #eee7dc !important;
    opacity: 1 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.86rem !important;
    line-height: 1.62 !important;
    padding: 22px 24px !important;
    resize: none !important;
    text-shadow: none !important;
    box-shadow: none !important;
    caret-color: #eee7dc !important;
}
.operation-terminal .wrap,
.dark .operation-terminal .wrap {
    background-color: #0d0f10 !important;
    border-color: #28231f !important;
}
.operation-terminal label, .operation-terminal .block-label,
.dark .operation-terminal label, .dark .operation-terminal .block-label {
    color: #8c7667 !important;
    -webkit-text-fill-color: #8c7667 !important;
    background: transparent !important;
}
.operation-terminal textarea::-webkit-scrollbar { width: 6px; }
.operation-terminal textarea::-webkit-scrollbar-track { background: #0d0f10; }
.operation-terminal textarea::-webkit-scrollbar-thumb { background: #4d3328; border-radius: 3px; }

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
.launch-button, button.primary {
    background-color: #802f1a !important;
    color: #ffffff !important;
    border: 1px solid #802f1a !important;
    border-radius: 4px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 24px !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
}

.launch-button:hover, button.primary:hover {
    background-color: #692412 !important;
    border-color: #692412 !important;
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
    letter-spacing: 0.05em !important;
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

def clean_console(text):
    replacements = {
        "✓": "PASS",
        "✗": "FAIL",
        "▶": "...",
        "—": "-",
        "–": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def format_operation_trace(red_out, blue_out):
    red = clean_console(red_out or "").strip()
    blue = clean_console(blue_out or "").strip()

    lines = [
        "VYBER OPERATION TRACE",
        "mode        : autonomous cyber-range",
        "model       : vxkyyy/vyber-security-7b-gguf",
        "backend     : Hugging Face Space UI -> Modal GPU worker",
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

    return "\n".join(lines)

def launch_duel(scenario_name):
    scenario_id = SCENARIO_MAP.get(scenario_name, 1)
    
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
            error_msg = f"Red Team Agent connection error:\n{str(e)}\nLocal Fallback error:\n{str(local_err)}"
            yield clean_console(error_msg), "Status: Connection Error"

# Build Gradio UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="zinc", secondary_hue="zinc"), css=css) as demo:
    gr.HTML(
        "<div style='text-align: center; margin-bottom: 40px;'>"
        "<p style='color: #802f1a; font-family: \"Inter\", sans-serif; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.15em; margin-bottom: 12px; text-transform: uppercase;'>"
        "Autonomous Self-Healing Cyber-Range"
        "</p>"
        "<h1 style='color: #231f1d; font-family: \"Playfair Display\", \"Georgia\", serif; font-size: 3rem; margin-bottom: 12px; font-weight: 700; letter-spacing: -0.01em;'>"
        "Vyber Duel"
        "</h1>"
        "<p style='color: #802f1a; font-family: \"Playfair Display\", \"Georgia\", serif; font-size: 1.35rem; font-style: italic; margin-bottom: 20px; font-weight: 400;'>"
        "will the defense agent patch the vulnerability before the attack succeeds?"
        "</p>"
        "<p style='color: #594c43; font-family: \"Inter\", sans-serif; font-size: 1rem; max-width: 800px; margin: 0 auto; line-height: 1.6; font-weight: 400;'>"
        "A serverless cyber-range where a custom fine-tuned 7B cybersecurity model acts as both offensive attacker and defensive responder. "
        "Running on the <strong>llama.cpp</strong> runtime with local CUDA acceleration.<br/>"
        "<span style='color: #802f1a; font-size: 0.85rem; font-weight: 500;'>Note: Initial execution requires 3-4 minutes to compile CUDA wheels, spin up hardware, and load GGUF weights.</span>"
        "</p>"
        "</div>"
    )
    
    with gr.Row():
        scenario_dropdown = gr.Dropdown(
            choices=SCENARIO_CHOICES,
            value="Scenario 1: Insecure Configuration File (Secret Leak)",
            label="Target Cyber-Range Scenario",
            elem_classes=["scenario-selector"]
        )
        launch_btn = gr.Button("Launch Simulation Duel", variant="primary", elem_classes=["launch-button"])

    gr.HTML(
        "<div class='lab-note'>"
        "<strong>Curated lab packs:</strong> choose the original Vyber config range or OWASP-inspired vulnerable app patterns. "
        "Every run is generated inside an isolated sandbox, streamed live, patched by the Blue Agent, and verified by deterministic validators."
        "</div>"
    )
        
    status_banner = gr.Markdown("Status: Active sandbox waiting for execution command", elem_id="status-banner")
    
    gr.Markdown("### Operation Terminal")
    operation_terminal = gr.Textbox(
        label="Autonomous Red-to-Blue Security Trace",
        lines=34,
        max_lines=42,
        autoscroll=True,
        elem_classes=["operation-terminal"]
    )
            
    # Connect trigger to generator
    launch_btn.click(
        fn=launch_duel,
        inputs=scenario_dropdown,
        outputs=[operation_terminal, status_banner]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
