---
title: Vyber
emoji: 🛡️
colorFrom: gray
colorTo: gray
sdk: gradio
sdk_version: 4.36.1
python_version: 3.11
app_file: app.py
pinned: false
---

# Vyber: Autonomous Self-Healing Cyber-Range

**Vyber** is a functional prototype of an autonomous, self-healing cyber-range. Built for the Hugging Face **Build Small Hackathon**, it simulates a continuous battle loop between an offensive agent (Red Team) and a defensive agent (Blue Team) operating inside secure, isolated serverless container sandboxes.

The goal is to demonstrate **zero-touch vulnerability remediation**—moving from threat detection to automated code patching and validation in seconds.

---

## What It Does
Vyber runs a multi-turn, stateful simulation loop where:
1. **Target Initialization**: A target playground environment is spun up with specific security vulnerabilities.
2. **Reconnaissance & Penetration (Red Team)**: The Attack Agent inspects configuration states, scans directories, runs reconnaissance commands, and outputs a structured JSON exploit strategy.
3. **Detection & Self-Healing (Blue Team)**: Acting as an automated SOC analyst, the Defense Agent reviews the system files and attack logs, constructs a configuration patch, edits the vulnerable file, and locks down permissions.
4. **Verification Scan**: The system forces the Red Team agent to re-run the exploit. If access is blocked, the system validates the infrastructure as secure.

---

## The Simulation Scenarios
The simulator features 3 distinct target vulnerability environments:
* **Scenario 1: Insecure Configuration File (Secret Leak)**
  * *Vulnerability*: Hardcoded plain-text API credentials and database connection strings in `app_config.json`.
  * *Mitigation*: Parameterizing the credentials and environment variables; tightening file access controls.
* **Scenario 2: Exposed Database Port (Global Binding)**
  * *Vulnerability*: Public database binding (`0.0.0.0`) on port `5432` with authentication disabled in `db_settings.yaml`.
  * *Mitigation*: Restricting database bind interface to `127.0.0.1` and enforcing `auth_required: true`.
* **Scenario 3: Unencrypted Communication Pipeline (MITM)**
  * *Vulnerability*: A simulated log capture indicating plain-text transit of customer billing payloads over unencrypted HTTP protocol.
  * *Mitigation*: Forcing HTTPS protocols, enabling SSL verification flags, and enforcing strong symmetric ciphers.

---

## Technical Stack & Infrastructure
* **Compute Backend**: Modal (`modal.App`) executing on demand on serverless GPU and CPU sandboxes.
* **Agent Tool Execution**: OpenCode CLI integrated during container image build, running in headless non-interactive script mode to execute bash commands and file edits.
* **Designated Models**: Configured for lightweight, highly-optimized open-weights models ($\le$ 32B parameters) like **`Qwen/Qwen2.5-7B-Instruct`** and **`meta-llama/Llama-3.2-3B-Instruct`** for fast, local inference.
* **UI Dashboard**: Built with Gradio (`gr.Blocks`) utilizing Python generators (`yield`) to stream terminal outputs character-by-character in real-time, preventing network timeout issues.

---

## Real-World Impact
1. **Minimizing MTTR (Mean Time to Remediation)**: Real-world security patches often take days or weeks of manual engineering. Vyber demonstrates how configuration drift and critical leaks can be corrected in under 30 seconds.
2. **Autonomous Pen-Testing**: Continuous scanning by AI pen-testers ensures that code repository merges do not leak credentials or misconfigure public network rules before deploying to production.
3. **Filtering Alert Noise**: By automatically generating and testing hotfixes inside staging sandboxes before notifying developers, it reduces alert fatigue for security operations center (SOC) teams.
