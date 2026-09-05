#!/usr/bin/env python3
"""
External Monitor for souss-actualites.com
Checks TARGET_URL every CHECK_INTERVAL seconds.
After FAIL_THRESHOLD consecutive failures: sends alerts + triggers Railway self-heal.
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv

from modules.email_alerts import send_email_alert
from modules.telegram_alerts import send_telegram_alert
from modules.self_heal import restart_railway_service

load_dotenv()

# --- Config ---
TARGET_URL       = os.getenv("TARGET_URL", "https://souss-actualites.com")
CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL", "60"))   # seconds between checks
FAIL_THRESHOLD   = int(os.getenv("FAIL_THRESHOLD", "3"))    # consecutive failures before alert
REQUEST_TIMEOUT  = int(os.getenv("REQUEST_TIMEOUT", "15"))  # seconds per request
ALERT_EMAIL      = os.getenv("ALERT_EMAIL", "")
TELEGRAM_BOT     = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT    = os.getenv("TELEGRAM_CHAT_ID", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("monitor")


def check_site(url: str, timeout: int) -> tuple:
    """Returns (ok, status_code, error_message)."""
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        ok = r.status_code < 500
        return ok, r.status_code, ""
    except requests.exceptions.Timeout:
        return False, 0, "Timeout"
    except requests.exceptions.ConnectionError as e:
        return False, 0, f"ConnectionError: {e}"
    except Exception as e:
        return False, 0, str(e)


def alert(subject: str, body: str):
    """Fire all configured alert channels."""
    if ALERT_EMAIL:
        try:
            send_email_alert(subject, body)
            log.info("Email alert sent to %s", ALERT_EMAIL)
        except Exception as e:
            log.error("Email alert failed: %s", e)

    if TELEGRAM_BOT and TELEGRAM_CHAT:
        try:
            send_telegram_alert(f"Alerta: {subject}\n\n{body}")
            log.info("Telegram alert sent")
        except Exception as e:
            log.error("Telegram alert failed: %s", e)


def main():
    log.info("Monitor starting - target: %s", TARGET_URL)
    log.info("Interval: %ds | Fail threshold: %d | Timeout: %ds",
             CHECK_INTERVAL, FAIL_THRESHOLD, REQUEST_TIMEOUT)

    consecutive_failures = 0
    alert_fired = False
    recovery_notified = False

    while True:
        ok, code, err = check_site(TARGET_URL, REQUEST_TIMEOUT)

        if ok:
            log.info("OK  %s - HTTP %d", TARGET_URL, code)
            if alert_fired and not recovery_notified:
                msg = f"{TARGET_URL} is back online (HTTP {code})."
                log.info("RECOVERY: %s", msg)
                alert(f"RECOVERY: {TARGET_URL}", msg)
                recovery_notified = True
            consecutive_failures = 0
            alert_fired = False
            recovery_notified = False
        else:
            consecutive_failures += 1
            log.warning("FAIL #%d - %s - code=%d err=%s",
                        consecutive_failures, TARGET_URL, code, err or "-")

            if consecutive_failures >= FAIL_THRESHOLD and not alert_fired:
                subject = f"DOWN: {TARGET_URL} ({consecutive_failures} failures)"
                body = (
                    f"Site: {TARGET_URL}\n"
                    f"Consecutive failures: {consecutive_failures}\n"
                    f"Last HTTP status: {code}\n"
                    f"Error: {err or 'N/A'}\n\n"
                    f"Attempting Railway auto-restart..."
                )
                alert(subject, body)
                alert_fired = True
                healed = restart_railway_service()
                if healed:
                    log.info("Railway restart triggered successfully")
                else:
                    log.warning("Railway restart failed or not configured")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
