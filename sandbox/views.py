from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django_otp_webauthn.utils import get_credential_model

WebAuthnCredential = get_credential_model()
User = get_user_model()


class IndexView(TemplateView):
    template_name = "sandbox/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["2fa_verified"] = self.request.user.is_verified()
        return ctx


class SecondFactorVerificationView(LoginRequiredMixin, TemplateView):
    template_name = "sandbox/second_factor_verification.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        return ctx
