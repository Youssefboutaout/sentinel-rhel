
<div align="center">

# 🛡️ Sentinel-RHEL

**Autonomous infrastructure, storage and security management for Red Hat Enterprise Linux 10**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-RHEL%2010-EE0000?logo=redhat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-blue.svg)

</div>

---

## Overview

**Sentinel-RHEL** is a Python CLI tool and background daemon that automates routine Linux administration on RHEL 10: LVM storage self-healing, CIS-style security audits, network inspection, a combined infrastructure tree and instant Telegram alerts.

> **Why "Sentinel"?** It watches the system continuously and acts on problems before they become outages.

<!-- ![Sentinel demo](docs/demo.gif) -->

---

## Features

| Module | Description |
|---|---|
| 🧠 **LVM Self-Healing** | Monitors logical volume usage and extends the volume and filesystem (XFS/ext4) online from the volume group's free space when a threshold is crossed. |
| 🔒 **Security Audit** | Checks SELinux enforcement and SSH hardening (e.g. `PermitRootLogin`) and produces a compliance score out of 100. |
| 🌐 **Network Telemetry** | Lists active interfaces with status, IPv4/IPv6 addresses and link speed. |
| 🌳 **Infrastructure Tree** | Combines system telemetry, LVM topology and directory traversal under mount points into one visual tree. |
| 📱 **Telegram Alerts & Reports** | Sends instant notifications on corrective actions or emergencies, plus a full infrastructure report (`sentinel report`) straight to your phone. |
| 🔄 **Watchdog Daemon** | Runs as a `systemd` service for continuous monitoring and incident logging to the journal. |

---

## Requirements

- Red Hat Enterprise Linux 10 (or a compatible distribution)
- Python 3.12 or later
- Root privileges for LVM operations and the security audit
- LVM2, SELinux and firewalld for the related modules
- A Telegram bot token and chat ID (optional, for alerts)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Youssefboutaout/sentinel-rhel.git
cd sentinel-rhel

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode
pip install -e .
```

**Optional: make `sentinel` available system-wide**

```bash
sudo ln -sf "$(pwd)/.venv/bin/sentinel" /usr/local/bin/sentinel
```

---

## Configuration

Sentinel reads its settings from `/etc/sentinel/config.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"

watchdog:
  interval_seconds: 60
  threshold_percent: 80.0
  extend_mb: 512
```

**Getting Telegram credentials**

1. Message [@BotFather](https://t.me/BotFather) on Telegram, run `/newbot` and copy the token.
2. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`.

**Protect your token.** The config file contains a secret. Restrict it and never commit it:

```bash
sudo mkdir -p /etc/sentinel
sudo chmod 600 /etc/sentinel/config.yaml
```

Verify the setup:

```bash
sentinel alert-test
```

---

## Usage

```bash
sentinel --help
```

| Command | Description |
|---|---|
| `sentinel check-all` | Run a full diagnostic across all modules |
| `sentinel tree` | Display system telemetry, LVM topology and directory tree |
| `sentinel report` | Send a full infrastructure report to Telegram |
| `sentinel status` | System health, telemetry and LVM overview |
| `sentinel heal` | Detect and extend volumes above the usage threshold |
| `sentinel audit` | Security and CIS-style compliance audit |
| `sentinel network` | Network interface inspection |
| `sentinel alert-test` | Send a test message to verify the Telegram setup |

### Examples

```bash
# Preview what the self-healing engine would do (no changes made)
sentinel heal --dry-run

# Extend any volume above 80% usage by 512 MiB
sentinel heal --threshold 80 --extend-mb 512

# Run the security audit
sentinel audit

# Send the infrastructure report to your phone
sentinel report
```

> ⚠️ **Note:** `sentinel heal` modifies live storage. Run it with `--dry-run` first and make sure your volume group has free extents.

---

## Running as a Service

```bash
sudo cp sentinel-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sentinel-watchdog.service
```

Check its status and follow the logs:

```bash
sudo systemctl status sentinel-watchdog.service
sudo journalctl -u sentinel-watchdog.service -f
```

---

## Project Structure

```text
sentinel-rhel/
├── sentinel/
│   ├── __init__.py
│   ├── cli.py            # Typer CLI and command definitions
│   └── core/
│       ├── system.py     # CPU, RAM, kernel, uptime and load telemetry
│       ├── lvm.py        # LVM parsing and auto-healing logic
│       ├── network.py    # Network interface inspection
│       ├── security.py   # SELinux and SSH hardening audit
│       ├── alerts.py     # Telegram alerts and reports
│       └── watchdog.py   # Daemon loop and event logging
├── sentinel-watchdog.service
├── pyproject.toml
└── README.md
```

---

## Tech Stack

**Python** · **Typer** · **Rich** · **psutil** · **LVM2** · **systemd** · **SELinux** · **firewalld** · **Telegram Bot API**

---

## Roadmap

- [ ] Alert cooldown to avoid repeated notifications
- [ ] Failed systemd service detection and auto-restart
- [ ] Heal history in SQLite (`sentinel history`)
- [ ] SELinux AVC denial analysis with suggested fixes
- [ ] Unit tests (pytest) and CI with GitHub Actions
- [ ] REST API (FastAPI) and web dashboard
- [ ] Prometheus metrics export
- [ ] RPM packaging

---

## Contributing

Issues and pull requests are welcome. For larger changes, please open an issue first to discuss what you would like to change.

---

## License

Distributed under the MIT License. See `LICENSE` for details.

---

## Author

**Youssef Boutaout**
Computer Science Student · Linux Systems Enthusiast

[GitHub](https://github.com/Youssefboutaout)
