import time
import logging
from sentinel.core.lvm import auto_heal_lvs, get_volume_groups
from sentinel.core.security import get_security_audit
from sentinel.core.alerts import send_alert
import yaml
import os

LOG_FILE = "/var/log/sentinel_watch.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def load_watchdog_config():
    config_path = "/etc/sentinel/config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                w_conf = data.get("watchdog", {})
                return w_conf.get("interval_seconds", 60), w_conf.get("threshold_percent", 80.0), w_conf.get("extend_mb", 512)
        except Exception:
            pass
    return 60, 80.0, 512

def run_watchdog_loop():
    """Run continuous background monitoring for LVM capacity, security, and alerting."""
    interval, threshold, extend_mb = load_watchdog_config()
    logging.info("Sentinel Watchdog service started (v0.2.0).")
    print(f"🛡️ Sentinel Watchdog running... (Checking every {interval}s at >{threshold}% threshold)")
    
    try:
        while True:
            # 1. Check LVM & Self-Heal
            results = auto_heal_lvs(threshold=threshold, extend_mb=extend_mb, dry_run=False)
            if results:
                for r in results:
                    msg = f"HEAL ACTION: {r['lv']} - {r['reason']}"
                    logging.warning(msg)
                    print(f"⚠️ {msg}")
                    send_alert(f"Logical Volume *{r['lv']}* was automatically extended.\nReason: {r['reason']}", level="HEAL")

            # 2. Check Volume Group Free Space Pool Warning
            vgs = get_volume_groups()
            for vg in vgs:
                if vg.get("vg_free") == "0g" or vg.get("vg_free") == "0":
                    warn_msg = f"Volume Group *{vg['vg_name']}* is out of free space! Self-healing pool exhausted."
                    logging.error(warn_msg)
                    send_alert(warn_msg, level="CRITICAL")

            # 3. Check Security Score
            sec = get_security_audit()
            if sec["score"] < 70:
                sec_msg = f"Security compliance score dropped to *{sec['score']}/100*! Check vulnerabilities."
                logging.warning(sec_msg)
                send_alert(sec_msg, level="WARNING")

            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Sentinel Watchdog stopped by user.")
        print("\n🛑 Watchdog stopped.")
