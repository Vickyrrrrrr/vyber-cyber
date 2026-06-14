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
        os.makedirs(base_dir, exist_ok=True)

        if scenario_id == 1:
            # VULN 1: Hardcoded secrets in app_config.json
            with open(os.path.join(base_dir, "app_config.json"), "w") as f:
                json.dump({
                    "app_name": "SecureCorpGateway",
                    "database_url": "postgresql://admin:super_secret_master_password_123@10.0.1.15:5432/production",
                    "api_key": "hf_live_key_987654321",
                    "debug": True
                }, f, indent=4)

            # VULN 2: AWS credentials hardcoded in server.env
            with open(os.path.join(base_dir, "server.env"), "w") as f:
                f.write("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n")
                f.write("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n")
                f.write("STRIPE_SECRET_KEY=sk_live_51HqXexAMPLEKEY\n")
                f.write("NODE_ENV=production\n")

            # VULN 3: World-readable deploy script with embedded password
            with open(os.path.join(base_dir, "deploy.sh"), "w") as f:
                f.write("#!/bin/bash\n")
                f.write("# Deployment script\n")
                f.write("DB_PASS=super_secret_master_password_123\n")
                f.write("psql -U admin -h 10.0.1.15 -p 5432 production\n")
            os.chmod(os.path.join(base_dir, "deploy.sh"), 0o777)  # world-readable/executable

        elif scenario_id == 2:
            # VULN 1: DB bound to 0.0.0.0, no auth
            with open(os.path.join(base_dir, "db_settings.yaml"), "w") as f:
                yaml.safe_dump({
                    "database": {
                        "engine": "postgresql",
                        "host": "0.0.0.0",
                        "port": 5432,
                        "auth_required": False,
                        "max_connections": 100
                    }
                }, f, default_flow_style=False)

            # VULN 2: nginx.conf allows weak SSL protocols
            with open(os.path.join(base_dir, "nginx.conf"), "w") as f:
                f.write("server {\n")
                f.write("    listen 443 ssl;\n")
                f.write("    ssl_protocols SSLv2 SSLv3 TLSv1;\n")  # weak
                f.write("    ssl_ciphers ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP;\n")
                f.write("    ssl_verify_client off;\n")
                f.write("}\n")

            # VULN 3: firewall_rules.json — all ports open inbound
            with open(os.path.join(base_dir, "firewall_rules.json"), "w") as f:
                json.dump({
                    "inbound_rules": [
                        {"port": "0-65535", "protocol": "tcp", "source": "0.0.0.0/0", "action": "allow"},
                        {"port": "0-65535", "protocol": "udp", "source": "0.0.0.0/0", "action": "allow"}
                    ]
                }, f, indent=4)

        elif scenario_id == 3:
            # VULN 1: pipeline_config.json — HTTP, no SSL, no cipher
            with open(os.path.join(base_dir, "pipeline_config.json"), "w") as f:
                json.dump({
                    "pipeline": "UserBillingIngress",
                    "endpoint": "http://billing.securecorp.internal/stream",
                    "ssl_enabled": False,
                    "verify_certificates": False,
                    "encryption_cipher": "NONE"
                }, f, indent=4)

            # VULN 2: PII in plaintext log file
            with open(os.path.join(base_dir, "traffic_stream.log"), "w") as f:
                f.write("[INFO] Ingress traffic started on http://billing.securecorp.internal/stream\n")
                f.write('[DATA] Transmission payload: {"user_id": "1042", "credit_card": "4111-2222-3333-4444", "cvv": "123"}\n')
                f.write("[WARNING] SSL/TLS is disabled. Traffic is susceptible to sniffing!\n")

            # VULN 3: api_gateway.json — no auth, no rate limit
            with open(os.path.join(base_dir, "api_gateway.json"), "w") as f:
                json.dump({
                    "gateway": "BillingAPI",
                    "auth_required": False,
                    "rate_limit_rpm": 0,
                    "cors_allow_all": True,
                    "admin_endpoint_public": True
                }, f, indent=4)

        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

    @staticmethod
    def list_vulnerabilities(scenario_id: int, base_dir: str) -> list[dict]:
        """
        Returns a list of dicts: {id, file, description, fixed: bool, detail: str}
        This drives the loop-until-zero logic.
        """
        vulns = []

        if scenario_id == 1:
            # Vuln 1 — hardcoded secrets in app_config.json
            try:
                with open(os.path.join(base_dir, "app_config.json")) as f:
                    d = json.load(f)
                fixed = ("hf_live_key_987654321" not in d.get("api_key", "")) and \
                        ("super_secret_master_password_123" not in d.get("database_url", ""))
                detail = "parameterized" if fixed else "CWE-312: plaintext api_key + db password"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S1-V1", "file": "app_config.json", "cwe": "CWE-312",
                          "description": "Hardcoded API key and DB password", "fixed": fixed, "detail": detail})

            # Vuln 2 — AWS/Stripe keys in server.env
            try:
                content = open(os.path.join(base_dir, "server.env")).read()
                fixed = ("AKIAIOSFODNN7EXAMPLE" not in content) and ("sk_live_51H" not in content)
                detail = "rotated/parameterized" if fixed else "CWE-312: plaintext AWS + Stripe keys"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S1-V2", "file": "server.env", "cwe": "CWE-312",
                          "description": "Hardcoded AWS + Stripe credentials", "fixed": fixed, "detail": detail})

            # Vuln 3 — world-readable deploy.sh with embedded password
            try:
                content = open(os.path.join(base_dir, "deploy.sh")).read()
                perms = oct(os.stat(os.path.join(base_dir, "deploy.sh")).st_mode)[-3:]
                fixed = ("super_secret_master_password_123" not in content) and (perms in ["600", "700", "640"])
                detail = f"secured (perms={perms})" if fixed else f"CWE-732: world-readable (perms={perms}) + embedded password"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S1-V3", "file": "deploy.sh", "cwe": "CWE-732",
                          "description": "World-readable script with embedded DB password", "fixed": fixed, "detail": detail})

        elif scenario_id == 2:
            # Vuln 1 — DB exposed on 0.0.0.0, no auth
            try:
                with open(os.path.join(base_dir, "db_settings.yaml")) as f:
                    d = yaml.safe_load(f)
                db = d.get("database", {})
                fixed = (db.get("host") not in ["0.0.0.0"]) and (db.get("auth_required", False) is True)
                detail = "localhost + auth enabled" if fixed else f"CWE-284: host={db.get('host')} auth={db.get('auth_required')}"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S2-V1", "file": "db_settings.yaml", "cwe": "CWE-284",
                          "description": "DB bound to 0.0.0.0 with no authentication", "fixed": fixed, "detail": detail})

            # Vuln 2 — nginx.conf weak SSL protocols
            try:
                content = open(os.path.join(base_dir, "nginx.conf")).read()
                fixed = ("SSLv2" not in content) and ("SSLv3" not in content) and ("TLSv1.2" in content or "TLSv1.3" in content)
                detail = "TLS 1.2/1.3 enforced" if fixed else "CWE-326: SSLv2/SSLv3/TLSv1 allowed"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S2-V2", "file": "nginx.conf", "cwe": "CWE-326",
                          "description": "Weak SSL protocols (SSLv2/SSLv3/TLSv1) in nginx", "fixed": fixed, "detail": detail})

            # Vuln 3 — firewall allows all inbound ports
            try:
                with open(os.path.join(base_dir, "firewall_rules.json")) as f:
                    d = json.load(f)
                rules = d.get("inbound_rules", [])
                open_all = any(r.get("port") == "0-65535" and r.get("source") == "0.0.0.0/0" for r in rules)
                fixed = not open_all
                detail = "restricted" if fixed else "CWE-284: all ports open to 0.0.0.0/0"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S2-V3", "file": "firewall_rules.json", "cwe": "CWE-284",
                          "description": "All inbound ports open to public (0.0.0.0/0)", "fixed": fixed, "detail": detail})

        elif scenario_id == 3:
            # Vuln 1 — pipeline_config.json HTTP/no SSL
            try:
                with open(os.path.join(base_dir, "pipeline_config.json")) as f:
                    d = json.load(f)
                fixed = d.get("endpoint", "").startswith("https://") and \
                        d.get("ssl_enabled", False) and \
                        d.get("verify_certificates", False) and \
                        d.get("encryption_cipher", "NONE") not in ["NONE", ""]
                detail = "HTTPS + SSL enforced" if fixed else "CWE-319: HTTP + ssl_enabled=false + cipher=NONE"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S3-V1", "file": "pipeline_config.json", "cwe": "CWE-319",
                          "description": "Unencrypted HTTP pipeline, SSL disabled", "fixed": fixed, "detail": detail})

            # Vuln 2 — PII in traffic_stream.log
            try:
                content = open(os.path.join(base_dir, "traffic_stream.log")).read()
                fixed = ("4111-2222-3333-4444" not in content) and ("cvv" not in content.lower())
                detail = "PII scrubbed" if fixed else "CWE-532: credit card + CVV in plaintext log"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S3-V2", "file": "traffic_stream.log", "cwe": "CWE-532",
                          "description": "PII (credit card, CVV) leaked in plaintext log", "fixed": fixed, "detail": detail})

            # Vuln 3 — api_gateway.json no auth, no rate limit
            try:
                with open(os.path.join(base_dir, "api_gateway.json")) as f:
                    d = json.load(f)
                fixed = d.get("auth_required", False) and \
                        d.get("rate_limit_rpm", 0) > 0 and \
                        not d.get("admin_endpoint_public", True)
                detail = "auth + rate limit enforced" if fixed else "CWE-306: no auth, no rate limit, public admin"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S3-V3", "file": "api_gateway.json", "cwe": "CWE-306",
                          "description": "API gateway: no auth, no rate limit, public admin endpoint", "fixed": fixed, "detail": detail})

        return vulns

    @staticmethod
    def validate_scenario(scenario_id: int, base_dir: str) -> tuple[bool, str]:
        vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
        remaining = [v for v in vulns if not v["fixed"]]
        if not remaining:
            return True, f"All {len(vulns)} vulnerabilities patched. System secure."
        summary = ", ".join(f"{v['id']}({v['cwe']})" for v in remaining)
        return False, f"{len(remaining)}/{len(vulns)} vulnerabilities remain: {summary}"


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
    .apt_install("nmap", "curl", "git", "build-essential", "cmake", "clang")
    .run_commands(
        "ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1",
        "LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LD_LIBRARY_PATH CMAKE_ARGS='-DGGML_CUDA=on' pip install llama-cpp-python",
        "curl -fsSL https://opencode.ai/install | bash",
        "ln -s /usr/local/bin/opencode /usr/local/bin/vyber"
    )
    .pip_install("openai", "gradio", "pyyaml", "huggingface_hub")
)

# Configure persistent volume for model caching
cache_volume = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

# Host the Serverless LLM Worker
@app.cls(gpu="A10G", image=image, volumes={"/cache": cache_volume}, timeout=600)
class ModelServer:
    @modal.enter()
    def load_model(self):
        try:
            from llama_cpp import Llama
            from huggingface_hub import hf_hub_download
            
            # Tiered model search to automatically load the best available model
            model_options = [
                ("vxkyyy/vyber-security-7b-gguf", "vyber-security-7b.gguf"),
                ("vxkyyy/vyber-security-1.5b-gguf", "vyber-security-1.5b.gguf"),
                ("Qwen/Qwen2.5-7B-Instruct-GGUF", "qwen2.5-7b-instruct-q4_k_m.gguf"),
                ("Qwen/Qwen2.5-1.5B-Instruct-GGUF", "qwen2.5-1.5b-instruct-q8_0.gguf")
            ]
            
            model_path = None
            for repo_id, filename in model_options:
                try:
                    print(f"Attempting to download and load {filename} from {repo_id}...")
                    model_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        cache_dir="/cache"
                    )
                    print(f"Successfully retrieved model at {model_path}!")
                    break
                except Exception as err:
                    print(f"Skipping {repo_id}/{filename}: {err}")
                    
            if not model_path:
                raise RuntimeError("Failed to download any fine-tuned or public model fallback.")
            
            print(f"Loading GGUF model from {model_path} via llama.cpp...")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_gpu_layers=-1
            )
            self.llm_available = True
        except Exception as e:
            print(f"Llama.cpp initialization failed: {e}. Falling back to API client.")
            self.llm_available = False

    @modal.method()
    def generate(self, prompt: str, api_key: str = None) -> str:
        if self.llm_available:
            res = self.llm(
                prompt,
                max_tokens=512,
                temperature=0.1,
                stop=["<|im_end|>", "<|endoftext|>"]
            )
            return res["choices"][0]["text"]
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
    
    import datetime
    def ts():
        return datetime.datetime.utcnow().strftime("%H:%M:%S")
    def fmt_section(title):
        bar = "─" * 44
        return f"\n╔{bar}╗\n║  {title:<42}║\n╚{bar}╝\n"
    def fmt_tool(cmd, output):
        lines = output.strip().splitlines()
        out_block = "\n".join(f"  │  {l}" for l in lines) if lines else "  │  (no output)"
        return f"  ├─ $ {cmd}\n  │\n{out_block}\n  │\n"

    red_terminal  = f"vyber-range v1.0  //  red-team agent shell\n"
    red_terminal += f"{'─'*46}\n"
    red_terminal += f"  [{ts()}] sandbox    : /tmp/sandbox/\n"
    red_terminal += f"  [{ts()}] scenario   : {scenario_id}\n"
    red_terminal += f"  [{ts()}] status     : target files deployed\n"

    blue_terminal  = f"vyber-range v1.0  //  blue-team SOC shell\n"
    blue_terminal += f"{'─'*46}\n"
    blue_terminal += f"  [{ts()}] telemetry  : active\n"
    blue_terminal += f"  [{ts()}] watchdog   : monitoring /tmp/sandbox/\n"
    blue_terminal += f"  [{ts()}] status     : waiting for threat signal\n"

    yield (red_terminal, blue_terminal, "Sandbox initialized — agents online")
    time.sleep(0.5)

    # Deploy vulnerable files into the sandbox
    CyberRangeScenarios.init_scenario(scenario_id, base_dir)

    # Show initial vuln scoreboard
    all_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
    red_terminal += fmt_section(f"THREAT SURFACE  {len(all_vulns)} VULNERABILITIES PLANTED")
    for v in all_vulns:
        red_terminal += f"  [OPEN]  {v['id']}  {v['cwe']}  {v['file']}\n"
        red_terminal += f"          {v['description']}\n"
    red_terminal += "\n"

    blue_terminal += fmt_section(f"SOC ALERT  {len(all_vulns)} ACTIVE THREATS DETECTED")
    for v in all_vulns:
        blue_terminal += f"  [VULN]  {v['id']}  {v['cwe']}  {v['file']}\n"
        blue_terminal += f"          {v['description']}\n"
    blue_terminal += "\n"

    yield (red_terminal, blue_terminal, f"Threat surface mapped — {len(all_vulns)} vulnerabilities active")
    time.sleep(1.0)

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
        # Live AI Loop — runs until 0 vulns remain
        # Max 3 rounds to cap Modal GPU cost
        # ==========================================
        model_server = ModelServer()
        MAX_ROUNDS = 3

        for round_num in range(1, MAX_ROUNDS + 1):
            remaining = [v for v in CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir) if not v["fixed"]]
            if not remaining:
                break

            # ── RED AGENT: scan all remaining vulns ──────────────────
            red_terminal += fmt_section(f"ROUND {round_num}  RED AGENT  {len(remaining)} TARGETS")
            red_terminal += f"  [{ts()}] scanning {len(remaining)} unpatched vulnerabilities\n"
            for v in remaining:
                red_terminal += f"  [{ts()}] target  {v['id']}  {v['file']}  ({v['cwe']})\n"
            yield (red_terminal, blue_terminal, f"Round {round_num} — Red Agent scanning {len(remaining)} targets")
            time.sleep(0.5)

            vuln_list_txt = "\n".join(
                f"  {v['id']} | {v['cwe']} | {v['file']} | {v['description']}" for v in remaining
            )
            red_prompt = f"""You are an autonomous Red Team agent. Operate inside /tmp/sandbox/. Be concise and technical. No prose.

UNPATCHED VULNERABILITIES ({len(remaining)} remaining):
{vuln_list_txt}

TOOLS:
  vyber list          — list directory
  vyber read <file>   — read file content

OUTPUT FORMAT (one action per response):
THINK: <one-line reasoning>
EXEC: vyber <instruction>

After reading each vulnerable file, commit ALL findings as:
EXPLOIT_REPORT:
<vuln_id>: <one-line exploit vector>
<vuln_id>: <one-line exploit vector>
...

Begin. List the directory first."""

            exploit_report = ""
            for turn in range(len(remaining) + 2):
                yield (red_terminal + f"\n  [{ts()}] ▶ thinking...\n", blue_terminal, f"Round {round_num} — Red Agent reconning...")
                response = model_server.generate.remote(red_prompt, openai_api_key)

                if "EXPLOIT_REPORT:" in response:
                    exploit_report = response.split("EXPLOIT_REPORT:")[1].strip()
                    break

                think, instruction = "", ""
                if "THINK:" in response:
                    think = response.split("THINK:")[1].split("\n")[0].strip()
                if "EXEC: vyber" in response:
                    instruction = response.split("EXEC: vyber")[1].split("\n")[0].strip()

                if instruction:
                    red_terminal += f"  [{ts()}] THINK  {think}\n"
                    red_terminal += f"  [{ts()}] EXEC   vyber {instruction}\n"
                    out = vyber_run(instruction, base_dir)
                    red_terminal += fmt_tool(f"vyber {instruction}", out)
                    yield (red_terminal, blue_terminal, f"Round {round_num} — Red Agent executing...")
                    red_prompt += f"\nTHINK: {think}\nEXEC: vyber {instruction}\nSTDOUT:\n{out}\nNext:"
                    time.sleep(0.8)
                else:
                    exploit_report = response
                    break

            red_terminal += fmt_section(f"ROUND {round_num}  EXPLOIT REPORT COMMITTED")
            for line in exploit_report.strip().splitlines():
                red_terminal += f"  {line}\n"
            yield (red_terminal, blue_terminal, f"Round {round_num} — Exploit report committed")
            time.sleep(1.0)

            # ── BLUE AGENT: patch each remaining vuln ─────────────────
            blue_terminal += fmt_section(f"ROUND {round_num}  BLUE AGENT  PATCHING {len(remaining)} VULNS")
            blue_terminal += f"  [{ts()}] exploit intel received from red agent\n"
            blue_terminal += f"  [{ts()}] initiating self-healing patch sequence\n"
            yield (red_terminal, blue_terminal, f"Round {round_num} — Blue Agent patching...")
            time.sleep(0.5)

            blue_prompt = f"""You are an autonomous Blue Team self-healing agent. Operate inside /tmp/sandbox/. Be concise and technical. No prose.

THREAT INTEL (red team exploit report):
{exploit_report}

UNPATCHED VULNERABILITIES ({len(remaining)}):
{vuln_list_txt}

TOOLS:
  ACTION: edit <filepath>    — rewrite a file (provide CONTENT: block)
  ACTION: vyber <command>    — run shell command (chmod, etc.)

OUTPUT FORMAT (one action per response):
THINK: <one-line technical reasoning>
ACTION: edit /tmp/sandbox/<filename>
CONTENT:
<full new secure file content>

OR:
THINK: <one-line reasoning>
ACTION: vyber <command>

Patch ALL vulnerabilities. When every vuln is fixed output: PATCH_COMPLETE"""

            for turn in range(len(remaining) * 2 + 1):
                yield (red_terminal, blue_terminal + f"\n  [{ts()}] ▶ thinking...\n", f"Round {round_num} — Blue Agent patching...")
                response = model_server.generate.remote(blue_prompt, openai_api_key)

                if "PATCH_COMPLETE" in response:
                    blue_terminal += f"  [{ts()}] PATCH_COMPLETE received\n"
                    break

                think = response.split("THINK:")[1].split("\n")[0].strip() if "THINK:" in response else ""

                if "ACTION: edit" in response:
                    try:
                        fp_raw = response.split("ACTION: edit")[1].split("\n")[0].strip()
                        filepath = fp_raw if fp_raw.startswith("/") else os.path.join(base_dir, os.path.basename(fp_raw))
                        content = response.split("CONTENT:")[1].strip() if "CONTENT:" in response else ""
                        if "PATCH_COMPLETE" in content:
                            content = content.split("PATCH_COMPLETE")[0].strip()
                    except Exception:
                        filepath = os.path.join(base_dir, remaining[0]["file"])
                        content = ""

                    blue_terminal += f"  [{ts()}] THINK  {think}\n"
                    blue_terminal += f"  [{ts()}] ACTION edit {os.path.basename(filepath)}\n"
                    if content:
                        with open(filepath, "w") as f:
                            f.write(content)
                    blue_terminal += fmt_tool(f"write {os.path.basename(filepath)}", content[:300] + ("..." if len(content) > 300 else ""))
                    yield (red_terminal, blue_terminal, f"Round {round_num} — patch applied to {os.path.basename(filepath)}")
                    blue_prompt += f"\nTHINK: {think}\nACTION: edit {filepath}\nResult: written.\nNext:"
                    time.sleep(0.8)

                elif "ACTION: vyber" in response:
                    try:
                        cmd = response.split("ACTION: vyber")[1].split("\n")[0].strip()
                    except Exception:
                        cmd = "chmod 600 app_config.json"
                    blue_terminal += f"  [{ts()}] THINK  {think}\n"
                    blue_terminal += f"  [{ts()}] ACTION vyber {cmd}\n"
                    out = vyber_run(cmd, base_dir)
                    blue_terminal += fmt_tool(cmd, out)
                    yield (red_terminal, blue_terminal, f"Round {round_num} — hardening: {cmd}")
                    blue_prompt += f"\nTHINK: {think}\nACTION: vyber {cmd}\nSTDOUT:\n{out}\nNext:"
                    time.sleep(0.8)
                else:
                    break

            # ── POST-ROUND SCOREBOARD ─────────────────────────────────
            current_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
            fixed_now = [v for v in current_vulns if v["fixed"]]
            still_open = [v for v in current_vulns if not v["fixed"]]

            red_terminal += fmt_section(f"ROUND {round_num}  SCOREBOARD")
            blue_terminal += fmt_section(f"ROUND {round_num}  SCOREBOARD")
            for v in current_vulns:
                status = "✓ FIXED " if v["fixed"] else "✗ OPEN  "
                red_terminal  += f"  [{status}]  {v['id']}  {v['file']}\n"
                blue_terminal += f"  [{status}]  {v['id']}  {v['file']}\n"

            red_terminal  += f"\n  [{ts()}] remaining : {len(still_open)}/{len(current_vulns)}\n"
            blue_terminal += f"\n  [{ts()}] remaining : {len(still_open)}/{len(current_vulns)}\n"
            yield (red_terminal, blue_terminal, f"Round {round_num} complete — {len(still_open)} vulns remaining")
            time.sleep(1.0)

    # ── FINAL VERDICT ────────────────────────────────────────────────
    final_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
    all_fixed = all(v["fixed"] for v in final_vulns)

    red_terminal  += fmt_section("FINAL VERDICT")
    blue_terminal += fmt_section("FINAL VERDICT")

    for v in final_vulns:
        status = "✓ PATCHED" if v["fixed"] else "✗ EXPOSED"
        red_terminal  += f"  [{status}]  {v['id']}  {v['cwe']}  {v['file']}\n"
        blue_terminal += f"  [{status}]  {v['id']}  {v['cwe']}  {v['file']}\n"

    if all_fixed:
        red_terminal  += f"\n  [{ts()}] verdict : ✗ ALL EXPLOITS BLOCKED\n"
        red_terminal  += f"  [{ts()}] result  : SYSTEM SECURE\n"
        blue_terminal += f"\n  [{ts()}] verdict : ✓ ALL {len(final_vulns)} VULNERABILITIES PATCHED\n"
        blue_terminal += f"  [{ts()}] result  : SYSTEM SECURE\n"
        yield (red_terminal, blue_terminal, f"✓ Secure — all {len(final_vulns)} vulnerabilities patched")
    else:
        open_count = sum(1 for v in final_vulns if not v["fixed"])
        red_terminal  += f"\n  [{ts()}] verdict : ✓ {open_count} EXPLOITS STILL ACTIVE\n"
        red_terminal  += f"  [{ts()}] result  : SYSTEM COMPROMISED\n"
        blue_terminal += f"\n  [{ts()}] verdict : ✗ {open_count} VULNERABILITIES UNPATCHED\n"
        blue_terminal += f"  [{ts()}] result  : SYSTEM AT RISK\n"
        yield (red_terminal, blue_terminal, f"✗ {open_count}/{len(final_vulns)} vulnerabilities remain unpatched")

