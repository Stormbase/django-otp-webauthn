from django.urls import path

from otp_passkeys.views import (
    BeginPasskeyAuthenticationView,
    BeginPasskeyRegistrationView,
    CompletePasskeyAuthenticationView,
    CompletePasskeyRegistrationView,
)

app_name = "otp_passkeys"

urlpatterns = [
    path(
        "registration/begin/",
        BeginPasskeyRegistrationView.as_view(),
        name="passkey-registration-begin",
    ),
    path(
        "registration/complete/",
        CompletePasskeyRegistrationView.as_view(),
        name="passkey-registration-complete",
    ),
    path(
        "authentication/begin/",
        BeginPasskeyAuthenticationView.as_view(),
        name="passkey-authentication-begin",
    ),
    path(
        "authentication/complete/",
        CompletePasskeyAuthenticationView.as_view(),
        name="passkey-authentication-complete",
    ),
]
