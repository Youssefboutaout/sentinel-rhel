import time
import logging
from sentinel.core.lvm import auto_heal_lvs

# Configuration des logs
LOG_FILE = "/var/log/sentinel_watch.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_watchdog_loop(interval_seconds: int = 60, threshold: float = 80.0):
    """Run continuous background monitoring for LVM capacity."""
    logging.info("Sentinel Watchdog service started.")
    print(f"🛡️ Sentinel Watchdog running... (Checking every {interval_seconds}s at >{threshold}% threshold)")
    
    try:
        while True:
            results = auto_heal_lvs(threshold=threshold, extend_mb=512, dry_run=False)
            if results:
                for r in results:
                    msg = f"HEAL ACTION: {r['lv']} - {r['reason']}"
                    logging.warning(msg)
                    print(f"⚠️ {msg}")
            else:
                logging.debug("All volumes healthy.")
            
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logging.info("Sentinel Watchdog stopped by user.")
        print("\n🛑 Watchdog stopped.")
