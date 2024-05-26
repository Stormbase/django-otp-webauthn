from functools import lru_cache
from logging import getLogger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import AbstractUser
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django_otp import login as otp_login
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
    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user()
        if not self.user:
            raise exceptions.UserDisabled()

        if not self.can_register(self.user):
            raise exceptions.RegistrationDisabled()
        return super().dispatch(request, *args, **kwargs)

    def get_user(self) -> AbstractUser:
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def can_register(self, user: AbstractUser) -> bool:
        if not user.is_active:
            return False
        return True


class AuthenticationCeremonyMixin:
    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user()
        if not self.can_authenticate(self.user):
            raise exceptions.AuthenticationDisabled()
        return super().dispatch(request, *args, **kwargs)

    def get_user(self) -> AbstractUser:
        if self.request.user.is_authenticated:
            return self.request.user
        return None

    def can_authenticate(self, user: AbstractUser) -> bool:
        if user and not user.is_active:
            return False
        return True


@method_decorator(never_cache, name="dispatch")
class BeginCredentialRegistrationView(RegistrationCeremonyMixin, APIView):
    """View for starting webauthn credential registration. Requires the user to be logged in.

    This view will return a JSON response with the options for the client to use to register a credential.
    """

    def post(self, *args, **kwargs):
        user = self.user
        provider = WebAuthnCredential.get_provider(request=self.request)
        data, state = provider.register_begin(user=user)

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
        user = self.user
        state = self.get_state()
        data = self.request.data

        provider = WebAuthnCredential.get_provider(request=self.request)

        logger = _get_pywebauthn_logger()
        with rewrite_exceptions(logger=logger):
            device = provider.register_complete(user=user, state=state, data=data)
        return Response(data={"id": device.pk}, content_type="application/json")


@method_decorator(never_cache, name="dispatch")
class BeginCredentialAuthenticationView(AuthenticationCeremonyMixin, APIView):
    """View for starting webauthn credential authentication. User does not necessarily need to be logged in.

    If the user is logged in, this view supplies more hints to the client about registered credentials.

    This view will return a JSON response with the options for the client to use to authenticate with a credential.
    """

    def post(self, *args, **kwargs):
        user = self.user

        provider = WebAuthnCredential.get_provider(request=self.request)
        require_user_verification = not bool(user)

        data, state = provider.authenticate_begin(user=user, require_user_verification=require_user_verification)
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

    def check_login_allowed(self, device: AbstractWebAuthnCredential) -> None:
        """Check if the user is allowed to log in using the device.

        This will raise:
         - ``PasswordlessLoginDisabled`` if there is no user logged in and
           ``OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN`` is False.
         - ``UserDisabled`` if the user associated with the device is not
           active.

        You can override this method to implement your own custom logic. If you
        do, you should raise an exception if the user is not allowed to log in.

        Args:
            device (AbstractWebAuthnCredential): The device the user is trying to log
            in with.
        """
        disallow_passwordless_login = not app_settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN
        if not device.confirmed:
            raise exceptions.CredentialDisabled()

        if self.get_user() is None and disallow_passwordless_login:
            raise exceptions.PasswordlessLoginDisabled()

        if not device.user.is_active:
            raise exceptions.UserDisabled()

    def complete_auth(self, device: AbstractWebAuthnCredential) -> AbstractUser:
        """Handle the completion of the authentication procedure.

        This method is called when a credential was successfully used and
        the user is allowed to log in. The user is logged in and marked as
        having passed verification.

        You may override this method to implement custom logic.
        """
        user = device.user
        if not self.request.user.is_authenticated:
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
        user = self.user
        state = self.get_state()
        data = self.request.data

        provider = WebAuthnCredential.get_provider(request=self.request)

        logger = _get_pywebauthn_logger()
        with rewrite_exceptions(logger=logger):
            device = provider.authenticate_complete(user=user, state=state, data=data)

        self.check_login_allowed(device)

        self.complete_auth(device)

        return Response(self.get_success_data(device))
