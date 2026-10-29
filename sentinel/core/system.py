import platform
import subprocess
import psutil
from typing import Dict


def get_cmd_output(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else "Unknown"


def get_system_summary() -> Dict[str, str]:
    mem = psutil.virtual_memory()
    return {
        "hostname": platform.node(),
        "kernel": platform.release(),
        "cpu_cores": str(psutil.cpu_count(logical=True)),
        "cpu_usage": f"{psutil.cpu_percent(interval=0.2)}%",
        "ram_usage": f"{mem.used // (1024**2)} MiB / {mem.total // (1024**2)} MiB ({mem.percent}%)",
        "selinux": get_cmd_output(["getenforce"]),
        "firewalld": get_cmd_output(["firewall-cmd", "--state"]),
    }
