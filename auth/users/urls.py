from __future__ import annotations

from django.urls import path
from .views import (
    MeView,
    RefreshTokenView,
    LoginView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    PhoneCheckView,
    PhoneVerificationRequestView,
    PhoneVerificationConfirmView,
    PasswordSetView,
    MyBranchesView,
    SwitchBranchView,
)


urlpatterns = [
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("password/reset/request-otp/", PasswordResetRequestView.as_view(), name="auth-password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
    # Redesigned flow
    path("phone/check/", PhoneCheckView.as_view(), name="auth-phone-check"),
    path("phone/verification/request/", PhoneVerificationRequestView.as_view(), name="auth-phone-verification-request"),
    path("phone/verification/confirm/", PhoneVerificationConfirmView.as_view(), name="auth-phone-verification-confirm"),
    path("password/set/", PasswordSetView.as_view(), name="auth-password-set"),
    path("branches/mine/", MyBranchesView.as_view(), name="auth-my-branches"),
    path("branch/switch/", SwitchBranchView.as_view(), name="auth-branch-switch"),
]
