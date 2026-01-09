"""
URL configuration for Real_MFA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
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
