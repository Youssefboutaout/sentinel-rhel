import psutil
import subprocess
from typing import List, Dict, Any

def get_network_interfaces() -> List[Dict[str, Any]]:
    """Retrieve active network interfaces, IP addresses, and operational status."""
    interfaces = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for interface_name, address_list in addrs.items():
        is_up = stats[interface_name].isup if interface_name in stats else False
        if not is_up and interface_name != "lo":
            continue

        ipv4 = "N/A"
        for addr in address_list:
            if addr.family.name == "AF_INET":
                ipv4 = addr.address

        interfaces.append({
            "name": interface_name,
            "status": "UP 🟢" if is_up else "DOWN 🔴",
            "ipv4": ipv4,
            "speed": f"{stats[interface_name].speed} Mbps" if interface_name in stats and stats[interface_name].speed > 0 else "Unknown"
        })
    return interfaces
