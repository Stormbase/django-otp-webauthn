import json
import logging
from base64 import b64decode, b64encode
from typing import TypedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.db.models import TextChoices
from django.http import Http404, JsonResponse
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View
from django_otp import login as otp_login

from otp_passkeys.conf import get_setting
from otp_passkeys.utils import get_passkey_model

UserPasskeyDevice = get_passkey_model()
User = get_user_model()


logger = logging.getLogger(__name__)


class ErrorCodes(TextChoices):
    NOT_FOUND = "not_found", _(
        "The passkey you are trying to authenticate with is not registered with this website.\n\nPerhaps it was removed? If this is the case, you should remove it from your stored passkeys."
    )
    NO_AUTH_STATE = "no_auth_state", _(
        "No authentication state found. Please begin authentication first."
    )
    LOGIN_NOT_ENABLED = "login_not_enabled", _(
        "Passwordless login is not enabled. \n\nYou must be logged in to complete this request."
    )
    UNHANDLED_ERROR = "unhandled_error", _(
        "An error occurred while processing the request. \n\nIf you are the site administrator, please check the server log for details."
    )


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class BeginPasskeyAuthenticationView(View):
    """View for starting passkey authentication.

    This view will return a JSON response with the options for the client to use to authenticate with a passkey.

    The `publicKey.user.id` and `publicKey.challenge` fields are base64 encoded to make them JSON serializable.
    """

    def post(self, request):
        options, state = UserPasskeyDevice.authenticate_begin(
            request=request,
            user=request.user,
        )
        request.session["otp_passkeys_authentication_state"] = state

        return JsonResponse(self.serialize(dict(options)))

    def serialize(self, options) -> dict:
        # We need to base64 encode the some binary data in the options to make it JSON serializable.
        opts = dict(options)
        opts["publicKey"]["challenge"] = b64encode(
            opts["publicKey"]["challenge"]
        ).decode("utf-8")

        # The begin authentication request may be anonymous, meaning there are no allowed credentials available.
        if "allowCredentials" in opts["publicKey"]:
            for i, cred in enumerate(opts["publicKey"]["allowCredentials"]):
                opts["publicKey"]["allowCredentials"][i]["id"] = b64encode(
                    cred["id"]
                ).decode("utf-8")

        return opts


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class CompletePasskeyAuthenticationView(View):
    """View for completing passkey authentication.

    This view expects a JSON body that closely resembles the attributes of the PublicKeyCredential interface as defined in the WebAuthn spec.

    The `rawId`, `response.clientDataJSON`, `response.signature` and `response.authenticatorData` fields are expected
    to be base64 encoded because they contain binary data, which cannot be represented in JSON.

    See https://www.w3.org/TR/webauthn-2/#iface-pkcredential
    """

    success_url_allowed_hosts = set()

    class DeserializedData(TypedDict):
        id: str
        rawId: bytes
        clientDataJSON: bytes
        client_data: dict
        authenticatorData: bytes
        signature: bytes
        userHandle: str
        type: str

    def deserialize(self, data: dict) -> DeserializedData:
        try:
            # Binary data is not valid JSON, thus it has been base64 encoded.
            data["rawId"] = b64decode(data["rawId"])
            data["response"]["clientDataJSON"] = b64decode(
                data["response"]["clientDataJSON"]
            )
            data["response"]["authenticatorData"] = b64decode(
                data["response"]["authenticatorData"]
            )
            data["response"]["signature"] = b64decode(data["response"]["signature"])
        except KeyError:
            return JsonResponse(
                {"success": False, "error_detail": "Missing required data"}, status=400
            )
        except ValueError:
            return JsonResponse(
                {"success": False, "error_detail": "Malformed data"}, status=400
            )
        return self.DeserializedData(
            id=data["id"],
            rawId=data["rawId"],
            # It is imperative that keep the clientDataJSON intact and make no attempt to deserialize it.
            # Any modification to clientDataJSON will invalidate the signature.
            clientDataJSON=data["response"]["clientDataJSON"],
            authenticatorData=data["response"]["authenticatorData"],
            signature=data["response"]["signature"],
            userHandle=data["response"].get("userHandle", None),
            type=data["type"],
        )

    def handle_complete_auth(self, request, device):
        """Handle the completion of the authentication procedure.

        This method is called when a passkey was successfully authenticated.
        The user is logged in and marked as having passed verification.
        """
        user = device.user
        if not request.user.is_authenticated:
            auth_login(request, user)

        # Mark the user as having passed verification
        otp_login(request, device)
        return user

    def get_success_data(self, *, user, redirect_url, device):
        return {
            "success": True,
            "persistent_id": device.persistent_id,
            "user": user.get_full_name() or user.get_username(),
            "redirect_url": redirect_url,
        }

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

    def get_default_redirect_url(self):
        """Return the default redirect URL."""
        return resolve_url(settings.LOGIN_REDIRECT_URL)

    def get_success_url(self):
        return self.get_redirect_url() or self.get_default_redirect_url()

    def post(self, request):
        # It is VITAL that we pop the state from the session before we do anything else.
        # We must not allow the state to be used more than once or we risk replay attacks.
        state = request.session.pop("otp_passkeys_authentication_state", None)

        if not state:
            return JsonResponse(
                {
                    "success": False,
                    "error_code": ErrorCodes.NO_AUTH_STATE.value,
                    "error_detail": ErrorCodes.NO_AUTH_STATE.label,
                },
                status=400,
            )

        data = json.loads(request.body)
        data = self.deserialize(data)

        user = request.user if request.user.is_authenticated else None

        try:
            device = UserPasskeyDevice.authenticate_complete(
                request=request,
                state=state,
                credential_id=data["rawId"],
                user=user,
                authenticator_data=data["authenticatorData"],
                signature=data["signature"],
                client_data=data["clientDataJSON"],
            )
        except UserPasskeyDevice.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "error_code": ErrorCodes.NOT_FOUND.value,
                    "error_detail": ErrorCodes.NOT_FOUND.label,
                },
                status=404,
            )
        # Unfortunately, the underlying python-fido2 library raises a ValueError for all errors.
        # We can't distinguish between different types of errors, so we have to catch all of them indiscriminately.
        except ValueError as e:
            logger.error("Error authenticating with passkey: %s", str(e))
            # Be vague about the error we return to the client to avoid leaking information that could be used to attack the system.
            return JsonResponse(
                {
                    "success": False,
                    "error_code": ErrorCodes.UNHANDLED_ERROR.value,
                    "error_detail": ErrorCodes.UNHANDLED_ERROR.label,
                },
                status=400,
            )

        disallow_passwordless_login = not get_setting(
            "OTP_PASSKEYS_ALLOW_PASSWORDLESS_LOGIN"
        )
        if user is None and disallow_passwordless_login:
            return JsonResponse(
                {
                    "success": False,
                    "error_code": ErrorCodes.LOGIN_NOT_ENABLED.value,
                    "error_detail": ErrorCodes.LOGIN_NOT_ENABLED.label,
                },
                status=403,
            )

        user = self.handle_complete_auth(request, device)

        redirect_url = self.get_success_url()

        return JsonResponse(
            self.get_success_data(user=user, redirect_url=redirect_url, device=device)
        )
