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

**Vyber** is a prototype of an autonomous, self-healing cyber-range. Built for the Hugging Face **Build Small Hackathon**, it demonstrates how small, highly-optimized language models ($\le$ 32B parameters) can automate security operations—acting as both the pen-tester (Red Team) and the automated responder (Blue Team) in isolated container sandboxes.

The goal is to demonstrate **zero-touch vulnerability remediation**—moving from threat detection to automated code patching and mitigation validation in seconds, without any human intervention.

---

## ⚡ What is Vyber?

In traditional security, when a vulnerability is found (like a leaked key or an open port), the mean time to remediation (MTTR) is often measured in days or weeks. **Vyber** shows a future where security operations are autonomous:
1. **Offensive Agent (Red Team)**: Performs automated reconnaissance, scans configurations, identifies vulnerabilities, and outputs a structured exploit strategy.
2. **Defensive Agent (Blue Team)**: Acts as an autonomous SOC analyst. It intercepts the exploit plan, inspects the vulnerable files, deploys a secure configuration patch, and hardens the environment (e.g., locking down file permissions or updating firewall rules).
3. **Automated Verification**: The system forces the Red Team agent to re-run its exploit against the updated environment. If the exploit fails, the patch is validated as secure.

---

## 🖥️ How to Use the Dashboard

1. **Select a Scenario**: Use the dropdown at the top to choose one of the three sandbox target environments.
2. **Launch the Duel**: Click the **"Launch Simulation Duel"** button.
3. **Monitor the Terminals**:
   * **Left Terminal (Red Team Logs)**: Watch the offensive agent run recon commands, inspect configuration files, and attempt exploits.
   * **Right Terminal (Blue Team Logs)**: Watch the defensive agent analyze the threat, write code patches, apply hardening rules, and verify the mitigation.
4. **View Status**: The status banner displays the real-time phase of the battle loop.

---

## 🛡️ Target Scenarios

Vyber features three target environments simulating real-world security vulnerabilities:

### 1. Insecure Configuration (Secret Leak)
* **The Flaw**: Plain-text API credentials and database connection strings leaked inside `app_config.json`.
* **The Mitigation**: Parameterizing the secrets into environment variables and locking down file permissions (`chmod 600`).

### 2. Exposed Database Port (Global Binding)
* **The Flaw**: A PostgreSQL database bound globally to interface `0.0.0.0` with authentication disabled.
* **The Mitigation**: Restricting the database binding to localhost (`127.0.0.1`) and enforcing mandatory authentication.

### 3. Unencrypted Communication (MITM)
* **The Flaw**: Plaintext transit of billing payloads over unencrypted HTTP network rules.
* **The Mitigation**: Updating the configuration to force HTTPS, enabling SSL verification flags, and restricting accepted ciphers.

---

## 🚀 Underlying Engine
* **Off the Grid**: Runs 100% locally with no cloud APIs.
* **Well-Tuned**: Powered by a custom `Qwen2.5` model fine-tuned specifically on a cybersecurity instruction dataset.
* **Llama Champion**: Powered by the optimized `llama.cpp` runtime with GPU offloading and CUDA acceleration.
