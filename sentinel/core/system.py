import psutil
import platform
import os
import subprocess
from typing import Dict, Any

def get_cmd_output(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else "Unknown"

def get_system_summary() -> Dict[str, Any]:
    """Retrieve comprehensive system telemetry including OS, Kernel, CPU, RAM, Uptime, and Load."""
    # OS Release info
    os_name = "Red Hat Enterprise Linux"
    if os.path.exists("/etc/redhat-release"):
        with open("/etc/redhat-release", "r") as f:
            os_name = f.read().strip()

    # Uptime
    boot_time = psutil.boot_time()
    import time
    uptime_seconds = time.time() - boot_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    uptime_str = f"{hours}h {minutes}m"

    # Load average
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)

    # CPU & RAM
    cpu_freq = psutil.cpu_freq()
    cpu_freq_str = f"{cpu_freq.current:.1f} MHz" if cpu_freq else "N/A"
    
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()

    # Security & Firewall status
    selinux = get_cmd_output(["getenforce"])
    firewalld = get_cmd_output(["systemctl", "is-active", "firewalld"])

    return {
        "hostname": platform.node(),
        "os_release": os_name,
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "uptime": uptime_str,
        "load_avg": f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}",
        "cpu_cores": psutil.cpu_count(logical=True),
        "cpu_usage": f"{psutil.cpu_percent(interval=0.1)}%",
        "cpu_freq": cpu_freq_str,
        "ram_usage": f"{virtual_mem.percent}% ({virtual_mem.used // (1024**2)}MB / {virtual_mem.total // (1024**2)}MB)",
        "swap_usage": f"{swap_mem.percent}%",
        "selinux": selinux,
        "firewalld": firewalld
    }
