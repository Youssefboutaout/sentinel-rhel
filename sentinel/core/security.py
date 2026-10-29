import subprocess
import os
from typing import Dict, Any

def get_cmd_output(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else ""

def audit_ssh_config() -> Dict[str, str]:
    """Audit key SSH hardening settings from sshd_config."""
    config_path = "/etc/ssh/sshd_config"
    results = {"PermitRootLogin": "Unknown", "PasswordAuthentication": "Unknown"}
    
    if not os.path.exists(config_path):
        return results

    try:
        with open(config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("PermitRootLogin"):
                    results["PermitRootLogin"] = line.split()[1]
                elif line.startswith("PasswordAuthentication"):
                    results["PasswordAuthentication"] = line.split()[1]
    except Exception:
        pass
    return results

def get_security_audit() -> Dict[str, Any]:
    """Run security checks and compute a CIS-style compliance score."""
    selinux_mode = get_cmd_output(["getenforce"])
    ssh_status = audit_ssh_config()
    
    score = 100
    deductions = []

    if selinux_mode != "Enforcing":
        score -= 30
        deductions.append("SELinux is not Enforcing (-30)")
    
    root_login = ssh_status.get("PermitRootLogin", "").lower()
    if root_login in ["yes", "prohibit-password"]:
        score -= 20
        deductions.append(f"Root login via SSH is allowed ({root_login}) (-20)")

    return {
        "selinux": selinux_mode,
        "ssh": ssh_status,
        "score": max(0, score),
        "deductions": deductions
    }
