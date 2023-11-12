import hashlib
from typing import Any, List, Optional, Tuple, TypedDict

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from fido2 import cbor
from fido2.server import Fido2Server
from fido2.webauthn import (
    AttestationConveyancePreference,
    AttestationObject,
    AttestedCredentialData,
    AuthenticatorData,
    CollectedClientData,
    CredentialCreationOptions,
    CredentialRequestOptions,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from precis_i18n import get_profile

from otp_passkeys.utils import get_passkey_model, get_setting

# The WebAuthn spec states[^1] that we SHOULD enforce the rules defined in RFC 8266[^2].
# PRECIS will help us do that by providing a profile that enforces the rules for us.
# [1]: https://www.w3.org/TR/webauthn-2/#dom-publickeycredentialuserentity-displayname
# [2]: https://datatracker.ietf.org/doc/html/rfc8266
nickname = get_profile("NicknameCaseMapped")

# The WebAuthn spec states[^3] that we SHOULD enforce the rules defined in RFC 8264[^4].
# PRECIS will help us do that by providing a profile that enforces the rules for us.
# [3]: https://www.w3.org/TR/webauthn-2/#dom-publickeycredentialentity-name
# [4]: https://datatracker.ietf.org/doc/html/rfc8264
username = get_profile("UsernameCasePreserved")

User = get_user_model()


class RegistrationData(TypedDict):
    aaguid: bytes
    credential_id: bytes
    cose_public_key: bytes
    flags: int


class FidoProvider:
    """A wrapper class around `fido2.webauthn`

    You may subclass this class to customize behavior, but there is NO GUARANTEE that future versions of this library will remain compatible with your subclass.

    Please consider raising an issue if you need to subclass this class to customize behavior. We may be able to support your use case.
    """

    def get_relying_party(self, request: HttpRequest) -> PublicKeyCredentialRpEntity:
        # The name of the relying party. It is often displayed to the user during passkey registration.
        # Could be the name of your website or company. Like "Acme Corporation".
        name = get_setting(
            "OTP_PASSKEYS_RP_NAME",
            raise_exception=True,
            callable_args={"request": request},
        )

        # The domain for the relying party. The WebAuthn spec calls this the RP ID.
        # https://www.w3.org/TR/webauthn-2/#rp-id
        domain = get_setting(
            "OTP_PASSKEYS_RP_DOMAIN",
            raise_exception=True,
            callable_args={"request": request},
        )

        return PublicKeyCredentialRpEntity(
            name=name,
            id=domain,
        )

    def get_server(self, request: HttpRequest) -> Fido2Server:
        """Get the Fido2Server instance.

        You may override this method to customize server initialization and parameters.
        """
        rp = self.get_relying_party(request)
        attestation = self.get_attestation_conveyance_preference(request)

        return Fido2Server(rp=rp, attestation=attestation)

    def get_discoverable_credentials_preference(
        self, request: HttpRequest
    ) -> ResidentKeyRequirement:
        """Determines if we'd like the authenticator to store the Passkey in authenticator memory
        instead of encrypting and storing it on the the server. When stored on the server, the private key is encrypted
        and encoded in the credential ID in an opaque format.

        **Note**: this is sometimes referred to as "resident keys". Resident keys mean the same thing as "discoverable credentials".
        Resident keys are an outdated term that was used in older  WebAuthn spec but still lives on in some places.
        This library attempts to use the term "discoverable credentials" consistently.

        Storing the Passkey in the authenticator makes it possible to do full passwordless authentication.
        Without the relying party having to provide all credential IDs for a given user.
        Providing credentials to unauthenticated users leaks information about the existence of the user
        and their registered passkeys.

        By default, this is set to 'preferred', which means we'd like the authenticator to store
        the private key + metadata in persistent authenticator memory if possible.

        Some devices - like security keys - have limited memory and can't store the private key and associated metadata
        for dozens of credentials. Thus is why we don't set this to 'required' by default.

        By default this is set to "preferred". This means we'd like the authenticator to store the private key
        and associated metadata in authenticator memory if possible, but it's not required.

        For source and for more information about discoverable credentials, see:
        - https://www.w3.org/TR/webauthn-3/#client-side-discoverable-public-key-credential-source
        - https://developers.yubico.com/WebAuthn/WebAuthn_Developer_Guide/Resident_Keys.html

        """
        return ResidentKeyRequirement.PREFERRED

    def get_attestation_conveyance_preference(
        self, request: HttpRequest
    ) -> AttestationConveyancePreference:
        """Determines if we'd like the authenticator to send an attestation statement.

        By default this is set to "none", which means we don't want the authenticator to send an attestation statement.

        The attestation statement is a signed statement from the authenticator that can be used to verify the authenticity of the authenticator.
        It can help answer the following question: "is this authenticator really from the manufacturer it claims to be from?".

        An example use case of this could be to ensure only authenticators from a certain manufacturer are allowed to register - if that were a requirement for your application.

        Please note that attestation statements don't all follow the same format. There are different formats for different authenticator manufacturers.
        By verifying statements, you are limiting the authenticators that can be used to register and you may end up breaking compatibility with future authenticators.

        Given the above caveats and challenging implementation, this package DOES NOT SUPPORT VERIFYING ATTESTATION STATEMENTS. Which is why we set this to "none" by default.

        For more information about attestation, see:
        - https://www.w3.org/TR/webauthn-2/#attestation-conveyance
        - https://www.w3.org/TR/webauthn-2/#sctn-attestation
        - https://developers.yubico.com/WebAuthn/WebAuthn_Developer_Guide/Attestation.html
        """
        return AttestationConveyancePreference.NONE

    def get_credential_display_name(self, request: HttpRequest, user: User) -> str:
        """Get the display name for the credential.

        This is used to display a name during registration and authentication.

        The default implementation calls User.get_full_name() and falls back to User.get_username().
        """
        return user.get_full_name() or user.get_username()

    def get_credential_name(self, request: HttpRequest, user: User) -> str:
        """Get the name for the credential.

        This is used to display the user's name during registration and authentication.

        The default implementation calls User.get_username()
        """
        return user.get_username()

    def register_begin(
        self,
        *,
        request: HttpRequest,
        user: User,
        credentials: List[PublicKeyCredentialDescriptor] = list(),
    ) -> Tuple[CredentialCreationOptions, Any]:
        """Start the registration process for a user.

        Args:
            request: The request object.
            user: The user that is attempting to register.
            credentials: A list of previously registered credentials. This is used to prevent users from registering the same credential multiple times.

        Returns:
            A tuple (options, state) containing the credential creation options to be passed to the client and the state of the server.

        You must ensure to persist the state because it is needed to complete the registration process.
        """

        server = self.get_server(request)

        PasskeyModel = get_passkey_model()

        # Enforce the rules defined in RFC 8266.
        display_name = nickname.enforce(
            PasskeyModel.get_credential_display_name(request, user)
        )
        # Enforce the rules defined in RFC 8264.
        name = username.enforce(self.get_credential_name(request, user))

        # Must be unique and must not contain personally identifiable information according to the WebAuthn spec.

        # https://www.w3.org/TR/webauthn-3/#user-handle
        # Must be unique per user, be 64 bytes at maximum, and not contain personally identifiable information.
        # We use the hash of the primary key of the user model as the user handle because the primary key is guaranteed to be unique.
        # It is also not personally identifiable information because it is an opaque value that is not derived from any user input.
        user_handle = hashlib.sha256(bytes(user.pk)).digest()

        user_entity = PublicKeyCredentialUserEntity(
            id=user_handle,
            name=name,
            display_name=display_name,
        )

        options, state = server.register_begin(
            user=user_entity,
            credentials=credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key_requirement=self.get_discoverable_credentials_preference(
                request
            ),
        )

        return options, state

    def register_complete(
        self, *, request: HttpRequest, state: Any, client_data: dict, attestation: bytes
    ) -> RegistrationData:
        """Complete the registration process for a user.

        You must call this method to verify the registration data returned by the client.

        Args:
            request: The request object.
            state: The state of the server. This is returned by `register_begin`.
            client_data: The client data returned by the client. Expects a dict with at least `type`, `challenge`, and `origin` keys. Optionally a `crossOrigin` key. See https://www.w3.org/TR/webauthn-2/#dictdef-collectedclientdata
            attestation: The attestation object returned by the client. Expects bytes.
        Returns:
            A dict containing the registration data.
        """

        server = self.get_server(request)

        client_data = CollectedClientData.create(
            type=client_data.get("type"),
            challenge=client_data.get("challenge"),
            origin=client_data.get("origin"),
            cross_origin=client_data.get("crossOrigin", False),
        )
        attestation_object = AttestationObject(attestation)

        auth_data = server.register_complete(
            state, client_data=client_data, attestation_object=attestation_object
        )

        aaguid = bytes(auth_data.credential_data.aaguid)
        public_key = cbor.encode(auth_data.credential_data.public_key)
        credential_id = auth_data.credential_data.credential_id

        return RegistrationData(
            aaguid=aaguid,
            # The flags indicate what capabilities the authenticator has in addition to some metadata.
            flags=attestation_object.auth_data.flags,
            credential_id=credential_id,
            cose_public_key=public_key,
        )

    def authenticate_begin(
        self,
        *,
        request: HttpRequest,
        require_user_verification: bool,
        user: User = None,
        allowed_credentials: Optional[List[PublicKeyCredentialDescriptor]] = None,
    ) -> Tuple[CredentialRequestOptions, Any]:
        """Start the authentication process for a user.

        Args:
            request: The request object.
            user: The user that is attempting to authenticate.
            allowed_credentials: A list of allowed credentials to include in the response.

        Returns:
            A tuple (options, state) containing the credential request options to be passed to the client and the state of the server.
        """

        server = self.get_server(request)

        kwargs = {}
        if allowed_credentials:
            kwargs["credentials"] = allowed_credentials

        kwargs["user_verification"] = (
            UserVerificationRequirement.REQUIRED
            if require_user_verification
            else UserVerificationRequirement.DISCOURAGED
        )

        options, state = server.authenticate_begin(**kwargs)
        return options, state

    def authenticate_complete(
        self,
        *,
        request: HttpRequest,
        state: Any,
        user: User = None,
        client_data: bytes,
        credential_id: bytes,
        signature: bytes,
        authenticator_data: bytes,
        credentials: List[PublicKeyCredentialDescriptor],
    ) -> AttestedCredentialData:
        """Complete the authentication process for a user.

        You must call this method to verify the attestation returned by the client.

        Args:
            request: The request object.
            state: The state of the server. This is returned by `authenticate_begin`.
            user: The user that is attempting to verify using their passkey. This can be None if the user is not yet logged in.
            client_data: The client data returned by the client. Expects bytes.
            credential_id: The credential ID the client is trying to authenticate with. Expects bytes.
            signature: The signature created by the client. Expects bytes.
            authenticator_data: The authenticator data created by the client. Expects bytes.
            credentials: The credentials that will be used to check the signature. Expects PublicKeyCredentialDescriptor objects.
        """

        server = self.get_server(request)

        client_data = CollectedClientData(client_data)
        auth_data = AuthenticatorData(authenticator_data)

        # This may raise exceptions if:
        # - the challenge is invalid
        # - the origin is invalid
        # - the signature is invalid
        # - the RP hash is invalid
        # - the user verification requirement is not satisfied
        # - the user presence requirement is not satisfied

        attested_credential_data = server.authenticate_complete(
            state=state,
            client_data=client_data,
            credential_id=credential_id,
            auth_data=auth_data,
            signature=signature,
            # The list of credentials that will be used to verify the signature.
            # Typically only one credential is passed, because we already know which
            # credential the user is trying to authenticate with based on the credential ID.
            # The fido2 library expects that we pass a list of credentials, so we comply with that expectation.
            credentials=credentials,
        )

        return attested_credential_data
