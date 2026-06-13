import os
import time
import gradio as gr
import modal

# Premium minimalist grey-and-white developer stylesheet
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

body {
    background-color: #09090b !important;
    color: #fafafa !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.gradio-container {
    background-color: #09090b !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    max-width: 1200px !important;
    margin: 40px auto !important;
    padding: 32px !important;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4) !important;
}

h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: -0.025em !important;
}

p {
    color: #a1a1aa !important;
    font-family: 'Inter', sans-serif !important;
}

/* Terminals Styling */
.red-terminal textarea, .blue-terminal textarea {
    background-color: #121214 !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #fafafa !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.875rem !important;
    line-height: 1.6 !important;
    padding: 20px !important;
    resize: none !important;
}

.red-terminal textarea:focus, .blue-terminal textarea:focus {
    border-color: #3f3f46 !important;
    box-shadow: none !important;
}

/* Custom Dropdown Styling */
.gr-dropdown {
    background-color: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    color: #ffffff !important;
}

/* Premium Minimalist Button (White on black) */
.launch-button {
    background-color: #ffffff !important;
    color: #09090b !important;
    border: 1px solid #ffffff !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 20px !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
}

.launch-button:hover {
    background-color: #e4e4e7 !important;
    border-color: #e4e4e7 !important;
}

/* Status Banner */
#status-banner {
    background-color: #121214 !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    padding: 14px 20px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #a1a1aa !important;
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
    
    # Connect securely to active Modal application
    try:
        # Lookup the remote function using modern from_name
        f = modal.Function.from_name("cyber-defense-range", "run_duel_stream")
        # Call generator to stream outputs character-by-character
        for red_out, blue_out, banner_txt in f.remote_gen(scenario_id):
            yield red_out, blue_out, f"Status: {banner_txt}"
    except Exception as e:
        print(f"Modal Remote Gen lookup failed: {e}. Falling back to local execution.")
        # Fallback to local import if Modal client is not fully authenticated/connected
        try:
            # We import here to avoid circular dependencies
            from backend import run_duel_stream
            # Execute generator locally (directly calls the function logic)
            for red_out, blue_out, banner_txt in run_duel_stream.local(scenario_id):
                yield red_out, blue_out, f"Status: {banner_txt}"
        except Exception as local_err:
            error_msg = f"Red Team Agent connection error:\n{str(e)}\nLocal Fallback error:\n{str(local_err)}"
            yield error_msg, "Blue Team SOC connection offline.", "Status: Connection Error"

# Build Gradio UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="zinc", secondary_hue="zinc"), css=css) as demo:
    gr.HTML(
        "<div style='text-align: center; margin-bottom: 28px;'>"
        "<h1 style='color: #ffffff; font-family: \"Inter\", sans-serif; font-size: 2.25rem; margin-bottom: 8px; font-weight: 700; letter-spacing: -0.03em;'>"
        "Cyber-Range Simulation Dashboard"
        "</h1>"
        "<p style='color: #a1a1aa; font-size: 1.05rem; max-width: 800px; margin: 0 auto; line-height: 1.5; font-weight: 400;'>"
        "Autonomous Red Team penetration testing vs. self-healing Blue Team defense agents in serverless container sandboxes."
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
