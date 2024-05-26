from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django_otp_webauthn.utils import get_exempt_urls


class Enforce2FAVerificationMiddleware:
    """Middleware that enforces specific types of users to be verified using 2FA.

    It must be called after `django_otp.middleware.OTPMiddleware`
    """

    redirect_url = reverse_lazy("second-factor-verification")

    def __init__(self, get_response):
        self.get_response = get_response

        # Need to do this in the constructor to ensure the urls are resolvable
        self.ignore_urls = [
            reverse("second-factor-verification"),
            reverse("auth:logout"),
        ]
        self.ignore_urls += get_exempt_urls()

    def __call__(self, request):
        # Don't do anything if we are not enforcing 2FA verification
        if not getattr(settings, "ENFORCE_2FA_VERIFICATION", False):
            return self.get_response(request)

        # If you are not logged in, you don't need to verify 2FA
        if request.user.is_anonymous:
            return self.get_response(request)

        # Don't redirect on urls that should be ignored. Avoid redirect loops.
        if request.path in self.ignore_urls:
            return self.get_response(request)

        # Logged in users who already verified 2FA don't need to be redirected
        if request.user.is_verified():
            return self.get_response(request)

        # If you don't need to be verified, continue with the request
        if not self.require_2fa(user=request.user):
            return self.get_response(request)

        # Looks like we need to verify 2FA for the user
        return HttpResponseRedirect(redirect_to=self.redirect_url)

    def require_2fa(self, user):
        """Returns true if the user should be required to perform 2FA verification."""
        return True
