"""
Profile Serializers - User profile and account management
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from .models import User, Profile, PasswordHistory
from otp.utils import get_client_ip


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    
    class Meta:
        model = Profile
        fields = [
            'phone_number',
            'phone_verified',
            'date_of_birth',
            'avatar',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'country',
            'postal_code',
            'timezone',
            'language',
            'profile_visibility',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['phone_verified', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Combined user and profile serializer for GET /api/profile/me/"""
    profile = ProfileSerializer()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'email_verified',
            'mfa_enabled',
            'mfa_method',
            'last_login_at',
            'last_activity',
            'created_at',
            'profile',
        ]
        read_only_fields = [
            'id', 'email', 'role', 'email_verified', 
            'last_login_at', 'last_activity', 'created_at'
        ]


class UpdateProfileSerializer(serializers.Serializer):
    """Serializer for updating user profile - PUT /api/profile/me/"""
    
    # User fields
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False)
    
    # Profile fields
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, required=False)
    language = serializers.CharField(max_length=10, required=False)
    profile_visibility = serializers.ChoiceField(
        choices=['public', 'private', 'friends'],
        required=False
    )
    
    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def update(self, instance, validated_data):
        user = instance
        
        # Update user fields
        user_fields = ['first_name', 'last_name', 'username']
        for field in user_fields:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        user.save()
        
        # Update profile fields
        profile = user.profile
        profile_fields = [
            'phone_number', 'date_of_birth', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code', 'timezone', 'language',
            'profile_visibility'
        ]
        for field in profile_fields:
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        
        return user


class AccountDetailsSerializer(serializers.ModelSerializer):
    """Serializer for account security details - GET /api/profile/account/"""
    devices_count = serializers.SerializerMethodField()
    trusted_devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'role',
            'email_verified',
            'mfa_enabled',
            'mfa_method',
            'last_login_ip',
            'last_login_at',
            'failed_login_attempts',
            'account_locked_until',
            'password_changed_at',
            'require_password_change',
            'created_at',
            'last_activity',
            'devices_count',
            'trusted_devices_count',
        ]
    
    def get_devices_count(self, obj):
        return obj.devices.filter(is_deleted=False).count()
    
    def get_trusted_devices_count(self, obj):
        return obj.devices.filter(is_deleted=False, is_trusted=True).count()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password - POST /api/profile/change-password/"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        # Use Django's password validators
        validate_password(value, self.context['request'].user)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "New passwords do not match."
            })
        
        # Check password is not the same as current
        user = self.context['request'].user
        if user.check_password(attrs['new_password']):
            raise serializers.ValidationError({
                "new_password": "New password cannot be the same as current password."
            })
        
        # Check password history (last 5 passwords)
        recent_passwords = PasswordHistory.objects.filter(user=user).order_by('-created_at')[:5]
        for history in recent_passwords:
            if check_password(attrs['new_password'], history.password_hash):
                raise serializers.ValidationError({
                    "new_password": "You cannot reuse one of your last 5 passwords."
                })
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        request = self.context['request']
        
        # Save current password to history
        PasswordHistory.objects.create(
            user=user,
            password_hash=user.password,
            changed_from_ip=get_client_ip(request)
        )
        
        # Set new password
        user.set_password(self.validated_data['new_password'])
        user.password_changed_at = timezone.now()
        user.require_password_change = False
        user.save(update_fields=['password', 'password_changed_at', 'require_password_change'])
        
        # Revoke all other sessions for security (exclude current)
        from devices.models import Session
        
        # Get current session to exclude
        current_jti = getattr(request, 'auth', {})
        exclude_session_id = None
        if hasattr(current_jti, 'payload'):
            jti = current_jti.payload.get('jti')
            current_session = Session.objects.filter(
                user=user,
                token_jti=jti,
                is_active=True
            ).first()
            if current_session:
                exclude_session_id = current_session.id
        
        revoked_count = Session.revoke_all_for_user(
            user=user,
            reason='password_changed',
            exclude_session_id=exclude_session_id
        )
        
        return {
            'message': 'Password changed successfully.',
            'other_sessions_revoked': revoked_count
        }
