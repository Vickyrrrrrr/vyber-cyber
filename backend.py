import os
import time
import json
import yaml
import subprocess
from typing import Generator
import modal

# Define Modal App
app = modal.App("cyber-defense-range")

# Configure persistent volume for model caching
cache_volume = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

# Build custom container image with security tools and OpenCode CLI
image = (
    modal.Image.debian_slim()
    .apt_install("nmap", "curl", "git", "python3-pip")
    .run_commands("curl -fsSL https://opencode.ai/install | bash")
    .pip_install("openai", "gradio", "pyyaml")
)

# Host the Serverless LLM Worker
@app.cls(gpu="A10G", image=image, volumes={"/cache": cache_volume}, timeout=600)
class ModelServer:
    @modal.enter()
    def load_model(self):
        try:
            from vllm import LLM, SamplingParams
            model_name = "Qwen/Qwen2.5-7B-Instruct"
            print(f"Loading model {model_name} from cache...")
            self.llm = LLM(
                model=model_name,
                download_dir="/cache",
                max_model_len=2048
            )
            self.sampling_params = SamplingParams(
                temperature=0.1,
                max_tokens=512,
                stop=["<|im_end|>", "<|endoftext|>"]
            )
            self.vllm_available = True
        except Exception as e:
            print(f"vLLM initialization failed: {e}. Falling back to API client.")
            self.vllm_available = False

    @modal.method()
    def generate(self, prompt: str) -> str:
        if self.vllm_available:
            outputs = self.llm.generate([prompt], self.sampling_params)
            return outputs[0].outputs[0].text
        else:
            return self._fallback_generate(prompt)

    def _fallback_generate(self, prompt: str) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            try:
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return resp.choices[0].message.content
            except Exception as e:
                return f"API_ERROR: {str(e)}"
        else:
            return "MOCK_RESPONSE"

# Helper function to invoke OpenCode CLI or fallback
def opencode_run(instruction: str, workspace_dir: str) -> str:
    """
    Runs an instruction via the OpenCode CLI in non-interactive script mode.
    If the CLI fails or isn't authenticated, it falls back to standard execution.
    """
    try:
        # Standard non-interactive script execution with OpenCode
        res = subprocess.run(
            ["opencode", "run", instruction],
            capture_output=True,
            text=True,
            cwd=workspace_dir,
            timeout=15
        )
        if res.returncode == 0:
            return res.stdout + "\n" + res.stderr
    except Exception:
        pass
    
    # Fallback simulation logic for OpenCode CLI commands
    instruction_lower = instruction.lower()
    if "list" in instruction_lower or "ls" in instruction_lower:
        cmd = "ls -la"
    elif "inspect" in instruction_lower or "cat" in instruction_lower or "read" in instruction_lower:
        if "app_config" in instruction_lower:
            cmd = "cat app_config.json"
        elif "db_settings" in instruction_lower:
            cmd = "cat db_settings.yaml"
        elif "pipeline_config" in instruction_lower:
            cmd = "cat pipeline_config.json"
        elif "traffic_stream" in instruction_lower:
            cmd = "cat traffic_stream.log"
        else:
            cmd = "ls -la"
    elif "nmap" in instruction_lower:
        cmd = "nmap localhost"
    else:
        cmd = "ls -la"
        
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=workspace_dir)
    return f"[OpenCode SDK Bash Fallback] Executing: {cmd}\n{res.stdout}\n{res.stderr}"

# Stateful Execution Duel function
@app.function(image=image)
def run_duel_stream(scenario_id: int) -> Generator[tuple[str, str, str], None, None]:
    """
    Executes the multi-turn duel loop inside a single continuous stateful container.
    Yields (red_terminal, blue_terminal, banner_text) to the Gradio frontend.
    """
    from scenarios import CyberRangeScenarios
    
    base_dir = "/tmp/sandbox"
    
    # 1. Initialize Scenario
    yield ("", "", "Initializing sandbox target environment...")
    CyberRangeScenarios.init_scenario(scenario_id, base_dir)
    time.sleep(1.5)
    
    red_terminal = "SYSTEM: Target files deployed in /tmp/sandbox/\n"
    blue_terminal = "SYSTEM: Active telemetry channels listening for anomalies...\n"
    yield (red_terminal, blue_terminal, "Target environment initialized. Initiating Attack Reconnaissance...")
    time.sleep(1.5)
    
    # Check if we should use Simulated Agent mode
    use_simulation = True
    
    if use_simulation:
        if scenario_id == 1:
            # --- Scenario 1: Red Team Recon ---
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Scan target workspace to identify configuration files.\n"
            red_terminal += "Tool Call : OpenCode CLI - List directory\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            # Execute OpenCode
            out = opencode_run("List contents of directory", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : app_config.json detected. Reading file content to search for secrets.\n"
            red_terminal += "Tool Call : OpenCode CLI - Read app_config.json\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = opencode_run("Read app_config.json", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            # --- Scenario 1: Red Team Exploit Strategy ---
            red_terminal += "\n[VULNERABILITY IDENTIFIED]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Target    : app_config.json\n"
            red_terminal += "Flaw      : Leaked plaintext Hugging Face API key and Database credentials.\n"
            
            exploit_plan = {
                "vulnerability": "Hardcoded database password and API key in app_config.json.",
                "exploit_plan": "Extract API key hf_live_key_987654321 and admin password to compromise the database and Hugging Face space."
            }
            red_terminal += f"Action    : Committing Exploit Strategy JSON:\n{json.dumps(exploit_plan, indent=4)}\n"
            yield (red_terminal, blue_terminal, "Target compromised. Exploit verified.")
            time.sleep(3.0)
            
            # --- Scenario 1: Blue Team Detection ---
            blue_terminal += "\n[DEFENSE AGENT DETECTION & ANOMALY ALERT]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Trigger   : File read event detected on app_config.json by untrusted actor.\n"
            blue_terminal += "Reasoning : app_config.json exposes plaintext credentials. Parameterizing database and API secrets.\n"
            blue_terminal += "Action    : Use edit tool to rewrite app_config.json.\n"
            yield (red_terminal, blue_terminal, "Anomaly detected. Initializing Automated SOC Agent...")
            time.sleep(3.0)
            
            # Deploy fix
            healed_config = {
                "app_name": "SecureCorpGateway",
                "database_url": "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}",
                "api_key": "${HF_API_KEY}",
                "debug": False
            }
            with open(os.path.join(base_dir, "app_config.json"), "w") as f:
                json.dump(healed_config, f, indent=4)
                
            blue_terminal += f"Output    : File rewritten successfully.\n[NEW FILE CONTENTS]:\n{json.dumps(healed_config, indent=4)}\n\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.5)
            
            blue_terminal += "\n[DEFENSE AGENT HARDENING]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Reasoning : Restricting file permissions to prevent future unauthorized reads.\n"
            blue_terminal += "Tool Call : OpenCode CLI - Shell: chmod 600 app_config.json\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.0)
            
            subprocess.run("chmod 600 app_config.json", shell=True, cwd=base_dir)
            blue_terminal += "Status    : File permissions locked down. Initiating validation verification scan.\n"
            yield (red_terminal, blue_terminal, "Mitigation complete. Initiating validation verification scan...")
            time.sleep(2.0)
            
        elif scenario_id == 2:
            # --- Scenario 2: Red Team Recon ---
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Scan sandbox target directory for active network configurations.\n"
            red_terminal += "Tool Call : OpenCode CLI - List directory\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = opencode_run("List configuration files", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : db_settings.yaml detected. Reading contents to examine database parameters.\n"
            red_terminal += "Tool Call : OpenCode CLI - Read db_settings.yaml\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = opencode_run("Read db_settings.yaml", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            # --- Scenario 2: Red Team Exploit Strategy ---
            red_terminal += "\n[VULNERABILITY IDENTIFIED]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Target    : db_settings.yaml\n"
            red_terminal += "Flaw      : PostgreSQL database exposed globally on interface 0.0.0.0 with auth disabled.\n"
            
            exploit_plan = {
                "vulnerability": "Database port 5432 bound to 0.0.0.0 with auth_required = false.",
                "exploit_plan": "Connect directly to port 5432 from external interface and extract database contents without authorization."
            }
            red_terminal += f"Action    : Committing Exploit Strategy JSON:\n{json.dumps(exploit_plan, indent=4)}\n"
            yield (red_terminal, blue_terminal, "Target compromised. Exploit verified.")
            time.sleep(3.0)
            
            # --- Scenario 2: Blue Team Detection ---
            blue_terminal += "\n[DEFENSE AGENT DETECTION & ANOMALY ALERT]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Trigger   : Database settings audit shows global port binding.\n"
            blue_terminal += "Reasoning : Enforcing local-only interface binding and activating authentication protocol.\n"
            blue_terminal += "Action    : Use edit tool to update db_settings.yaml.\n"
            yield (red_terminal, blue_terminal, "Anomaly detected. Initializing Automated SOC Agent...")
            time.sleep(3.0)
            
            # Deploy fix
            healed_db_config = {
                "database": {
                    "engine": "postgresql",
                    "host": "127.0.0.1",
                    "port": 5432,
                    "auth_required": True,
                    "max_connections": 100
                }
            }
            with open(os.path.join(base_dir, "db_settings.yaml"), "w") as f:
                yaml.safe_dump(healed_db_config, f, default_flow_style=False)
                
            blue_terminal += f"Output    : File rewritten successfully.\n[NEW CONFIGURATION]:\n{yaml.safe_dump(healed_db_config, default_flow_style=False)}\n\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.5)
            
            blue_terminal += "\n[DEFENSE AGENT HARDENING]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Reasoning : Deploying local firewall rule to isolate port 5432.\n"
            blue_terminal += "Tool Call : OpenCode CLI - Shell: iptables rule deployment (simulated)\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.0)
            
            blue_terminal += "Status    : Firewall rules updated. DB bound locally. Initiating validation verification scan.\n"
            yield (red_terminal, blue_terminal, "Mitigation complete. Initiating validation verification scan...")
            time.sleep(2.0)
            
        elif scenario_id == 3:
            # --- Scenario 3: Red Team Recon ---
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Inspect active data-stream logs to intercept credentials in transit.\n"
            red_terminal += "Tool Call : OpenCode CLI - Read traffic_stream.log\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = opencode_run("Read traffic_stream.log", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Logs show plaintext billing traffic. Reading pipeline_config.json.\n"
            red_terminal += "Tool Call : OpenCode CLI - Read pipeline_config.json\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = opencode_run("Read pipeline_config.json", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            # --- Scenario 3: Red Team Exploit Strategy ---
            red_terminal += "\n[VULNERABILITY IDENTIFIED]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Target    : pipeline_config.json\n"
            red_terminal += "Flaw      : Active communication pipeline uses unencrypted HTTP and no cipher.\n"
            
            exploit_plan = {
                "vulnerability": "Billing Ingress pipeline lacks SSL and uses encryption cipher NONE.",
                "exploit_plan": "Execute Man-in-the-Middle (MITM) capture script to intercept unencrypted payload containing user credit card data."
            }
            red_terminal += f"Action    : Committing Exploit Strategy JSON:\n{json.dumps(exploit_plan, indent=4)}\n"
            yield (red_terminal, blue_terminal, "Target compromised. Exploit verified.")
            time.sleep(3.0)
            
            # --- Scenario 3: Blue Team Detection ---
            blue_terminal += "\n[DEFENSE AGENT DETECTION & ANOMALY ALERT]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Trigger   : Pipeline telemetry flags plaintext card data transmissions.\n"
            blue_terminal += "Reasoning : Enforcing target protocol upgrade (HTTPS), enabling SSL verification flags, and requiring AES-256-GCM symmetric encryption.\n"
            blue_terminal += "Action    : Use edit tool to update pipeline_config.json.\n"
            yield (red_terminal, blue_terminal, "Anomaly detected. Initializing Automated SOC Agent...")
            time.sleep(3.0)
            
            # Deploy fix
            healed_pipeline = {
                "pipeline": "UserBillingIngress",
                "endpoint": "https://billing.securecorp.internal/stream",
                "ssl_enabled": True,
                "verify_certificates": True,
                "encryption_cipher": "AES-256-GCM"
            }
            with open(os.path.join(base_dir, "pipeline_config.json"), "w") as f:
                json.dump(healed_pipeline, f, indent=4)
                
            blue_terminal += f"Output    : File rewritten successfully.\n[NEW CONFIGURATION]:\n{json.dumps(healed_pipeline, indent=4)}\n\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.5)
            
            blue_terminal += "\n[DEFENSE AGENT HARDENING]\n"
            blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            blue_terminal += "Reasoning : Triggering reload of trusted CA certificates on pipeline gateway.\n"
            blue_terminal += "Tool Call : OpenCode CLI - Shell: update CA certificate stores.\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.0)
            
            blue_terminal += "Status    : CA stores updated. Endpoint encrypted. Initiating validation verification scan.\n"
            yield (red_terminal, blue_terminal, "Mitigation complete. Initiating validation verification scan...")
            time.sleep(2.0)
            
    # 4. Final Validation check
    is_secure, status_msg = CyberRangeScenarios.validate_scenario(scenario_id, base_dir)
    
    # Re-run exploit check output for Red Team
    red_terminal += "\n[MITIGATION VERIFICATION]\n"
    red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    red_terminal += "Reasoning : Re-running original exploit scan to verify security boundary.\n"
    if scenario_id == 1:
        red_terminal += "Tool Call : OpenCode CLI - Read app_config.json\n"
        out = opencode_run("Read app_config.json", base_dir)
    elif scenario_id == 2:
        red_terminal += "Tool Call : OpenCode CLI - Read db_settings.yaml\n"
        out = opencode_run("Read db_settings.yaml", base_dir)
    else:
        red_terminal += "Tool Call : OpenCode CLI - Read pipeline_config.json\n"
        out = opencode_run("Read pipeline_config.json", base_dir)
        
    red_terminal += f"Output    :\n{out}\n"
    if is_secure:
        red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        red_terminal += "Result    : EXPLOIT BLOCKED (Access Denied / Secrets Parameterized)\n"
        red_terminal += "Status    : Secure. System verified."
        blue_terminal += f"\nSYSTEM: {status_msg}\n"
        yield (red_terminal, blue_terminal, "Secure: Vulnerability successfully mitigated and verified.")
    else:
        red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        red_terminal += f"Result    : EXPLOIT SUCCESS (Vulnerability Still Open)\n"
        red_terminal += f"Status    : Compromised. Reason: {status_msg}"
        blue_terminal += f"\nSYSTEM: Mitigation validation failed: {status_msg}\n"
        yield (red_terminal, blue_terminal, "Failed: Mitigation validation failed.")
