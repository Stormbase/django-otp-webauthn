from django.contrib.auth.urls import urlpatterns as auth_urls
from django.urls import include, path

from .admin import admin_site
from .views import IndexView, SecondFactorVerificationView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path(
        "verification/",
        SecondFactorVerificationView.as_view(),
        name="second-factor-verification",
    ),
    path("auth/", include((auth_urls, "auth"), namespace="auth")),
    path("admin/", admin_site.urls),
    path("webauthn/", include("django_otp_webauthn.urls", namespace="otp_webauthn")),
]
