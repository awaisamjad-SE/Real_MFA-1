"""
OTP URLs - OTP and TOTP management endpoints
"""

from django.urls import path
from . import views
from . import totp_views

urlpatterns = [
    # OTP - Resend OTP for device verification
    path('resend-device/', views.resend_device_otp, name='resend-device-otp'),
]

# TOTP URLs (moved to separate path in main urls.py)
totp_urlpatterns = [
    # TOTP Setup and Verification
    path('setup/', totp_views.setup_totp, name='totp-setup'),
    path('verify/', totp_views.verify_totp, name='totp-verify'),
    path('disable/', totp_views.disable_totp, name='totp-disable'),
    
    # Backup Codes
    path('regenerate-backup-codes/', totp_views.regenerate_backup_codes, name='regenerate-backup-codes'),
    
    # MFA Status
    path('status/', totp_views.mfa_status, name='mfa-status'),
]
