"""Email delivery helpers with SMTP and Brevo API support."""

import json
import logging
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_via_brevo_api(
    subject: str,
    message: str,
    recipient_list: List[str],
    html_message: Optional[str] = None,
    from_email: Optional[str] = None,
) -> Dict[str, str]:
    api_key = getattr(settings, "BREVO_API_KEY", "")
    if not api_key:
        raise ValueError("BREVO_API_KEY is not configured")

    sender_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "")
    if not sender_email:
        raise ValueError("DEFAULT_FROM_EMAIL is not configured")

    payload = {
        "sender": {"email": sender_email},
        "to": [{"email": email} for email in recipient_list],
        "subject": subject,
        "textContent": message or "",
        "htmlContent": html_message or message or "",
    }

    endpoint = getattr(settings, "BREVO_API_ENDPOINT", "https://api.brevo.com/v3/smtp/email")
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key,
        },
        method="POST",
    )

    timeout = int(getattr(settings, "EMAIL_TIMEOUT", 30))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8") if resp else "{}"
            data = json.loads(body or "{}")
            message_id = data.get("messageId") or data.get("messageIds", [None])[0]
            return {
                "provider": "brevo_api",
                "message_id": str(message_id or ""),
            }
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        logger.error("Brevo API HTTP error: %s %s", exc.code, details)
        raise


def send_app_email(
    *,
    subject: str,
    message: str,
    recipient_list: List[str],
    html_message: Optional[str] = None,
    from_email: Optional[str] = None,
    fail_silently: bool = False,
) -> Dict[str, str]:
    """
    Send email based on EMAIL_DELIVERY_MODE.

    Modes:
    - smtp: SMTP only
    - brevo_api: Brevo API only
    - smtp_with_brevo_fallback: SMTP first, then Brevo API on SMTP failure
    """
    mode = str(getattr(settings, "EMAIL_DELIVERY_MODE", "smtp")).strip().lower()

    if mode == "brevo_api":
        return _send_via_brevo_api(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            html_message=html_message,
            from_email=from_email,
        )

    if mode == "smtp_with_brevo_fallback":
        try:
            sent_count = send_mail(
                subject=subject,
                message=message,
                from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", ""),
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=fail_silently,
            )
            return {
                "provider": "smtp",
                "message_id": "",
                "sent_count": str(sent_count),
            }
        except Exception:
            logger.warning("SMTP failed; falling back to Brevo API", exc_info=True)
            return _send_via_brevo_api(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                html_message=html_message,
                from_email=from_email,
            )

    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", ""),
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=fail_silently,
    )
    return {
        "provider": "smtp",
        "message_id": "",
        "sent_count": str(sent_count),
    }
