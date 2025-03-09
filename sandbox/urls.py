from django.contrib.auth.urls import urlpatterns as auth_urls
from django.urls import include, path

from django_otp_webauthn.views import WellKnownWebAuthnView

from .admin import admin_site
from .views import IndexView, LoginWithPasskeyView, SecondFactorVerificationView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login-passkey/", LoginWithPasskeyView.as_view(), name="login-passkey"),
    path(
        "verification/",
        SecondFactorVerificationView.as_view(),
        name="second-factor-verification",
    ),
    path("auth/", include((auth_urls, "auth"), namespace="auth")),
    path("admin/", admin_site.urls),
    path("webauthn/", include("django_otp_webauthn.urls", namespace="otp_webauthn")),
    path(".well-known/webauthn", WellKnownWebAuthnView.as_view()),
]
