import json
from base64 import b64decode, b64encode
from typing import Literal, Optional, Tuple, TypedDict

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

from otp_passkeys.utils import get_passkey_model

UserPasskeyDevice = get_passkey_model()
User = get_user_model()


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class BeginPasskeyRegistrationView(LoginRequiredMixin, View):
    """View for starting a passkey registration. Requires the user to be logged in.

    This view will return a JSON response with the options for the client to use to register a passkey.

    The `publicKey.user.id` and `publicKey.challenge` fields are base64 encoded to make them JSON serializable.
    """

    def post(self, request):
        options, state = UserPasskeyDevice.register_begin(
            request=request, user=request.user
        )
        request.session["otp_passkeys_register_state"] = state
        return JsonResponse(self.serialize(dict(options)))

    def serialize(self, options) -> dict:
        # We need to base64 encode the some binary data in the options to make it JSON serializable.
        opts = dict(options)
        opts["publicKey"]["user"]["id"] = b64encode(
            opts["publicKey"]["user"]["id"]
        ).decode("utf-8")
        opts["publicKey"]["challenge"] = b64encode(
            opts["publicKey"]["challenge"]
        ).decode("utf-8")

        for i, cred in enumerate(opts["publicKey"]["excludeCredentials"]):
            opts["publicKey"]["excludeCredentials"][i]["id"] = b64encode(
                cred["id"]
            ).decode("utf-8")
        return opts


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class CompletePasskeyRegistrationView(LoginRequiredMixin, View):
    """View for completing a passkey registration. Requires the user to be logged in.

    This view expects a JSON body that closely resembles the attributes of the PublicKeyCredential interface as defined in the WebAuthn spec.

    The `rawId`, `response.clientDataJSON` and `response.attestationObject` fields are expected to be base64 encoded
    because they contain binary data, which cannot be represented in JSON.

    See https://www.w3.org/TR/webauthn-2/#iface-pkcredential
    """

    class DeserializedData(TypedDict):
        id: str
        rawId: bytes
        clientDataJSON: bytes
        authenticatorAttachment: Optional[str]
        client_data: dict
        attestationObject: bytes
        transports: list[str]
        type: str

    def deserialize(self, data: dict) -> DeserializedData:
        try:
            # Binary data is not valid JSON, thus it has been base64 encoded.
            data["rawId"] = b64decode(data["rawId"])
            data["response"]["clientDataJSON"] = b64decode(
                data["response"]["clientDataJSON"]
            )
            data["response"]["attestationObject"] = b64decode(
                data["response"]["attestationObject"]
            )

            client_data = json.loads(data["response"]["clientDataJSON"])
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
            clientDataJSON=data["response"]["clientDataJSON"],
            client_data=client_data,
            attestationObject=data["response"]["attestationObject"],
            transports=data["transports"],
            authenticatorAttachment=data["authenticatorAttachment"],
            type=data["type"],
        )

    def post(self, request):
        state = request.session.pop("otp_passkeys_register_state", None)
        if not state:
            return JsonResponse(
                {
                    "success": False,
                    "error_detail": "No registration state found. Please begin registration first.",
                },
                status=400,
            )

        data = json.loads(request.body)
        data = self.deserialize(data)

        try:
            key = UserPasskeyDevice.register_complete(
                request=request,
                state=state,
                user=request.user,
                client_data=data["client_data"],
                attestation=data["attestationObject"],
                authenticator_attachment=data["authenticatorAttachment"],
                transports=data["transports"],
            )
        except ValueError as e:
            return JsonResponse({"success": False, "error_detail": str(e)}, status=400)

        return JsonResponse({"success": True, "persistent_id": key.persistent_id})
