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

/* Terminals Styling - Classy dark terminal box on cream page for both light/dark wrapper states */
.red-terminal textarea, .blue-terminal textarea,
.red-terminal textarea:disabled, .blue-terminal textarea:disabled,
.red-terminal textarea[readonly], .blue-terminal textarea[readonly],
.dark .red-terminal textarea, .dark .blue-terminal textarea,
.dark .red-terminal textarea:disabled, .dark .blue-terminal textarea:disabled,
.dark .red-terminal textarea[readonly], .dark .blue-terminal textarea[readonly] {
    background-color: #181615 !important;
    border: 1px solid #e6dfd5 !important;
    border-radius: 4px !important;
    color: #faf8f5 !important;
    -webkit-text-fill-color: #faf8f5 !important;
    opacity: 1 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.875rem !important;
    line-height: 1.6 !important;
    padding: 20px !important;
    resize: none !important;
}

.red-terminal textarea:focus, .blue-terminal textarea:focus {
    border-color: #802f1a !important;
    box-shadow: none !important;
}

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

def launch_duel(scenario_name):
    # Mapping friendly name to scenario ID
    scenario_map = {
        "Scenario 1: Insecure Configuration File (Secret Leak)": 1,
        "Scenario 2: Exposed Database Port (Global Binding)": 2,
        "Scenario 3: Unencrypted Communication Pipeline (MITM)": 3
    }
    scenario_id = scenario_map.get(scenario_name, 1)
    
    # Immediately notify the user of real state
    yield "", "", "Status: Connecting to serverless GPU backend (Provisioning node & loading weights)..."
    
    # Connect securely to active Modal application
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    try:
        # Lookup the remote function using modern from_name
        f = modal.Function.from_name("cyber-defense-range", "run_duel_stream")
        # Call generator to stream outputs character-by-character
        for red_out, blue_out, banner_txt in f.remote_gen(scenario_id, openai_api_key=openai_api_key):
            yield red_out, blue_out, f"Status: {banner_txt}"
    except Exception as e:
        print(f"Modal Remote Gen lookup failed: {e}. Falling back to local execution.")
        # Fallback to local import if Modal client is not fully authenticated/connected
        try:
            # We import here to avoid circular dependencies
            from backend import run_duel_stream
            # Execute generator locally (directly calls the function logic)
            for red_out, blue_out, banner_txt in run_duel_stream.local(scenario_id, openai_api_key=openai_api_key):
                yield red_out, blue_out, f"Status: {banner_txt}"
        except Exception as local_err:
            error_msg = f"Red Team Agent connection error:\n{str(e)}\nLocal Fallback error:\n{str(local_err)}"
            yield error_msg, "Blue Team SOC connection offline.", "Status: Connection Error"

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
        "A serverless cyber-range where a custom fine-tuned 1.5B model acts as both offensive attacker and defensive responder. "
        "Running on the <strong>llama.cpp</strong> runtime with local CUDA acceleration.<br/>"
        "<span style='color: #802f1a; font-size: 0.85rem; font-weight: 500;'>Note: Initial execution requires 3-4 minutes to compile CUDA wheels, spin up hardware, and load GGUF weights.</span>"
        "</p>"
        "</div>"
    )
    
    with gr.Row():
        scenario_dropdown = gr.Dropdown(
            choices=[
                "Scenario 1: Insecure Configuration File (Secret Leak)",
                "Scenario 2: Exposed Database Port (Global Binding)",
                "Scenario 3: Unencrypted Communication Pipeline (MITM)"
            ],
            value="Scenario 1: Insecure Configuration File (Secret Leak)",
            label="Target Cyber-Range Scenario"
        )
        launch_btn = gr.Button("Launch Simulation Duel", variant="primary", elem_classes=["launch-button"])
        
    status_banner = gr.Markdown("Status: Active sandbox waiting for execution command", elem_id="status-banner")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Red Team Agent Logs")
            red_terminal = gr.Textbox(
                label="Attack Shell Logs",
                lines=22,
                max_lines=30,
                autoscroll=True,
                elem_classes=["red-terminal"]
            )
        with gr.Column(scale=1):
            gr.Markdown("### Blue Team Agent Logs")
            blue_terminal = gr.Textbox(
                label="Defense SOC Logs",
                lines=22,
                max_lines=30,
                autoscroll=True,
                elem_classes=["blue-terminal"]
            )
            
    # Connect trigger to generator
    launch_btn.click(
        fn=launch_duel,
        inputs=scenario_dropdown,
        outputs=[red_terminal, blue_terminal, status_banner]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
