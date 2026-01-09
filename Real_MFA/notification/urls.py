"""
Notification URLs - Email verification endpoints
"""

from django.urls import path
from . import views

urlpatterns = [
    # Email verification
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-verification-email/', views.resend_verification_email, name='resend-verification-email'),
]