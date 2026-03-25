"""Celery tasks for notification retry workflows."""

from celery import shared_task
from django.utils import timezone

from Real_MFA.email_provider import send_app_email
from .models import EmailNotification


def _plain_text_from_body(body: str) -> str:
    """Fallback plain-text body for API providers that also expect text content."""
    if not body:
        return ""
    return body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")


@shared_task(bind=True)
def send_pending_notifications(self):
    """
    Retry unsent email notifications.

    Processes:
    - status='pending'
    - status='failed' with retry_count < max_retries
    """
    pending_qs = EmailNotification.objects.filter(status="pending")
    retry_qs = EmailNotification.objects.filter(status="failed")

    total_candidates = pending_qs.count()
    total_candidates += sum(1 for item in retry_qs if item.is_retryable())

    sent_count = 0
    failed_count = 0

    # Send all pending records first.
    for notification in pending_qs.iterator():
        try:
            result = send_app_email(
                subject=notification.subject,
                message=_plain_text_from_body(notification.body),
                recipient_list=[notification.to_email],
                html_message=notification.body,
                fail_silently=False,
            )
            notification.provider = result.get("provider", notification.provider)
            notification.save(update_fields=["provider"])
            notification.mark_sent(provider_message_id=result.get("message_id") or None)
            sent_count += 1
        except Exception as exc:
            notification.increment_retry()
            notification.mark_failed(str(exc))
            failed_count += 1

    # Retry failed records that are still retryable.
    for notification in retry_qs.iterator():
        if not notification.is_retryable():
            continue
        try:
            result = send_app_email(
                subject=notification.subject,
                message=_plain_text_from_body(notification.body),
                recipient_list=[notification.to_email],
                html_message=notification.body,
                fail_silently=False,
            )
            notification.provider = result.get("provider", notification.provider)
            notification.save(update_fields=["provider"])
            notification.mark_sent(provider_message_id=result.get("message_id") or None)
            sent_count += 1
        except Exception as exc:
            notification.increment_retry()
            notification.mark_failed(str(exc))
            failed_count += 1

    return {
        "status": "completed",
        "at": timezone.now().isoformat(),
        "candidates": total_candidates,
        "sent": sent_count,
        "failed": failed_count,
    }
