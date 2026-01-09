"""
Profile URLs - User profile and account management
"""

from django.urls import path
from .profile_views import (
    ProfileMeView,
    AccountDetailsView,
    ChangePasswordView,
)

urlpatterns = [
    # Profile endpoints
    path('me/', ProfileMeView.as_view(), name='profile-me'),
    path('account/', AccountDetailsView.as_view(), name='account-details'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]
