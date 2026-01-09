"""
Authentication Serializers - Login and Logout only
Device verification moved to devices app
OTP resend moved to otp app
"""

import json
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .redis_utils import redis_client
from .validators import get_location_from_ip
from devices.models import Device, Session
from otp.models import OTP
from otp.utils import generate_otp_code, hash_otp, get_client_ip


class DeviceLoginSerializer(serializers.Serializer):
    """Device info for login request"""
    fingerprint_hash = serializers.CharField(max_length=255, min_length=10)
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=['mobile', 'tablet', 'desktop', 'unknown'],
        default='unknown'
    )
    browser = serializers.CharField(max_length=100, required=False, allow_blank=True)
    os = serializers.CharField(max_length=100, required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    """
    Login serializer with device fingerprinting and MFA support
    
    Scenarios:
    1. Known trusted device -> Return JWT tokens immediately
    2. New/untrusted device -> Send OTP for device verification
    3. Account locked -> Reject login
    4. Email not verified -> Reject login
    """
    identifier = serializers.CharField(
        max_length=255,
        help_text="Email or username"
    )
    password = serializers.CharField(write_only=True)
    device = DeviceLoginSerializer()
    
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        device_data = attrs.get('device')
        request = self.context.get('request')
        
        # Find user by email or username
        user = None
        if '@' in identifier:
            # Looks like an email
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        
        if user is None:
            # Try username
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                pass
        
        if user is None:
            raise serializers.ValidationError({
                "error": "Invalid credentials."
            })
        
        # Check if account is locked
        if user.is_account_locked():
            lock_time = user.account_locked_until
            remaining = (lock_time - timezone.now()).seconds // 60
            raise serializers.ValidationError({
                "error": f"Account locked. Try again in {remaining} minutes.",
                "locked_until": lock_time.isoformat()
            })
        
        # Check email verification
        if not user.email_verified:
            raise serializers.ValidationError({
                "error": "Email not verified. Please verify your email first.",
                "code": "email_not_verified"
            })
        
        # Authenticate user (password check) - use email for backend
        authenticated_user = authenticate(
            request=request,
            username=user.email,
            password=password
        )
        
        if not authenticated_user:
            # Increment failed login attempts
            user.increment_failed_login(max_attempts=5, lockout_duration=30)
            remaining_attempts = 5 - user.failed_login_attempts
            raise serializers.ValidationError({
                "error": "Invalid credentials.",
                "remaining_attempts": max(0, remaining_attempts)
            })
        
        # Reset failed login attempts on successful password check
        user.reset_failed_login()
        
        # Check device
        fingerprint = device_data.get('fingerprint_hash')
        ip_address = get_client_ip(request)
        
        # Try to find existing device
        device = Device.objects.filter(
            user=user,
            fingerprint_hash=fingerprint,
            is_deleted=False
        ).first()
        
        attrs['user'] = user
        attrs['device_obj'] = device
        attrs['ip_address'] = ip_address
        
        return attrs
    
    def create_tokens(self, user):
        """Create JWT tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            # Store REFRESH token's jti (not access token's) because:
            # - Access token jti changes on every refresh
            # - Refresh token jti stays constant for the session lifetime
            'jti': str(refresh.payload.get('jti'))
        }
    
    def create_session(self, user, device, tokens, location_data, request):
        """Create a new session record"""
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        Session.objects.create(
            user=user,
            token_jti=tokens['jti'],  # This is now refresh token's jti
            fingerprint_hash=device.fingerprint_hash if device else '',
            ip_address=location_data['ip'],
            user_agent=user_agent,
            device_name=device.device_name if device else '',
            device_type=device.device_type if device else 'unknown',
            browser=device.browser if device else '',
            os=device.os if device else '',
            country=location_data['country'],
            city=location_data['city'],
            expires_at=timezone.now() + timezone.timedelta(days=7)  # Match JWT expiry
        )
    
    def send_device_otp(self, user, ip_address):
        """Generate and send OTP for device verification"""
        # Invalidate any existing device verification OTPs
        OTP.objects.filter(
            user=user,
            purpose='device_verification',
            is_used=False
        ).update(is_used=True)
        
        # Generate new OTP
        otp_code = generate_otp_code(6)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Create OTP record
        otp = OTP.objects.create(
            user=user,
            code_hash=hash_otp(otp_code),
            purpose='device_verification',
            target=user.email,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        # Store pending device verification in Redis (expires in 10 minutes)
        # Use fingerprint_hash to allow multiple devices to verify simultaneously
        fingerprint_hash = self.validated_data['device']['fingerprint_hash']
        pending_key = f"pending_device_verification:{user.id}:{fingerprint_hash}"
        redis_client.setex(pending_key, 600, str(otp.id))
        
        # Send OTP via email (async Celery task)
        from Real_MFA.celery_tasks import send_device_verification_otp
        send_device_verification_otp.delay(str(user.id), otp_code)
        
        return {
            'otp_id': str(otp.id),
            'expires_at': expires_at.isoformat()
        }
    
    def save(self):
        user = self.validated_data['user']
        device = self.validated_data.get('device_obj')
        device_data = self.validated_data['device']
        ip_address = self.validated_data['ip_address']
        request = self.context.get('request')
        
        # Get location data from IP
        location_data = get_location_from_ip(ip_address)
        
        # =====================================================================
        # CHECK MFA REQUIREMENT FIRST (before any login scenario)
        # =====================================================================
        # If MFA is enabled, ALWAYS require TOTP verification (no skipping)
        if user.mfa_enabled:
            # Store pending MFA login in Redis
            fingerprint_hash = device_data['fingerprint_hash']
            pending_mfa_key = f"pending_mfa_login:{user.id}:{fingerprint_hash}"
            redis_client.setex(pending_mfa_key, 600, json.dumps({
                'user_id': str(user.id),
                'fingerprint_hash': fingerprint_hash,
                'device_data': device_data,
                'ip_address': location_data['ip'],
                'location': location_data
            }))
            
            return {
                'status': 'mfa_required',
                'message': 'MFA verification required. Please enter your TOTP code.',
                'user_id': str(user.id),
                'fingerprint_hash': fingerprint_hash,
                'mfa_method': user.mfa_method,
                'email_hint': f"{user.email[:3]}***@{user.email.split('@')[1]}"
            }
        
        # =====================================================================
        # SCENARIO 1: Known trusted device - login immediately (MFA not enabled)
        # =====================================================================
        if device and device.is_trusted and not device.is_trust_expired():
            # Update device last used info and location
            device.total_logins += 1
            device.last_ip = location_data['ip']
            device.country = location_data['country']
            device.city = location_data['city']
            device.latitude = location_data['latitude']
            device.longitude = location_data['longitude']
            device.save(update_fields=['total_logins', 'last_ip', 'last_used_at', 'country', 'city', 'latitude', 'longitude'])
            
            # Update user login info
            user.last_login_ip = location_data['ip']
            user.last_login_at = timezone.now()
            user.last_activity = timezone.now()
            user.save(update_fields=['last_login_ip', 'last_login_at', 'last_activity'])
            
            tokens = self.create_tokens(user)
            
            # Create session record
            self.create_session(user, device, tokens, location_data, request)
            
            return {
                'status': 'success',
                'message': 'Login successful',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'role': user.role
                },
                'device': {
                    'id': str(device.id),
                    'name': device.device_name,
                    'is_trusted': device.is_trusted
                },
                'tokens': {
                    'access': tokens['access'],
                    'refresh': tokens['refresh']
                }
            }
        
        # =====================================================================
        # SCENARIO 2: Known verified but not trusted device
        # =====================================================================
        if device and device.is_verified and not device.is_trusted:
            # Update device info and location
            device.total_logins += 1
            device.last_ip = location_data['ip']
            device.country = location_data['country']
            device.city = location_data['city']
            device.latitude = location_data['latitude']
            device.longitude = location_data['longitude']
            device.save(update_fields=['total_logins', 'last_ip', 'last_used_at', 'country', 'city', 'latitude', 'longitude'])
            
            # Update user login info
            user.last_login_ip = location_data['ip']
            user.last_login_at = timezone.now()
            user.last_activity = timezone.now()
            user.save(update_fields=['last_login_ip', 'last_login_at', 'last_activity'])
            
            tokens = self.create_tokens(user)
            
            # Create session record
            self.create_session(user, device, tokens, location_data, request)
            
            return {
                'status': 'success',
                'message': 'Login successful (device not trusted - MFA may be required)',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'role': user.role
                },
                'device': {
                    'id': str(device.id),
                    'name': device.device_name,
                    'is_trusted': device.is_trusted
                },
                'tokens': {
                    'access': tokens['access'],
                    'refresh': tokens['refresh']
                }
            }
        
        # Scenario 3: New or unverified device - require OTP verification
        # Store device data in Redis for later creation (include location)
        # Use fingerprint_hash to allow multiple devices to verify simultaneously
        fingerprint_hash = device_data['fingerprint_hash']
        pending_device_key = f"pending_device_data:{user.id}:{fingerprint_hash}"
        redis_client.setex(pending_device_key, 600, json.dumps({
            'fingerprint_hash': device_data['fingerprint_hash'],
            'device_name': device_data.get('device_name', ''),
            'device_type': device_data.get('device_type', 'unknown'),
            'browser': device_data.get('browser', ''),
            'os': device_data.get('os', ''),
            'ip_address': location_data['ip'],
            'country': location_data['country'],
            'city': location_data['city'],
            'latitude': location_data['latitude'],
            'longitude': location_data['longitude']
        }))
        
        otp_info = self.send_device_otp(user, ip_address)
        
        return {
            'status': 'device_verification_required',
            'message': 'New device detected. Please verify with the OTP sent to your email.',
            'user_id': str(user.id),
            'fingerprint_hash': fingerprint_hash,  # Required for verification
            'email_hint': f"{user.email[:3]}***@{user.email.split('@')[1]}",
            'otp_expires_at': otp_info['expires_at']
        }


class MFAVerifyLoginSerializer(serializers.Serializer):
    """
    Verify MFA (TOTP) code during login to complete authentication
    """
    user_id = serializers.UUIDField()
    fingerprint_hash = serializers.CharField(max_length=255)
    totp_code = serializers.CharField(min_length=6, max_length=6, required=False)
    backup_code = serializers.CharField(max_length=10, required=False)
    trust_device = serializers.BooleanField(default=False)
    trust_days = serializers.IntegerField(default=30, min_value=1, max_value=90)
    
    def validate(self, attrs):
        import pyotp
        from hashlib import sha256
        from otp.models import TOTPDevice, BackupCode
        
        user_id = attrs.get('user_id')
        fingerprint_hash = attrs.get('fingerprint_hash')
        totp_code = attrs.get('totp_code')
        backup_code = attrs.get('backup_code')
        
        # Must provide either TOTP code or backup code
        if not totp_code and not backup_code:
            raise serializers.ValidationError({
                "error": "Please provide either TOTP code or backup code."
            })
        
        # Find user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "Invalid user."})
        
        # Check for pending MFA login
        pending_key = f"pending_mfa_login:{user_id}:{fingerprint_hash}"
        pending_data = redis_client.get(pending_key)
        
        if not pending_data:
            raise serializers.ValidationError({
                "error": "No pending MFA verification. Please login again."
            })
        
        pending_login = json.loads(pending_data)
        
        # Verify TOTP code
        if totp_code:
            if not hasattr(user, 'totp_device') or not user.totp_device.is_verified:
                raise serializers.ValidationError({
                    "error": "TOTP not configured for this user."
                })
            
            totp = pyotp.TOTP(user.totp_device.secret)
            if not totp.verify(totp_code, valid_window=1):
                raise serializers.ValidationError({
                    "error": "Invalid TOTP code."
                })
            
            # Update TOTP device stats
            user.totp_device.last_used_at = timezone.now()
            user.totp_device.total_verifications += 1
            user.totp_device.save(update_fields=['last_used_at', 'total_verifications'])
        
        # Verify backup code
        elif backup_code:
            code_hash = sha256(backup_code.upper().encode()).hexdigest()
            backup = BackupCode.objects.filter(
                user=user,
                code_hash=code_hash,
                is_used=False
            ).first()
            
            if not backup:
                raise serializers.ValidationError({
                    "error": "Invalid or already used backup code."
                })
            
            # Mark backup code as used
            backup.is_used = True
            backup.used_at = timezone.now()
            backup.used_from_ip = pending_login.get('ip_address')
            backup.save(update_fields=['is_used', 'used_at', 'used_from_ip'])
        
        attrs['user'] = user
        attrs['pending_login'] = pending_login
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        pending_login = self.validated_data['pending_login']
        fingerprint_hash = self.validated_data['fingerprint_hash']
        trust_device = self.validated_data.get('trust_device', False)
        trust_days = self.validated_data.get('trust_days', 30)
        request = self.context.get('request')
        
        location_data = pending_login.get('location', {})
        device_data = pending_login.get('device_data', {})
        
        # Find or create device
        device, created = Device.objects.get_or_create(
            user=user,
            fingerprint_hash=fingerprint_hash,
            defaults={
                'device_name': device_data.get('device_name', ''),
                'device_type': device_data.get('device_type', 'unknown'),
                'browser': device_data.get('browser', ''),
                'os': device_data.get('os', ''),
                'ip_address': location_data.get('ip', ''),
                'country': location_data.get('country', ''),
                'city': location_data.get('city', ''),
                'is_verified': True,
                'verified_at': timezone.now()
            }
        )
        
        if not created:
            # Update existing device
            device.last_ip = location_data.get('ip', '')
            device.country = location_data.get('country', '')
            device.city = location_data.get('city', '')
            device.total_logins += 1
            device.is_deleted = False
            device.save(update_fields=['last_ip', 'country', 'city', 'total_logins', 'last_used_at', 'is_deleted'])
        
        # Trust device if requested (allows skipping MFA next time)
        if trust_device:
            device.mark_trusted(days=trust_days)
        
        # Update user login info
        user.last_login_ip = location_data.get('ip', '')
        user.last_login_at = timezone.now()
        user.last_activity = timezone.now()
        user.save(update_fields=['last_login_ip', 'last_login_at', 'last_activity'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'jti': str(refresh.payload.get('jti'))
        }
        
        # Create session record
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        Session.objects.create(
            user=user,
            token_jti=tokens['jti'],
            fingerprint_hash=fingerprint_hash,
            ip_address=location_data.get('ip', ''),
            user_agent=user_agent,
            device_name=device.device_name,
            device_type=device.device_type,
            browser=device.browser,
            os=device.os,
            country=location_data.get('country', ''),
            city=location_data.get('city', ''),
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        # Clean up Redis
        redis_client.delete(f"pending_mfa_login:{user.id}:{fingerprint_hash}")
        
        return {
            'status': 'success',
            'message': 'MFA verified. Login successful.',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'role': user.role
            },
            'device': {
                'id': str(device.id),
                'name': device.device_name,
                'is_trusted': device.is_trusted,
                'is_new': created
            },
            'tokens': {
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }
        }


class LogoutSerializer(serializers.Serializer):
    """
    Logout user by blacklisting refresh token
    """
    refresh = serializers.CharField()
    
    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")
        return value
    
    def save(self):
        try:
            self.token.blacklist()
            return {'message': 'Logged out successfully'}
        except Exception:
            raise serializers.ValidationError("Failed to logout. Token may already be blacklisted.")
