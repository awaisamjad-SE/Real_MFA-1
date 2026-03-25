from rest_framework import serializers
from django.conf import settings
from .models import User, Profile
from .validators import (
    validate_unique_username, validate_unique_email, validate_phone_format,
    validate_fingerprint, get_ip_from_ipinfo, get_location_from_ip
)
from .redis_utils import VerificationTokenManager, ResendLimiter, CooldownManager
from devices.models import Device
from Real_MFA.celery_tasks import send_verification_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import logging

logger = logging.getLogger(__name__)


def _dispatch_verification_email(user_id: str) -> None:
    """Send verification email sync by default; async only when explicitly enabled."""
    if getattr(settings, 'SEND_VERIFICATION_EMAIL_ASYNC', False):
        send_verification_email.delay(user_id)
    else:
        send_verification_email.apply(args=[user_id])


def _short_exc(exc: Exception) -> str:
    msg = str(exc)
    msg = " ".join(msg.split())
    if len(msg) > 180:
        return msg[:177] + "..."
    return msg


class DeviceDataSerializer(serializers.Serializer):
    """Nested serializer for device information"""
    fingerprint_hash = serializers.CharField(max_length=255, min_length=10, validators=[validate_fingerprint])
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(choices=['mobile', 'tablet', 'desktop', 'unknown'], default='unknown')
    browser = serializers.CharField(max_length=100, required=False, allow_blank=True)
    os = serializers.CharField(max_length=100, required=False, allow_blank=True)


class RegisterSerializer(serializers.Serializer):
    """User registration with device fingerprinting and async email verification"""
    username = serializers.CharField(max_length=150, validators=[validate_unique_username])
    email = serializers.EmailField(validators=[validate_unique_email])
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['user', 'manager', 'admin'], default='user')
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True, validators=[validate_phone_format])
    device = DeviceDataSerializer()

    def validate(self, attrs):
        # Check passwords match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Extract data
        device_data = validated_data.pop('device')
        phone_number = validated_data.pop('phone_number', None)
        password = validated_data.pop('password')
        validated_data.pop('password2')
        
        # Create user with email_verified=False (default)
        # Set flag so signal does NOT send email (we handle it explicitly below)
        user = User(email_verified=False, **validated_data)
        user._skip_verification_email = True
        user.set_password(password)
        user.save()
        
        # Update profile with phone
        if phone_number:
            user.profile.phone_number = phone_number
            user.profile.save()
        
        # Get location data from IP
        location_data = get_location_from_ip()
        
        # Create device with location data
        Device.objects.create(
            user=user,
            ip_address=location_data['ip'],
            country=location_data['country'],
            city=location_data['city'],
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            is_verified=True,
            is_trusted=True,
            **device_data
        )
        
        # Generate and store verification token
        token = default_token_generator.make_token(user)
        VerificationTokenManager.store_token(user.id, token)
        
        # Send verification email.
        # Default is synchronous so delivery works even without a worker.
        try:
            _dispatch_verification_email(str(user.id))
            logger.info(
                "Verification email dispatched for user_id=%s (async=%s)",
                str(user.id),
                getattr(settings, 'SEND_VERIFICATION_EMAIL_ASYNC', False),
            )
        except Exception as exc:
            logger.warning(
                "Failed to send verification email for user_id=%s: %s",
                str(user.id),
                _short_exc(exc),
            )
        
        return user
