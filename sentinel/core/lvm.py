import json
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any, List


def run_json_cmd(cmd: List[str]) -> Dict[str, Any]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def parse_size_gb(size_str: str) -> float:
    clean = size_str.strip().lstrip("<").rstrip("gG")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def get_volume_groups() -> List[Dict[str, str]]:
    data = run_json_cmd(["vgs", "--reportformat", "json", "--units", "g"])
    try:
        return data["report"][0]["vg"]
    except (KeyError, IndexError):
        return []


def get_logical_volumes() -> List[Dict[str, Any]]:
    data = run_json_cmd([
        "lvs", "--reportformat", "json", "--units", "g",
        "-o", "lv_name,vg_name,lv_size,lv_path,lv_attr"
    ])
    lvs_list = []
    try:
        raw_lvs = data["report"][0]["lv"]
    except (KeyError, IndexError):
        return []

    lsblk_data = run_json_cmd(["lsblk", "-J", "-o", "NAME,FSTYPE,MOUNTPOINTS"])
    mount_map = {}

    def walk_blocks(blocks):
        for b in blocks:
            mps = [m for m in (b.get("mountpoints") or []) if m]
            if mps:
                mount_map[b["name"]] = (b.get("fstype") or "unknown", mps[0])
            if "children" in b:
                walk_blocks(b["children"])

    walk_blocks(lsblk_data.get("blockdevices", []))

    for lv in raw_lvs:
        mapper_name = f"{lv['vg_name']}-{lv['lv_name']}"
        fstype, mountpoint = mount_map.get(mapper_name, ("unmounted", "-"))
        usage_pct = "-"
        usage_val = 0.0
        if mountpoint not in ("-", "[SWAP]"):
            try:
                usage = shutil.disk_usage(mountpoint)
                usage_val = (usage.used / usage.total) * 100
                usage_pct = f"{usage_val:.1f}%"
            except OSError:
                usage_pct = "N/A"

        lvs_list.append({
            "lv_name": lv["lv_name"],
            "vg_name": lv["vg_name"],
            "lv_path": lv.get("lv_path") or f"/dev/{lv['vg_name']}/{lv['lv_name']}",
            "size": lv["lv_size"],
            "fstype": fstype,
            "mountpoint": mountpoint,
            "usage": usage_pct,
            "usage_val": usage_val,
        })
    return lvs_list


def auto_heal_lvs(threshold: float = 80.0, extend_mb: int = 512, dry_run: bool = False) -> List[Dict[str, Any]]:
    """Scan mounted LVs and automatically extend any volume exceeding threshold."""
    vgs = {vg["vg_name"]: parse_size_gb(vg["vg_free"]) for vg in get_volume_groups()}
    lvs = get_logical_volumes()
    actions = []

    for lv in lvs:
        if lv["mountpoint"] in ("-", "[SWAP]") or lv["usage_val"] < threshold:
            continue

        vg_name = lv["vg_name"]
        free_gb = vgs.get(vg_name, 0.0)
        needed_gb = extend_mb / 1024.0

        if free_gb < needed_gb:
            actions.append({
                "lv": f"{vg_name}/{lv['lv_name']}",
                "status": "FAILED",
                "reason": f"Usage at {lv['usage']}, but VG '{vg_name}' only has {free_gb:.2f}G free."
            })
            continue

        cmd = ["lvextend", "-r", "-L", f"+{extend_mb}M", lv["lv_path"]]
        if dry_run:
            actions.append({
                "lv": f"{vg_name}/{lv['lv_name']}",
                "status": "DRY-RUN",
                "reason": f"Would execute: {' '.join(cmd)}"
            })
        else:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                vgs[vg_name] -= needed_gb
                actions.append({
                    "lv": f"{vg_name}/{lv['lv_name']}",
                    "status": "HEALED",
                    "reason": f"Extended by +{extend_mb}M online (was {lv['usage']} on {lv['mountpoint']})."
                })
            else:
                actions.append({
                    "lv": f"{vg_name}/{lv['lv_name']}",
                    "status": "ERROR",
                    "reason": res.stderr.strip()
                })
    return actions
