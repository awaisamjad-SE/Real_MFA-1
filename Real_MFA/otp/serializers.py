"""
OTP Serializers - Resend OTP for device verification
"""

from rest_framework import serializers
from django.utils import timezone
from accounts.models import User
from accounts.redis_utils import redis_client
from .models import OTP
from .utils import generate_otp_code, hash_otp, get_client_ip


class ResendDeviceOTPSerializer(serializers.Serializer):
    """
    Resend OTP for device verification
    Rate limited: 3 resends per 10 minutes, 60 second cooldown
    """
    user_id = serializers.UUIDField()
    fingerprint_hash = serializers.CharField(max_length=255)  # Required to identify device
    
    def validate(self, attrs):
        user_id = attrs.get('user_id')
        fingerprint_hash = attrs.get('fingerprint_hash')
        request = self.context.get('request')
        
        # Find user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Invalid user."})
        
        # Check for pending device verification (with fingerprint_hash)
        pending_key = f"pending_device_verification:{user_id}:{fingerprint_hash}"
        pending_otp_id = redis_client.get(pending_key)
        
        if not pending_otp_id:
            raise serializers.ValidationError({
                "error": "No pending device verification. Please login again."
            })
        
        # Check cooldown (60 seconds) - per device
        cooldown_key = f"device_otp_cooldown:{user_id}:{fingerprint_hash}"
        if redis_client.exists(cooldown_key):
            ttl = redis_client.ttl(cooldown_key)
            raise serializers.ValidationError({
                "error": f"Please wait {ttl} seconds before requesting another OTP."
            })
        
        # Check resend limit (3 per 10 minutes) - per device
        limit_key = f"device_otp_limit:{user_id}:{fingerprint_hash}"
        count = redis_client.get(limit_key)
        if count and int(count) >= 3:
            ttl = redis_client.ttl(limit_key)
            raise serializers.ValidationError({
                "error": f"Too many OTP requests. Try again in {ttl} seconds."
            })
        
        attrs['user'] = user
        attrs['fingerprint_hash'] = fingerprint_hash
        attrs['ip_address'] = get_client_ip(request)
        
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        fingerprint_hash = self.validated_data['fingerprint_hash']
        ip_address = self.validated_data['ip_address']
        
        # Set cooldown (60 seconds) - per device
        cooldown_key = f"device_otp_cooldown:{user.id}:{fingerprint_hash}"
        redis_client.setex(cooldown_key, 60, "1")
        
        # Increment resend count - per device
        limit_key = f"device_otp_limit:{user.id}:{fingerprint_hash}"
        count = redis_client.incr(limit_key)
        if count == 1:
            redis_client.expire(limit_key, 600)  # 10 minutes
        
        # Invalidate previous OTPs
        OTP.objects.filter(
            user=user,
            purpose='device_verification',
            is_used=False
        ).update(is_used=True)
        
        # Generate new OTP
        otp_code = generate_otp_code(6)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        otp = OTP.objects.create(
            user=user,
            code_hash=hash_otp(otp_code),
            purpose='device_verification',
            target=user.email,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        # Update pending verification reference (with fingerprint_hash)
        pending_key = f"pending_device_verification:{user.id}:{fingerprint_hash}"
        redis_client.setex(pending_key, 600, str(otp.id))
        
        # TODO: Send OTP via email
        # send_device_verification_email.delay(str(user.id), otp_code)
        
        remaining = 3 - int(redis_client.get(limit_key) or 0)
        
        return {
            'message': 'OTP resent successfully',
            'email_hint': f"{user.email[:3]}***@{user.email.split('@')[1]}",
            'expires_at': expires_at.isoformat(),
            'remaining_resends': remaining
        }
