import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_alert(message: str, parse_mode: str = "HTML") -> bool:
    """Envía alerta al canal Telegram configurado."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados. Alerta omitida.")
        return False

    url = TELEGRAM_API.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            logger.info("Alerta Telegram enviada.")
            return True
        logger.error("Telegram API error: %s", data)
        return False
    except requests.exceptions.RequestException as e:
        logger.error("Error enviando alerta Telegram: %s", e)
        return False
