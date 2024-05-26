from django.urls import path
from django.views.i18n import JavaScriptCatalog

from django_otp_webauthn.views import (
    BeginCredentialAuthenticationView,
    BeginCredentialRegistrationView,
    CompleteCredentialAuthenticationView,
    CompleteCredentialRegistrationView,
)

app_name = "otp_webauthn"

urlpatterns = [
    path(
        "registration/begin/",
        BeginCredentialRegistrationView.as_view(),
        name="credential-registration-begin",
    ),
    path(
        "registration/complete/",
        CompleteCredentialRegistrationView.as_view(),
        name="credential-registration-complete",
    ),
    path(
        "authentication/begin/",
        BeginCredentialAuthenticationView.as_view(),
        name="credential-authentication-begin",
    ),
    path(
        "authentication/complete/",
        CompleteCredentialAuthenticationView.as_view(),
        name="credential-authentication-complete",
    ),
    path(
        "jsi18n/",
        JavaScriptCatalog.as_view(packages=["django_otp_webauthn"]),
        name="js-i18n-catalog",
    ),
]
