from __future__ import annotations

from functools import lru_cache
from logging import getLogger

from django.conf import settings
from django.contrib.auth import authenticate as auth_authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.base_user import AbstractBaseUser
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django_otp import login as otp_login
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_otp_webauthn import exceptions
from django_otp_webauthn.models import AbstractWebAuthnCredential
from django_otp_webauthn.settings import app_settings
from django_otp_webauthn.utils import get_credential_model, rewrite_exceptions

WebAuthnCredential = get_credential_model()
User = get_user_model()


@lru_cache(maxsize=1)
def _get_pywebauthn_logger():
    logger_name = app_settings.OTP_WEBAUTHN_EXCEPTION_LOGGER_NAME
    if logger_name:
        return getLogger(logger_name)


class RegistrationCeremonyMixin:
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.check_can_register()
        return super().dispatch(request, *args, **kwargs)

    def get_user(self) -> AbstractBaseUser | None:
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def check_can_register(self):
        """Perform any necessary pre-checks to see if the registration ceremony can proceed."""
        user = self.get_user()
        # Only active users may attempt to register a new credential
        if user and not user.is_active:
            raise exceptions.UserDisabled()


class AuthenticationCeremonyMixin:
    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        self.check_can_authenticate()
        return super().dispatch(request, *args, **kwargs)

    def get_user(self) -> AbstractBaseUser | None:
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def check_can_authenticate(self):
        """Perform any necessary pre-checks to see if the authentication ceremony can proceed."""
        user = self.get_user()
        # In case we already have a user (scenario: webauthn used as a second factor only)
        # we allow the ceremony to proceed, as long as the user is active
        if user and user.is_active:
            return

        # In case we don't have a user (scenario: webauthn used as for passwordless login, no user logged in yet)
        disallow_passwordless_login = (
            not app_settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN
        )
        if self.get_user() is None and disallow_passwordless_login:
            raise exceptions.PasswordlessLoginDisabled()


@method_decorator(never_cache, name="dispatch")
class BeginCredentialRegistrationView(RegistrationCeremonyMixin, APIView):
    """View for starting webauthn credential registration. Requires the user to be logged in.

    This view will return a JSON response with the options for the client to use to register a credential.
    """

    def post(self, *args, **kwargs):
        user = self.get_user()
        helper = WebAuthnCredential.get_webauthn_helper(request=self.request)
        data, state = helper.register_begin(user=user)

        self.request.session["otp_webauthn_register_state"] = state

        return Response(data=data, content_type="application/json")


@method_decorator(never_cache, name="dispatch")
class CompleteCredentialRegistrationView(RegistrationCeremonyMixin, APIView):
    """View for completing webauthn credential registration. Requires the user to be logged in and to have started the registration.

    This view accepts client data about the registered credential, validates it, and saves the credential to the database.
    """

    def get_state(self):
        """Retrieve the registration state."""

        state = self.request.session.pop("otp_webauthn_register_state", None)
        # Ensure to persist the session after popping the state, so even if an
        # exception is raised, the state is _never_ reused.
        self.request.session.save()
        if not state:
            raise exceptions.InvalidState()
        return state

    def post(self, *args, **kwargs):
        user = self.get_user()
        state = self.get_state()
        data = self.request.data

        helper = WebAuthnCredential.get_webauthn_helper(request=self.request)

        logger = _get_pywebauthn_logger()
        with rewrite_exceptions(logger=logger):
            device = helper.register_complete(user=user, state=state, data=data)
        return Response(data={"id": device.pk}, content_type="application/json")


@method_decorator(never_cache, name="dispatch")
class BeginCredentialAuthenticationView(AuthenticationCeremonyMixin, APIView):
    """View for starting webauthn credential authentication. User does not necessarily need to be logged in.

    If the user is logged in, this view supplies more hints to the client about registered credentials.

    This view will return a JSON response with the options for the client to use to authenticate with a credential.
    """

    def post(self, *args, **kwargs):
        user = self.get_user()

        helper = WebAuthnCredential.get_webauthn_helper(request=self.request)
        require_user_verification = not bool(user)

        data, state = helper.authenticate_begin(
            user=user, require_user_verification=require_user_verification
        )
        self.request.session["otp_webauthn_authentication_state"] = state

        return Response(data=data, content_type="application/json")


@method_decorator(never_cache, name="dispatch")
class CompleteCredentialAuthenticationView(AuthenticationCeremonyMixin, APIView):
    """View for completing webauthn credential authentication. Requires the user to be
    logged in and to have started the authentication.

    This view accepts client data about the registered webauthn , validates it,
    and logs the user in.
    """

    def get_state(self):
        """Retrieve the authentication state."""
        # It is VITAL that we pop the state from the session before we do anything else.
        # We must not allow the state to be used more than once or we risk replay attacks.

        state = self.request.session.pop("otp_webauthn_authentication_state", None)
        # Ensure to persist the session after popping the state, so even if an
        # exception is raised, the state is _never_ reused.
        self.request.session.save()

        if not state:
            raise exceptions.InvalidState()
        return state

    def check_device_usable(self, device: AbstractWebAuthnCredential) -> None:
        """Check if this device may be used to login.

        This will raise:
         - ``CredentialDisabled`` if `device.confirmed=False`.
         - ``UserDisabled`` if the user associated with the device is not
           active.

        You can override this method to implement your own custom logic. If you
        do, you should raise an exception if this device may not be used to
        login.

        Args:
            device (AbstractWebAuthnCredential): The device the user is trying to log
            in with.
        """
        if not device.confirmed:
            raise exceptions.CredentialDisabled()

        if not device.user.is_active:
            raise exceptions.UserDisabled()

    def complete_auth(self, device: AbstractWebAuthnCredential) -> AbstractBaseUser:
        """Handle the completion of the authentication procedure.

        This method is called when a credential was successfully used and
        the user is allowed to log in. The user is logged in and marked as
        having passed verification.

        You may override this method to implement custom logic.
        """
        if self.request.user.is_authenticated:
            user = device.user
        else:
            user = auth_authenticate(self.request, webauthn_credential=device)
            auth_login(self.request, user)

        # Mark the user as having passed verification
        otp_login(self.request, device)

    success_url_allowed_hosts = set()

    def get_success_data(self, device: AbstractWebAuthnCredential):
        data = {
            "id": device.pk,
            "redirect_url": self.get_success_url(),
        }

        return data

    def get_success_url_allowed_hosts(self):
        return {self.request.get_host(), *self.success_url_allowed_hosts}

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.GET.get("next")
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ""

    def get_success_url(self):
        """Where to send the user after a successful login."""
        return self.get_redirect_url() or resolve_url(settings.LOGIN_REDIRECT_URL)

    def post(self, *args, **kwargs):
        user = self.get_user()
        state = self.get_state()
        data = self.request.data

        helper = WebAuthnCredential.get_webauthn_helper(request=self.request)

        logger = _get_pywebauthn_logger()
        with rewrite_exceptions(logger=logger):
            device = helper.authenticate_complete(user=user, state=state, data=data)

        self.check_device_usable(device)

        self.complete_auth(device)

        return Response(self.get_success_data(device))
