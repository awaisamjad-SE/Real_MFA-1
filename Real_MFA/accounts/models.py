# ============================================================================
# ACCOUNTS APP - models.py
# Core user authentication and account management
# ============================================================================

from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


# ---------------------------
# Abstract Base Models
# ---------------------------
class TimeStampedModel(models.Model):
    """Abstract model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Soft delete the instance"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore soft deleted instance"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


# ---------------------------
# User Model
# ---------------------------
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'user')
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('role') != 'admin':
            raise ValueError("Superuser must have role='admin'.")

        return self._create_user(email, username, password, **extra_fields)


class User(AbstractUser, SoftDeleteModel):
    """
    Custom user model with role-based access control
    Security: Uses email as primary identifier, supports MFA, tracks security events
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
    ]
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', db_index=True)
    
    # Security Fields
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False, db_index=True)
    mfa_method = models.CharField(
        max_length=20, 
        choices=[('totp', 'TOTP'), ('email', 'Email'), ('sms', 'SMS')],
        default='totp'
    )
    
    # Account Security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    require_password_change = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Use email as login identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['email_verified', 'is_active']),
            models.Index(fields=['mfa_enabled']),
        ]
        permissions = [
            ('can_view_audit_logs', 'Can view audit logs'),
            ('can_manage_users', 'Can manage users'),
            ('can_access_admin_panel', 'Can access admin panel'),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to set permissions based on role"""
        # Track password changes
        if self.pk:
            old_user = User.objects.filter(pk=self.pk).first()
            if old_user and old_user.password != self.password:
                self.password_changed_at = timezone.now()
        
        # Set permissions based on role
        if self.role == 'admin':
            self.is_superuser = True
            self.is_staff = True
        elif self.role == 'manager':
            self.is_superuser = False
            self.is_staff = True
        else:  # user
            self.is_superuser = False
            self.is_staff = False
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self, max_attempts=5, lockout_duration=30):
        """Increment failed login attempts and lock if exceeded"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lock_account(lockout_duration)
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.last_login_ip = None
        self.save(update_fields=['failed_login_attempts'])


# ---------------------------
# Profile Model
# ---------------------------
class Profile(TimeStampedModel):
    """
    Extended user profile information
    Separated from User model for better data organization
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    phone_number = models.CharField(
        max_length=15, 
        null=True, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    phone_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Privacy Settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[('public', 'Public'), ('private', 'Private'), ('friends', 'Friends Only')],
        default='private'
    )
    
    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
    
    def __str__(self):
        return f"Profile of {self.user.email}"


# ---------------------------
# Password History Model
# ---------------------------
class PasswordHistory(TimeStampedModel):
    """
    Track password history to prevent password reuse
    Security: Prevents users from reusing recent passwords
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=255)
    changed_from_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'password_history'
        verbose_name = 'Password History'
        verbose_name_plural = 'Password Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Password history for {self.user.email} at {self.created_at}"


# ============================================================================
# END OF FILE
# ============================================================================
