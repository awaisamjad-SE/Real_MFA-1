"""
Devices Signals - Send notifications for device-related events
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Device
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Device)
def notify_new_device_login(sender, instance, created, **kwargs):
    """Send notification when a new device is registered"""
    if created:
        from notification.utils import notify_new_device_login
        try:
            notify_new_device_login(instance.user, instance)
            logger.info(f"New device login notification sent to {instance.user.email}")
        except Exception as e:
            logger.error(f"Failed to send new device notification: {e}")


@receiver(post_save, sender=Device)
def notify_device_verified(sender, instance, created, **kwargs):
    """Send notification when device is verified"""
    if not created:  # Only for updates
        # Check if device was just verified
        if instance.is_verified and not getattr(instance, '_verification_notified', False):
            from notification.utils import notify_device_verified
            try:
                notify_device_verified(instance.user, instance)
                logger.info(f"Device verified notification sent to {instance.user.email}")
                # Mark as notified to prevent duplicate notifications
                instance._verification_notified = True
            except Exception as e:
                logger.error(f"Failed to send device verified notification: {e}")
