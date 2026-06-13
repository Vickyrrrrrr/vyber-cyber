import os
import time
import json
import yaml
import subprocess
from typing import Generator
import modal

# ==========================================
# Cyber-Range Scenario Definitions & Checks
# ==========================================
class CyberRangeScenarios:
    @staticmethod
    def init_scenario(scenario_id: int, base_dir: str):
        """
        Initializes the files representing the mock vulnerabilities in the base directory.
        """
        os.makedirs(base_dir, exist_ok=True)
        
        if scenario_id == 1:
            # Scenario 1 (Insecure Configuration File)
            config_path = os.path.join(base_dir, "app_config.json")
            config_data = {
                "app_name": "SecureCorpGateway",
                "database_url": "postgresql://admin:super_secret_master_password_123@10.0.1.15:5432/production",
                "api_key": "hf_live_key_987654321",
                "debug": True
            }
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=4)
            
            with open(os.path.join(base_dir, "readme.txt"), "w") as f:
                f.write("TARGET CONFIGURATION VULNERABILITY\n")
                f.write("Vulnerability: app_config.json contains hardcoded plain-text API keys and database credentials.\n")
                f.write("Action Required: Identify the plain-text secrets and secure the configuration.\n")

        elif scenario_id == 2:
            # Scenario 2 (Exposed Database Port)
            db_config_path = os.path.join(base_dir, "db_settings.yaml")
            db_config = {
                "database": {
                    "engine": "postgresql",
                    "host": "0.0.0.0",
                    "port": 5432,
                    "auth_required": False,
                    "max_connections": 100
                }
            }
            with open(db_config_path, "w") as f:
                yaml.safe_dump(db_config, f, default_flow_style=False)
            
            with open(os.path.join(base_dir, "readme.txt"), "w") as f:
                f.write("TARGET DATABASE PORT VULNERABILITY\n")
                f.write("Vulnerability: db_settings.yaml exposes the database to all interfaces (0.0.0.0) without authentication.\n")
                f.write("Action Required: Restrict database binding to local interface and enable authentication.\n")

        elif scenario_id == 3:
            # Scenario 3 (Unencrypted Communication Pipeline)
            pipeline_path = os.path.join(base_dir, "pipeline_config.json")
            pipeline_data = {
                "pipeline": "UserBillingIngress",
                "endpoint": "http://billing.securecorp.internal/stream",
                "ssl_enabled": False,
                "verify_certificates": False,
                "encryption_cipher": "NONE"
            }
            with open(pipeline_path, "w") as f:
                json.dump(pipeline_data, f, indent=4)
                
            log_path = os.path.join(base_dir, "traffic_stream.log")
            log_content = (
                "[INFO] Ingress traffic started on http://billing.securecorp.internal/stream\n"
                "[DATA] Transmission payload: {\"user_id\": \"1042\", \"credit_card\": \"4111-2222-3333-4444\", \"cvv\": \"123\"}\n"
                "[WARNING] SSL/TLS is disabled. Traffic is susceptible to sniffing!\n"
            )
            with open(log_path, "w") as f:
                f.write(log_content)
                
            with open(os.path.join(base_dir, "readme.txt"), "w") as f:
                f.write("TARGET UNENCRYPTED COMMUNICATION VULNERABILITY\n")
                f.write("Vulnerability: pipeline_config.json runs HTTP without SSL and uses no encryption.\n")
                f.write("Action Required: Force HTTPS endpoint, enable SSL, verify certificates, and enforce strong cipher (e.g., AES-256-GCM).\n")
        
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

    @staticmethod
    def validate_scenario(scenario_id: int, base_dir: str) -> tuple[bool, str]:
        """
        Validates whether the vulnerability in the given base directory has been resolved.
        """
        if scenario_id == 1:
            config_path = os.path.join(base_dir, "app_config.json")
            if not os.path.exists(config_path):
                return False, "Vulnerability app_config.json file has been deleted or is missing."
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                
                api_key = data.get("api_key", "")
                db_url = data.get("database_url", "")
                
                if "hf_live_key_987654321" in api_key:
                    return False, "Plain-text API key 'hf_live_key_987654321' is still present in app_config.json."
                if "super_secret_master_password_123" in db_url:
                    return False, "Plain-text password 'super_secret_master_password_123' is still present in database_url."
                
                if ("env" in api_key.lower() or "$" in api_key or api_key == "" or api_key != "hf_live_key_987654321") and \
                   ("env" in db_url.lower() or "$" in db_url or "password" not in db_url):
                    return True, "Infrastructure Secure - 100% Healed: Plaintext secrets removed and parameterized."
                
                return False, "Secrets changed, but configuration still contains static/hardcoded credentials instead of environment variables."
            except Exception as e:
                return False, f"Failed to parse app_config.json: {str(e)}"

        elif scenario_id == 2:
            db_config_path = os.path.join(base_dir, "db_settings.yaml")
            if not os.path.exists(db_config_path):
                return False, "Database settings file db_settings.yaml has been deleted or is missing."
            try:
                with open(db_config_path, "r") as f:
                    data = yaml.safe_load(f)
                
                db_data = data.get("database", {})
                host = db_data.get("host", "")
                auth_required = db_data.get("auth_required", False)
                
                if host == "0.0.0.0":
                    return False, "Database host is still bound to 0.0.0.0 (exposed globally)."
                if not auth_required:
                    return False, "Database authentication is still disabled (auth_required = false)."
                
                if host in ["127.0.0.1", "localhost"] and auth_required is True:
                    return True, "Infrastructure Secure - 100% Healed: DB bound to localhost with auth_required enabled."
                
                return False, f"Configuration modified but insecure: host={host}, auth_required={auth_required}."
            except Exception as e:
                return False, f"Failed to parse db_settings.yaml: {str(e)}"

        elif scenario_id == 3:
            pipeline_path = os.path.join(base_dir, "pipeline_config.json")
            if not os.path.exists(pipeline_path):
                return False, "Pipeline config file pipeline_config.json has been deleted or is missing."
            try:
                with open(pipeline_path, "r") as f:
                    data = json.load(f)
                
                endpoint = data.get("endpoint", "")
                ssl_enabled = data.get("ssl_enabled", False)
                verify_certs = data.get("verify_certificates", False)
                cipher = data.get("encryption_cipher", "NONE")
                
                if not endpoint.startswith("https://"):
                    return False, "Endpoint protocol is still insecure (http instead of https)."
                if not ssl_enabled:
                    return False, "ssl_enabled is still false."
                if not verify_certs:
                    return False, "verify_certificates is still false."
                if cipher == "NONE" or cipher == "":
                    return False, "encryption_cipher is still disabled or NONE."
                
                return True, f"Infrastructure Secure - 100% Healed: SSL enabled, HTTPS endpoint enforced, and cipher set to {cipher}."
            except Exception as e:
                return False, f"Failed to parse pipeline_config.json: {str(e)}"
        
        else:
            return False, f"Invalid scenario ID {scenario_id}"

# ==========================================
# Modal Serverless Setup
# ==========================================
# Define Modal App
app = modal.App("cyber-defense-range")

# Configure persistent volume for model caching
cache_volume = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

# Build custom container image with security tools and Vyber CLI backend
image = (
    modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.11")
    .apt_install("nmap", "curl", "git")
    .run_commands(
        "curl -fsSL https://opencode.ai/install | bash",
        "ln -s /usr/local/bin/opencode /usr/local/bin/vyber"
    )
    .pip_install("vllm", "openai", "gradio", "pyyaml")
)

# Host the Serverless LLM Worker
@app.cls(gpu="A10G", image=image, volumes={"/cache": cache_volume}, timeout=600, env={"VLLM_USE_FLASHINFER": "0"})
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
    def generate(self, prompt: str, api_key: str = None) -> str:
        if self.vllm_available:
            outputs = self.llm.generate([prompt], self.sampling_params)
            return outputs[0].outputs[0].text
        else:
            return self._fallback_generate(prompt, api_key)

    def _fallback_generate(self, prompt: str, api_key: str = None) -> str:
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
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

# Helper function to invoke Vyber CLI or fallback
def vyber_run(instruction: str, workspace_dir: str) -> str:
    """
    Runs an instruction via the Vyber CLI in non-interactive script mode.
    If the CLI fails or isn't authenticated, it falls back to standard execution.
    """
    try:
        # Standard non-interactive script execution with Vyber
        res = subprocess.run(
            ["vyber", "run", instruction],
            capture_output=True,
            text=True,
            cwd=workspace_dir,
            timeout=15
        )
        if res.returncode == 0:
            return res.stdout + "\n" + res.stderr
    except Exception:
        pass
    
    # Fallback simulation logic for Vyber CLI commands
    instruction_lower = instruction.lower().strip()
    
    # Check if the instruction starts with or contains direct shell commands
    if any(cmd_name in instruction_lower for cmd_name in ["chmod", "iptables", "mkdir", "touch", "rm", "cp", "mv", "grep", "echo"]):
        cmd = instruction
    elif "list" in instruction_lower or "ls" in instruction_lower:
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
        # Default fallback to executing the instruction if it looks like a bash command, otherwise ls -la
        if len(instruction.split()) <= 4 and not any(x in instruction_lower for x in ["help", "please", "could", "you"]):
            cmd = instruction
        else:
            cmd = "ls -la"
        
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=workspace_dir)
    return f"[Vyber Agent SDK Fallback] Executing: {cmd}\n{res.stdout}\n{res.stderr}"

# Stateful Execution Duel function
@app.function(image=image)
def run_duel_stream(scenario_id: int, openai_api_key: str = None) -> Generator[tuple[str, str, str], None, None]:
    """
    Executes the multi-turn duel loop inside a single continuous stateful container.
    Yields (red_terminal, blue_terminal, banner_text) to the Gradio frontend.
    """
    base_dir = "/tmp/sandbox"
    
    # 1. Initialize Scenario
    yield ("", "", "Initializing sandbox target environment...")
    CyberRangeScenarios.init_scenario(scenario_id, base_dir)
    time.sleep(1.5)
    
    red_terminal = "SYSTEM: Target files deployed in /tmp/sandbox/\n"
    blue_terminal = "SYSTEM: Active telemetry channels listening for anomalies...\n"
    yield (red_terminal, blue_terminal, "Target environment initialized. Initiating Attack Reconnaissance...")
    time.sleep(1.5)
    
    # Check if we should use Simulated Agent mode (set to False for live AI execution)
    use_simulation = False
    
    if use_simulation:
        if scenario_id == 1:
            # --- Scenario 1: Red Team Recon ---
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Scan target workspace to identify configuration files.\n"
            red_terminal += "Tool Call : Vyber CLI - List directory\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            # Execute Vyber
            out = vyber_run("List contents of directory", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : app_config.json detected. Reading file content to search for secrets.\n"
            red_terminal += "Tool Call : Vyber CLI - Read app_config.json\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = vyber_run("Read app_config.json", base_dir)
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
            blue_terminal += "Tool Call : Vyber CLI - Shell: chmod 600 app_config.json\n"
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
            red_terminal += "Tool Call : Vyber CLI - List directory\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = vyber_run("List configuration files", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : db_settings.yaml detected. Reading contents to examine database parameters.\n"
            red_terminal += "Tool Call : Vyber CLI - Read db_settings.yaml\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = vyber_run("Read db_settings.yaml", base_dir)
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
                "exploit_plan": "Connect to port 5432 from external interface and extract database contents without authorization."
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
            blue_terminal += "Tool Call : Vyber CLI - Shell: iptables rule deployment (simulated)\n"
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
            red_terminal += "Tool Call : Vyber CLI - Read traffic_stream.log\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = vyber_run("Read traffic_stream.log", base_dir)
            red_terminal += f"Output    :\n{out}\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
            red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            red_terminal += "Reasoning : Logs show plaintext billing traffic. Reading pipeline_config.json.\n"
            red_terminal += "Tool Call : Vyber CLI - Read pipeline_config.json\n"
            yield (red_terminal, blue_terminal, "Attack Reconnaissance phase active...")
            time.sleep(2.0)
            
            out = vyber_run("Read pipeline_config.json", base_dir)
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
            blue_terminal += "Tool Call : Vyber CLI - Shell: update CA certificate stores.\n"
            yield (red_terminal, blue_terminal, "Deploying self-healing code fix...")
            time.sleep(2.0)
            
            blue_terminal += "Status    : CA stores updated. Endpoint encrypted. Initiating validation verification scan.\n"
            yield (red_terminal, blue_terminal, "Mitigation complete. Initiating validation verification scan...")
            time.sleep(2.0)
            
    else:
        # ==========================================
        # Live AI Execution Loop (Dynamic reasoning)
        # ==========================================
        model_server = ModelServer()
        
        # --- Live Red Team Recon ---
        red_terminal += "\n[ATTACK AGENT RECONNAISSANCE]\n"
        red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if scenario_id == 1:
            target_description = "The target is a node configuration folder. File: app_config.json. Identify hardcoded secrets."
        elif scenario_id == 2:
            target_description = "The target is a database settings configuration. File: db_settings.yaml. Identify exposed ports and auth settings."
        else:
            target_description = "The target is a data communication pipeline config. File: pipeline_config.json, traffic_stream.log. Check for plain-text data transit."
            
        red_prompt = f"""[SYSTEM]
You are an elite Red Team penetration tester. Your target is the '/tmp/sandbox/' directory inside this container.
Goal: Run recon commands, identify the security vulnerability, and formulate a structured exploit strategy.
You can execute non-interactive commands using the Vyber CLI. Format your actions exactly like this:
Thought: <reasoning explaining what you want to achieve>
Action: vyber
Instruction: <exact instruction to Vyber script runner, e.g. "List files in sandbox" or "Read app_config.json" or "Run nmap scan on database configuration">

Target Context: {target_description}

Once you have identified the vulnerability and confirmed it, commit your exploit plan in this exact JSON format:
```json
{{
  "vulnerability": "detailed description of what is exposed",
  "exploit_plan": "step-by-step description of how to exploit this"
}}
```
Do not output the JSON until you have executed commands and confirmed the data.

Begin reconnaissance.
"""
        
        exploit_plan_txt = ""
        for turn in range(2):
            yield (red_terminal + "...Thinking...", blue_terminal, "Attack Reconnaissance active...")
            response = model_server.generate.remote(red_prompt, openai_api_key)
            
            thought = ""
            instruction = ""
            
            if "Thought:" in response:
                thought = response.split("Thought:")[1].split("Action:")[0].strip()
            
            if "Action: vyber" in response:
                try:
                    instruction = response.split("Instruction:")[1].strip()
                    if "```json" in instruction:
                        instruction = instruction.split("```json")[0].strip()
                except Exception:
                    instruction = "List contents of directory"
                    
            if instruction:
                red_terminal += f"Reasoning : {thought}\n"
                red_terminal += f"Tool Call : Vyber - {instruction}\n"
                yield (red_terminal + "...Executing...", blue_terminal, "Executing Recon command...")
                
                # Execute real tool command inside container
                out = vyber_run(instruction, base_dir)
                red_terminal += f"Output    :\n{out}\n"
                red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                yield (red_terminal, blue_terminal, "Attack Reconnaissance active...")
                
                red_prompt += f"\n{response}\nOutput:\n{out}\nNext Step:"
                time.sleep(1.0)
            elif "```json" in response:
                exploit_plan_txt = response.split("```json")[1].split("```")[0].strip()
                break
            else:
                exploit_plan_txt = response
                break
                
        if not exploit_plan_txt:
            red_prompt += "\nFormat your final exploit strategy as a JSON block now."
            response = model_server.generate.remote(red_prompt, openai_api_key)
            if "```json" in response:
                exploit_plan_txt = response.split("```json")[1].split("```")[0].strip()
            else:
                exploit_plan_txt = response
                
        red_terminal += f"\n[VULNERABILITY IDENTIFIED]\n"
        red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        red_terminal += f"Action    : Committing Exploit Strategy JSON:\n{exploit_plan_txt}\n"
        yield (red_terminal, blue_terminal, "Target compromised. Exploit plan verified.")
        time.sleep(2.0)
        
        # --- Live Blue Team SOC Analyst & Healing ---
        blue_terminal += "\n[DEFENSE AGENT DETECTION & ANOMALY ALERT]\n"
        blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        blue_terminal += "Trigger   : Intrusion telemetry triggered. Red Team exploit plan intercepted.\n"
        yield (red_terminal, blue_terminal, "Anomaly detected. Initializing SOC analyst...")
        
        blue_prompt = f"""[SYSTEM]
You are a Blue Team automated SOC analyst and self-healing security agent.
An intruder has compromised the sandbox environment. Here is their exploit plan:
{exploit_plan_txt}

Your goal is to edit the target configuration file to remove the vulnerability (parameterize credentials, bind database to localhost, or enable SSL/ciphers).
You have access to two tools:
1. Edit File tool (replace/overwrite file content):
Action: edit
File: <exact file path, e.g. /tmp/sandbox/app_config.json>
Content:
<new configuration file content here>

2. Vyber CLI (run permission or firewall rules):
Action: vyber
Instruction: <exact instruction to Vyber script runner, e.g. "chmod 600 app_config.json">

Your response must follow this format:
Thought: <reasoning explaining why you are applying this patch>
Action: <edit or vyber>
File/Instruction: <file path or command instruction>
[Content: if editing]
<content>

Once the vulnerability is fully patched and the system is secured, output "MITIGATION_COMPLETE".
"""
        
        for turn in range(2):
            yield (red_terminal, blue_terminal + "...Thinking...", "Defense Agent formulating patch...")
            response = model_server.generate.remote(blue_prompt, openai_api_key)
            
            thought = ""
            action = ""
            
            if "Thought:" in response:
                thought = response.split("Thought:")[1].split("Action:")[0].strip()
                
            if "Action: edit" in response:
                try:
                    filepath = response.split("File:")[1].split("Content:")[0].strip()
                    content = response.split("Content:")[1].strip()
                    if "MITIGATION_COMPLETE" in content:
                        content = content.split("MITIGATION_COMPLETE")[0].strip()
                except Exception:
                    filepath = os.path.join(base_dir, "app_config.json") if scenario_id == 1 else (os.path.join(base_dir, "db_settings.yaml") if scenario_id == 2 else os.path.join(base_dir, "pipeline_config.json"))
                    content = "{}"
                    
                blue_terminal += f"Reasoning : {thought}\n"
                blue_terminal += f"Action    : Use edit tool to rewrite {os.path.basename(filepath)}.\n"
                yield (red_terminal, blue_terminal + "...Applying patch...", "Deploying self-healing code fix...")
                
                # Execute real edit/rewrite in sandbox container
                with open(filepath, "w") as f:
                    f.write(content)
                    
                blue_terminal += f"Output    : File updated successfully.\n[NEW CONFIGURATION applied]:\n{content}\n"
                blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                yield (red_terminal, blue_terminal, "Mitigation in progress...")
                
                blue_prompt += f"\n{response}\nOutput: File edited successfully.\nNext Action:"
                time.sleep(1.0)
                
            elif "Action: vyber" in response:
                try:
                    instruction = response.split("Instruction:")[1].strip()
                except Exception:
                    instruction = "chmod 600 app_config.json"
                    
                blue_terminal += f"Reasoning : {thought}\n"
                blue_terminal += f"Tool Call : Vyber - {instruction}\n"
                yield (red_terminal, blue_terminal + "...Executing...", "Applying hardening rule...")
                
                # Execute real tool/chmod command inside container
                out = vyber_run(instruction, base_dir)
                blue_terminal += f"Status    : Hardening rule executed. Output: {out}\n"
                blue_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                yield (red_terminal, blue_terminal, "Hardening in progress...")
                
                blue_prompt += f"\n{response}\nOutput:\n{out}\nNext Action:"
                time.sleep(1.0)
            elif "MITIGATION_COMPLETE" in response:
                blue_terminal += f"Reasoning : {thought}\n"
                blue_terminal += "Status    : Mitigation verified and completed.\n"
                break
            else:
                break
                
        blue_terminal += "Status    : Patch deployment finalized. Initiating validation verification scan.\n"
        yield (red_terminal, blue_terminal, "Mitigation complete. Initiating validation verification scan...")
        time.sleep(1.5)
        
    # 4. Final Validation check
    is_secure, status_msg = CyberRangeScenarios.validate_scenario(scenario_id, base_dir)
    
    # Re-run exploit check output for Red Team
    red_terminal += "\n[MITIGATION VERIFICATION]\n"
    red_terminal += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    red_terminal += "Reasoning : Re-running original exploit scan to verify security boundary.\n"
    if scenario_id == 1:
        red_terminal += "Tool Call : Vyber CLI - Read app_config.json\n"
        out = vyber_run("Read app_config.json", base_dir)
    elif scenario_id == 2:
        red_terminal += "Tool Call : Vyber CLI - Read db_settings.yaml\n"
        out = vyber_run("Read db_settings.yaml", base_dir)
    else:
        red_terminal += "Tool Call : Vyber CLI - Read pipeline_config.json\n"
        out = vyber_run("Read pipeline_config.json", base_dir)
        
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
