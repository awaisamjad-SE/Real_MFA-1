"""
URL configuration for Real_MFA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from otp.urls import totp_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Accounts: Login, Logout, Registration
    path('api/', include('accounts.urls')),
    
    # Profile: User profile and account management
    path('api/profile/', include('accounts.profile_urls')),
    
    # Password: Forgot/Reset password
    path('api/password/', include('accounts.password_urls')),
    
    # Devices: Device verification and management
    path('api/devices/', include('devices.urls')),
    
    # OTP: OTP resend
    path('api/otp/', include('otp.urls')),
    
    # TOTP/MFA: TOTP setup, verify, disable, backup codes
    path('api/totp/', include(totp_urlpatterns)),
    
    # Notifications: Email verification
    path('api/notifications/', include('notification.urls')),
    
    # Admin: Admin dashboard APIs
    path('api/admin-dashboard/', include('accounts.admin_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
