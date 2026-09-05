"""Send alert emails via SMTP."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ALERT_EMAIL    = os.getenv("ALERT_EMAIL", "")
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASSWORD  = os.getenv("SMTP_PASSWORD", "")
SENDER_NAME    = os.getenv("SENDER_NAME", "Site Monitor")


def send_email_alert(subject: str, body: str, to: str = None):
    """Send a plain-text alert email."""
    recipient = to or ALERT_EMAIL
    if not recipient:
        raise ValueError("No recipient email configured (ALERT_EMAIL)")
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP credentials not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"]      = recipient

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [recipient], msg.as_string())
