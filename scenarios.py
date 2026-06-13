import os
import json
import yaml

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
            
            # Create a mock description file to guide the agent
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
            
            # Create a mock readme
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
                
            # Create a mock network log that reveals the cleartext vulnerability
            log_path = os.path.join(base_dir, "traffic_stream.log")
            log_content = (
                "[INFO] Ingress traffic started on http://billing.securecorp.internal/stream\n"
                "[DATA] Transmission payload: {\"user_id\": \"1042\", \"credit_card\": \"4111-2222-3333-4444\", \"cvv\": \"123\"}\n"
                "[WARNING] SSL/TLS is disabled. Traffic is susceptible to sniffing!\n"
            )
            with open(log_path, "w") as f:
                f.write(log_content)
                
            # Create a mock readme
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
        Returns (is_secure, explanation_message).
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
                
                # Check if secret has been parameterized or replaced
                if "hf_live_key_987654321" in api_key:
                    return False, "Plain-text API key 'hf_live_key_987654321' is still present in app_config.json."
                if "super_secret_master_password_123" in db_url:
                    return False, "Plain-text password 'super_secret_master_password_123' is still present in database_url."
                
                # Check if they parameterize them
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
