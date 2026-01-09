"""
Accounts Signals - Auto-create related objects and send notifications
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.contrib.auth.tokens import default_token_generator
from .models import User, Profile
import logging

logger = logging.getLogger(__name__)

# Custom signals for security events
password_changed = Signal()
mfa_status_changed = Signal()
profile_updated = Signal()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create Profile when User is created"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def send_verification_email_on_create(sender, instance, created, **kwargs):
    """
    Send verification email when a new user is created (via admin or any other path).
    Skips if:
    - User is not newly created
    - User email is already verified
    - _skip_verification_email flag is set (e.g., API already handles it)
    """
    # Skip if not a new user
    if not created:
        return

    # Skip if email already verified (e.g., admin marked it verified on creation)
    if instance.email_verified:
        return

    # Skip if flagged (API registration handles email itself)
    if getattr(instance, '_skip_verification_email', False):
        return

    # Import here to avoid circular imports
    from .redis_utils import VerificationTokenManager
    from Real_MFA.celery_tasks import send_verification_email

    try:
        # Generate and store token
        token = default_token_generator.make_token(instance)
        VerificationTokenManager.store_token(instance.id, token)

        # Send email task
        send_verification_email.delay(str(instance.id))
        logger.info("Verification email triggered via signal for user_id=%s", instance.id)
    except Exception as exc:
        logger.warning("Failed to send verification email via signal for user_id=%s: %s", instance.id, exc)


@receiver(pre_save, sender=User)
def detect_password_change(sender, instance, **kwargs):
    """Detect password changes and send notification"""
    if instance.pk:  # Only for existing users
        try:
            old_user = User.objects.get(pk=instance.pk)
            # Check if password changed
            if old_user.password != instance.password:
                # Mark for notification after save
                instance._password_changed = True
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def notify_password_changed(sender, instance, created, **kwargs):
    """Send notification when password is changed"""
    if not created and getattr(instance, '_password_changed', False):
        from notification.utils import notify_password_changed
        try:
            notify_password_changed(instance)
            logger.info(f"Password change notification sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send password change notification: {e}")
        # Clean up flag
        instance._password_changed = False


@receiver(pre_save, sender=User)
def detect_mfa_status_change(sender, instance, **kwargs):
    """Detect MFA status changes"""
    if instance.pk:  # Only for existing users
        try:
            old_user = User.objects.get(pk=instance.pk)
            # Check if MFA status changed
            if old_user.mfa_enabled != instance.mfa_enabled:
                instance._mfa_status_changed = True
                instance._old_mfa_enabled = old_user.mfa_enabled
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def notify_mfa_status_changed(sender, instance, created, **kwargs):
    """Send notification when MFA status is changed"""
    if not created and getattr(instance, '_mfa_status_changed', False):
        from notification.utils import notify_mfa_enabled, notify_mfa_disabled
        try:
            if instance.mfa_enabled:
                notify_mfa_enabled(instance, instance.mfa_method or 'TOTP')
                logger.info(f"MFA enabled notification sent to {instance.email}")
            else:
                notify_mfa_disabled(instance, getattr(instance, '_old_mfa_enabled', 'Unknown'))
                logger.info(f"MFA disabled notification sent to {instance.email}")
        except Exception as e:
            logger.error(f"Failed to send MFA status change notification: {e}")
        # Clean up flags
        instance._mfa_status_changed = False
        if hasattr(instance, '_old_mfa_enabled'):
            delattr(instance, '_old_mfa_enabled')


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save Profile when User is saved (if exists)"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(pre_save, sender=Profile)
def detect_profile_change(sender, instance, **kwargs):
    """Detect profile changes before save"""
    if instance.pk:
        try:
            old_profile = Profile.objects.get(pk=instance.pk)
            changed_fields = {}
            
            # Track specific fields
            tracked_fields = ['phone_number', 'date_of_birth', 'address_line1', 
                            'city', 'country', 'timezone', 'language', 'profile_visibility']
            
            for field in tracked_fields:
                old_value = getattr(old_profile, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changed_fields[field] = {
                        'old': str(old_value) if old_value else '',
                        'new': str(new_value) if new_value else ''
                    }
            
            # Store changed fields temporarily
            if changed_fields:
                instance._profile_changed_fields = changed_fields
        except Profile.DoesNotExist:
            pass


@receiver(post_save, sender=Profile)
def notify_profile_changed(sender, instance, created, **kwargs):
    """Send notification when profile is updated"""
    if not created and hasattr(instance, '_profile_changed_fields'):
        from notification.utils import notify_profile_changed
        try:
            # Get request from middleware if available
            request = getattr(instance, '_request', None)
            notify_profile_changed(instance.user, instance._profile_changed_fields, request)
            logger.info(f"Profile change notification sent to {instance.user.email}")
        except Exception as e:
            logger.error(f"Failed to send profile change notification: {e}")
        # Clean up temporary attribute
        if hasattr(instance, '_profile_changed_fields'):
            delattr(instance, '_profile_changed_fields')


