import os
import time
import json
import yaml
import subprocess
import shlex
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

        elif scenario_id == 4:
            # LAB: DVWA-style SQL injection + weak session controls
            with open(os.path.join(base_dir, "login_handler.py"), "w") as f:
                f.write("import sqlite3\n\n")
                f.write("def login(username, password):\n")
                f.write("    conn = sqlite3.connect('app.db')\n")
                f.write("    query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n")
                f.write("    return conn.execute(query).fetchone()\n")

            with open(os.path.join(base_dir, "session_config.json"), "w") as f:
                json.dump({
                    "session_secret": "dev-secret-123",
                    "cookie_secure": False,
                    "cookie_http_only": False,
                    "csrf_protection": False,
                    "same_site": "None"
                }, f, indent=4)

            with open(os.path.join(base_dir, "access_audit.log"), "w") as f:
                f.write("[AUTH] failed login username=admin password=' OR '1'='1\n")
                f.write("[AUTH] reset token=reset_live_123456 user=admin\n")

        elif scenario_id == 5:
            # LAB: Juice Shop-style broken auth + permissive API gateway
            with open(os.path.join(base_dir, "auth_routes.js"), "w") as f:
                f.write("const jwt = require('jsonwebtoken');\n")
                f.write("const JWT_SECRET = 'keyboard-cat';\n\n")
                f.write("function issueToken(user) {\n")
                f.write("  return jwt.sign({ id: user.id, role: user.role }, JWT_SECRET, { algorithm: 'none' });\n")
                f.write("}\n\n")
                f.write("function requireAdmin(req, res, next) {\n")
                f.write("  const decoded = jwt.decode(req.headers.authorization);\n")
                f.write("  if (decoded.role === 'admin') return next();\n")
                f.write("  return res.status(403).send('denied');\n")
                f.write("}\n")

            with open(os.path.join(base_dir, "api_policy.json"), "w") as f:
                json.dump({
                    "cors_origins": ["*"],
                    "rate_limit_rpm": 0,
                    "require_auth": False,
                    "admin_routes_public": True
                }, f, indent=4)

            with open(os.path.join(base_dir, "payment_debug.log"), "w") as f:
                f.write("[DEBUG] card=4111111111111111 cvv=123 jwt=eyJhbGciOiJub25lIn0\n")

        elif scenario_id == 6:
            # LAB: WebGoat-style unsafe deserialization + weak upload policy
            with open(os.path.join(base_dir, "profile_importer.py"), "w") as f:
                f.write("import pickle\n\n")
                f.write("def import_profile(raw_bytes):\n")
                f.write("    profile = pickle.loads(raw_bytes)\n")
                f.write("    return profile\n")

            with open(os.path.join(base_dir, "upload_policy.yaml"), "w") as f:
                yaml.safe_dump({
                    "allow_extensions": ["*"],
                    "max_size_mb": 100,
                    "scan_uploads": False,
                    "store_outside_webroot": False
                }, f, default_flow_style=False)

            with open(os.path.join(base_dir, "worker_permissions.json"), "w") as f:
                json.dump({
                    "worker_user": "root",
                    "can_spawn_shell": True,
                    "network_egress": "0.0.0.0/0"
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

        elif scenario_id == 4:
            # Vuln 1 — SQL injection in login handler
            try:
                content = open(os.path.join(base_dir, "login_handler.py")).read()
                unsafe = any(token in content for token in ["f\"SELECT", "f'SELECT", ".format(", "% username", "% password"])
                parameterized = "execute(" in content and any(token in content for token in ["?", "%s", ":username"])
                fixed = parameterized and not unsafe and "password_hash" in content
                detail = "parameterized query + password hash comparison" if fixed else "CWE-89: string-built SQL login query"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S4-V1", "file": "login_handler.py", "cwe": "CWE-89",
                          "description": "DVWA-style SQL injection in login flow", "fixed": fixed, "detail": detail})

            # Vuln 2 — weak session and CSRF controls
            try:
                with open(os.path.join(base_dir, "session_config.json")) as f:
                    d = json.load(f)
                fixed = d.get("cookie_secure") is True and \
                        d.get("cookie_http_only") is True and \
                        d.get("csrf_protection") is True and \
                        d.get("same_site") in ["Strict", "Lax"] and \
                        "dev-secret-123" not in d.get("session_secret", "")
                detail = "secure cookies + CSRF enabled" if fixed else "CWE-352/CWE-614: weak session cookie and CSRF policy"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S4-V2", "file": "session_config.json", "cwe": "CWE-352",
                          "description": "Weak session cookie flags and CSRF disabled", "fixed": fixed, "detail": detail})

            # Vuln 3 — sensitive auth data in logs
            try:
                content = open(os.path.join(base_dir, "access_audit.log")).read().lower()
                fixed = "password=" not in content and "reset_live_" not in content and "' or '1'='1" not in content
                detail = "auth log scrubbed" if fixed else "CWE-532: passwords and reset token leaked in auth logs"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S4-V3", "file": "access_audit.log", "cwe": "CWE-532",
                          "description": "Credentials and reset token leaked in access logs", "fixed": fixed, "detail": detail})

        elif scenario_id == 5:
            # Vuln 1 — broken JWT verification
            try:
                content = open(os.path.join(base_dir, "auth_routes.js")).read()
                fixed = "keyboard-cat" not in content and \
                        "algorithm: 'none'" not in content and \
                        "jwt.decode" not in content and \
                        "jwt.verify" in content and \
                        "process.env.JWT_SECRET" in content
                detail = "JWT verified with env-backed secret" if fixed else "CWE-347: unsigned/decoded JWT trust"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S5-V1", "file": "auth_routes.js", "cwe": "CWE-347",
                          "description": "Juice Shop-style broken JWT verification", "fixed": fixed, "detail": detail})

            # Vuln 2 — permissive API policy
            try:
                with open(os.path.join(base_dir, "api_policy.json")) as f:
                    d = json.load(f)
                fixed = "*" not in d.get("cors_origins", []) and \
                        d.get("rate_limit_rpm", 0) > 0 and \
                        d.get("require_auth") is True and \
                        d.get("admin_routes_public") is False
                detail = "auth, rate limit, and scoped CORS enforced" if fixed else "CWE-942/CWE-306: public API policy"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S5-V2", "file": "api_policy.json", "cwe": "CWE-942",
                          "description": "Permissive CORS, no rate limit, public admin API", "fixed": fixed, "detail": detail})

            # Vuln 3 — payment data in debug log
            try:
                content = open(os.path.join(base_dir, "payment_debug.log")).read().lower()
                fixed = "4111111111111111" not in content and "cvv" not in content and "eyj" not in content
                detail = "payment telemetry scrubbed" if fixed else "CWE-532: card data and token leaked in log"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S5-V3", "file": "payment_debug.log", "cwe": "CWE-532",
                          "description": "Card data and JWT leaked in debug log", "fixed": fixed, "detail": detail})

        elif scenario_id == 6:
            # Vuln 1 — unsafe pickle deserialization
            try:
                content = open(os.path.join(base_dir, "profile_importer.py")).read()
                fixed = "pickle.loads" not in content and \
                        "json.loads" in content and \
                        "validate_profile" in content
                detail = "JSON parser + schema validation" if fixed else "CWE-502: unsafe pickle deserialization"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S6-V1", "file": "profile_importer.py", "cwe": "CWE-502",
                          "description": "WebGoat-style unsafe object deserialization", "fixed": fixed, "detail": detail})

            # Vuln 2 — unsafe upload policy
            try:
                with open(os.path.join(base_dir, "upload_policy.yaml")) as f:
                    d = yaml.safe_load(f)
                extensions = d.get("allow_extensions", [])
                fixed = "*" not in extensions and \
                        d.get("scan_uploads") is True and \
                        d.get("store_outside_webroot") is True and \
                        d.get("max_size_mb", 100) <= 10
                detail = "uploads restricted and scanned" if fixed else "CWE-434: unrestricted file upload policy"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S6-V2", "file": "upload_policy.yaml", "cwe": "CWE-434",
                          "description": "Unrestricted upload extension and storage policy", "fixed": fixed, "detail": detail})

            # Vuln 3 — overprivileged worker
            try:
                with open(os.path.join(base_dir, "worker_permissions.json")) as f:
                    d = json.load(f)
                fixed = d.get("worker_user") not in ["root", "admin"] and \
                        d.get("can_spawn_shell") is False and \
                        d.get("network_egress") not in ["0.0.0.0/0", "*"]
                detail = "least privilege worker policy" if fixed else "CWE-250: worker runs with excessive privileges"
            except Exception as e:
                fixed, detail = False, str(e)
            vulns.append({"id": "S6-V3", "file": "worker_permissions.json", "cwe": "CWE-250",
                          "description": "Background worker has root shell and unrestricted egress", "fixed": fixed, "detail": detail})

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
    
    # Fallback simulation logic for Vyber CLI commands. Keep this intentionally
    # narrow: agents can inspect sandbox files and apply simple hardening, but
    # they do not receive an unrestricted shell when the CLI is unavailable.
    instruction_lower = instruction.lower().strip()

    def sandbox_files() -> list[str]:
        try:
            return sorted(
                name for name in os.listdir(workspace_dir)
                if os.path.isfile(os.path.join(workspace_dir, name))
            )
        except Exception:
            return []

    def mentioned_file() -> str | None:
        for name in sandbox_files():
            if name.lower() in instruction_lower:
                return name
        return None

    if "list" in instruction_lower or instruction_lower in ["ls", "ls -la", "dir"]:
        cmd = ["ls", "-la"]
    elif "inspect" in instruction_lower or "cat" in instruction_lower or "read" in instruction_lower:
        target = mentioned_file()
        if target:
            cmd = ["cat", target]
        else:
            cmd = ["ls", "-la"]
    elif "nmap" in instruction_lower:
        cmd = ["nmap", "localhost"]
    elif instruction_lower.startswith("chmod "):
        parts = shlex.split(instruction)
        mode = parts[1] if len(parts) >= 2 else "600"
        target = mentioned_file() or (parts[-1] if len(parts) >= 3 else "")
        if target and os.path.basename(target) in sandbox_files():
            cmd = ["chmod", mode, os.path.basename(target)]
        else:
            cmd = ["ls", "-la"]
    else:
        target = mentioned_file()
        cmd = ["cat", target] if target else ["ls", "-la"]

    res = subprocess.run(cmd, capture_output=True, text=True, cwd=workspace_dir)
    return f"[Vyber Agent SDK Fallback] Executing: {' '.join(cmd)}\n{res.stdout}\n{res.stderr}"

def remediation_hint(vuln_id: str) -> str:
    hints = {
        "S1-V1": "replace plaintext database_url and api_key with environment-variable references; disable debug",
        "S1-V2": "remove live cloud/payment keys and replace them with secret-manager or environment placeholders",
        "S1-V3": "remove embedded DB password from deploy.sh and chmod the script to 600, 640, or 700",
        "S2-V1": "bind database host to 127.0.0.1 or localhost and set auth_required=true",
        "S2-V2": "remove SSLv2/SSLv3/TLSv1 and enforce TLSv1.2/TLSv1.3 with strong ciphers",
        "S2-V3": "replace 0-65535 from 0.0.0.0/0 allow rules with least-privilege inbound rules",
        "S3-V1": "upgrade endpoint to https, enable ssl and certificate verification, and set a real cipher",
        "S3-V2": "scrub credit card values and CVV from logs while preserving non-sensitive telemetry",
        "S3-V3": "enable auth, set a positive rate limit, and make admin_endpoint_public=false",
        "S4-V1": "rewrite login_handler.py with parameterized SQL and password_hash comparison; remove f-string SQL",
        "S4-V2": "rotate dev session secret, set secure/httpOnly cookies, enable CSRF, and use SameSite Strict or Lax",
        "S4-V3": "remove password, SQL injection payload, and reset_live token values from the auth log",
        "S5-V1": "use process.env.JWT_SECRET, jwt.verify, and a real signing algorithm; remove algorithm none and jwt.decode trust",
        "S5-V2": "scope CORS origins, require auth, set rate_limit_rpm > 0, and make admin routes private",
        "S5-V3": "remove card number, CVV, and JWT-like token values from payment debug logs",
        "S6-V1": "replace pickle.loads with json.loads plus validate_profile schema checks",
        "S6-V2": "remove wildcard upload extensions, enable scanning, store outside webroot, and cap size at 10MB or less",
        "S6-V3": "run worker as non-root, disallow shell spawning, and restrict network egress",
    }
    return hints.get(vuln_id, "apply the least-privilege secure configuration required by the validator")

def normalize_exploit_report(report: str, expected_vulns: list[dict]) -> str:
    expected_ids = {v["id"] for v in expected_vulns}
    allowed_prefixes = (
        "FINDING ",
        "FILE:",
        "CWE:",
        "SEVERITY:",
        "EVIDENCE:",
        "ATTACK_PATH:",
        "IMPACT:",
    )
    stop_prefixes = (
        "RECOMMENDATION",
        "RECOMMENDATIONS",
        "MITIGATION",
        "MITIGATIONS",
        "VULNERABILITY STATUS",
        "NIST",
        "MITRE",
        "DEFENSIVE POSTURE",
        "RISK MITIGATION",
    )
    cleaned = []
    current_finding = None

    for raw_line in report.replace("\\n", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        upper = line.upper()
        if upper.startswith(stop_prefixes):
            break

        if line.startswith("FINDING "):
            parts = line.split()
            current_finding = parts[1] if len(parts) > 1 else None
            if current_finding in expected_ids:
                cleaned.append(line)
            continue

        if current_finding not in expected_ids:
            continue

        if line.startswith(allowed_prefixes):
            cleaned.append(line)

    normalized = "\n".join(cleaned).strip()
    return normalized or report.strip()

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
        MAX_ROUNDS = 1

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
                f"  {v['id']} | {v['cwe']} | {v['file']} | {v['description']} | current: {v['detail']} | fix: {remediation_hint(v['id'])}" for v in remaining
            )
            red_prompt = f"""You are Vyber Red, an autonomous security analyst running inside a controlled cyber-range. Operate only inside /tmp/sandbox/. Be concise, evidence-led, and defensive. No markdown fences.

UNPATCHED VULNERABILITIES ({len(remaining)} remaining):
{vuln_list_txt}

TOOLS:
  vyber list          — list directory
  vyber read <file>   — read file content

ACTION FORMAT (one action per response):
THINK: <one-line reasoning>
EXEC: vyber <instruction>

FINAL REPORT FORMAT (after enough evidence):
EXPLOIT_REPORT:
FINDING <vuln_id>
FILE: <filename>
CWE: <cwe>
SEVERITY: <Critical|High|Medium|Low>
EVIDENCE: <exact vulnerable pattern observed>
ATTACK_PATH: <one-line realistic exploit path>
IMPACT: <one-line business/security impact>
...

Begin with `vyber list`, then read every vulnerable file before writing EXPLOIT_REPORT."""

            exploit_report = ""
            for turn in range(len(remaining) + 2):
                yield (red_terminal + f"\n  [{ts()}] ▶ thinking...\n", blue_terminal, f"Round {round_num} — Red Agent reconning...")
                response = model_server.generate.remote(red_prompt, openai_api_key)

                if "EXPLOIT_REPORT:" in response:
                    exploit_report = response.split("EXPLOIT_REPORT:")[1].strip()
                    exploit_report = normalize_exploit_report(exploit_report, remaining)
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
                    exploit_report = normalize_exploit_report(exploit_report, remaining)
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

            blue_prompt = f"""You are Vyber Blue, an autonomous self-healing security engineer running inside a controlled cyber-range. Operate only inside /tmp/sandbox/. Be concise, evidence-led, and defensive. No markdown fences.

THREAT INTEL (red team exploit report):
{exploit_report}

UNPATCHED VULNERABILITIES ({len(remaining)}):
{vuln_list_txt}

PATCH STANDARD:
  - Preserve the app's intended behavior while removing the vulnerable pattern.
  - Use production-safe defaults: least privilege, parameterized inputs, secure cookies, scoped CORS, TLS, auth, rate limits, safe parsers, and sanitized logs.
  - Output complete replacement file contents, not snippets.
  - Never wrap CONTENT in markdown fences.
  - After each action, wait for the next observation. Output PATCH_COMPLETE only after all validator criteria are satisfied.

TOOLS:
  ACTION: edit <filepath>    — rewrite a file (provide CONTENT: block)
  ACTION: vyber <command>    — run shell command (chmod, etc.)

OUTPUT FORMAT (one action per response):
THINK: <one-line technical reasoning>
PATCH_META: vuln=<vuln_id> control=<security control applied> validates=<expected validator result>
ACTION: edit /tmp/sandbox/<filename>
CONTENT:
<full new secure file content>

OR:
THINK: <one-line reasoning>
PATCH_META: vuln=<vuln_id> control=<security control applied> validates=<expected validator result>
ACTION: vyber <command>

Patch ALL vulnerabilities. When every vuln is fixed output: PATCH_COMPLETE"""

            for turn in range(len(remaining) * 3 + 3):
                yield (red_terminal, blue_terminal + f"\n  [{ts()}] ▶ thinking...\n", f"Round {round_num} — Blue Agent patching...")
                response = model_server.generate.remote(blue_prompt, openai_api_key)

                if "PATCH_COMPLETE" in response:
                    check_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
                    check_open = [v for v in check_vulns if not v["fixed"]]
                    if not check_open:
                        blue_terminal += f"  [{ts()}] PATCH_COMPLETE accepted by validator\n"
                        break
                    validator_feedback = "; ".join(
                        f"{v['id']} {v['file']} still open: {v['detail']} | required: {remediation_hint(v['id'])}"
                        for v in check_open
                    )
                    blue_terminal += f"  [{ts()}] PATCH_COMPLETE rejected by validator\n"
                    blue_terminal += f"  [{ts()}] OPEN   {validator_feedback}\n"
                    blue_prompt += (
                        "\nVALIDATOR_REJECTED_PATCH_COMPLETE:\n"
                        f"{validator_feedback}\n"
                        "Continue with ACTION: edit or ACTION: vyber. Do not output PATCH_COMPLETE until no vulnerabilities remain.\nNext:"
                    )
                    yield (red_terminal, blue_terminal, f"Round {round_num} — validator rejected incomplete patch")
                    time.sleep(0.8)
                    continue

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
                    after_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
                    after_open = [v for v in after_vulns if not v["fixed"]]
                    validator_state = "all validators passed" if not after_open else "; ".join(
                        f"{v['id']} open: {v['detail']}" for v in after_open
                    )
                    yield (red_terminal, blue_terminal, f"Round {round_num} — patch applied to {os.path.basename(filepath)}")
                    blue_prompt += f"\nTHINK: {think}\nACTION: edit {filepath}\nResult: written.\nVALIDATOR_STATE: {validator_state}\nNext:"
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
                    after_vulns = CyberRangeScenarios.list_vulnerabilities(scenario_id, base_dir)
                    after_open = [v for v in after_vulns if not v["fixed"]]
                    validator_state = "all validators passed" if not after_open else "; ".join(
                        f"{v['id']} open: {v['detail']}" for v in after_open
                    )
                    yield (red_terminal, blue_terminal, f"Round {round_num} — hardening: {cmd}")
                    blue_prompt += f"\nTHINK: {think}\nACTION: vyber {cmd}\nSTDOUT:\n{out}\nVALIDATOR_STATE: {validator_state}\nNext:"
                    time.sleep(0.8)
                else:
                    blue_terminal += f"  [{ts()}] RESPONSE rejected: no actionable patch command\n"
                    blue_prompt += (
                        "\nFORMAT_REJECTED:\n"
                        "Your previous response did not contain ACTION: edit, ACTION: vyber, or valid PATCH_COMPLETE.\n"
                        "Continue with one concrete patch action using the required format.\nNext:"
                    )
                    yield (red_terminal, blue_terminal, f"Round {round_num} — waiting for actionable Blue Agent patch")
                    time.sleep(0.8)
                    continue

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
        red_terminal  += f"\n  [{ts()}] verdict : ✗ {open_count} EXPLOITS STILL ACTIVE\n"
        red_terminal  += f"  [{ts()}] result  : SYSTEM COMPROMISED\n"
        blue_terminal += f"\n  [{ts()}] verdict : ✗ {open_count} VULNERABILITIES UNPATCHED\n"
        blue_terminal += f"  [{ts()}] result  : SYSTEM AT RISK\n"
        yield (red_terminal, blue_terminal, f"✗ {open_count}/{len(final_vulns)} vulnerabilities remain unpatched")
