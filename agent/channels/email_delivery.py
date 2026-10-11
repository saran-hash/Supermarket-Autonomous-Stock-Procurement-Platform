"""Email dispatch adapter using SMTP / Gmail."""

import os
import smtplib
from email.mime.text import MIMEText


def send_email_po(recipient_email: str, subject: str, body: str) -> bool:
    """Send formal PO email via SMTP or fallback simulation."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not smtp_host or not smtp_user:
        print(f"   [Email Sim] Sent to {recipient_email} | Subject: {subject}")
        return True

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
