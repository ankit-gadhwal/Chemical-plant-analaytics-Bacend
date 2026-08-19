import logging
from pathlib import Path
from typing import List
import httpx
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.config import Config

BASE_DIR = Path(__file__).resolve().parent

# Optional FastMail fallback
mail = None
try:
    if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
        mail_config = ConnectionConfig(
            MAIL_USERNAME=Config.MAIL_USERNAME,
            MAIL_PASSWORD=Config.MAIL_PASSWORD,
            MAIL_FROM=Config.MAIL_FROM or "noreply@chempulse.app",
            MAIL_PORT=Config.MAIL_PORT or 587,
            MAIL_SERVER=Config.MAIL_SERVER or "smtp.gmail.com",
            MAIL_FROM_NAME=Config.MAIL_FROM_NAME or "ChemPulse",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=Path(BASE_DIR, "templates"),
        )
        mail = FastMail(config=mail_config)
except Exception as e:
    logging.warning(f"FastMail initialization skipped: {e}")


def create_message(recipients: List[str], subject: str, body: str):
    message = MessageSchema(
        recipients=recipients, subject=subject, body=body, subtype=MessageType.html
    )
    return message


async def send_email_async(recipients: List[str], subject: str, body: str) -> bool:
    """
    Sends an email using Resend API (HTTPS port 443) if RESEND_API_KEY is configured,
    or falls back to FastMail (SMTP) if available.
    """
    # 1. Try Resend HTTP API first (Works everywhere, including Render free tier)
    if Config.RESEND_API_KEY:
        try:
            sender_from = (
                Config.MAIL_FROM
                if (Config.MAIL_FROM and "@" in Config.MAIL_FROM and not "gmail.com" in Config.MAIL_FROM)
                else "ChemPulse <onboarding@resend.dev>"
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": sender_from,
                        "to": recipients,
                        "subject": subject,
                        "html": body,
                    },
                )
                if response.status_code in (200, 201):
                    print(f"[EmailService] Successfully sent email via Resend API to {recipients}")
                    return True
                else:
                    print(f"[EmailService] Resend API error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"[EmailService] Resend API exception: {e}")

    # 2. Fallback to FastMail SMTP
    if mail:
        try:
            message = create_message(recipients=recipients, subject=subject, body=body)
            await mail.send_message(message)
            print(f"[EmailService] Successfully sent email via FastMail (SMTP) to {recipients}")
            return True
        except Exception as e:
            print(f"[EmailService] FastMail SMTP error: {e}")

    print(f"[EmailService] Notice: Email could not be sent to {recipients}. Please configure RESEND_API_KEY.")
    return False
