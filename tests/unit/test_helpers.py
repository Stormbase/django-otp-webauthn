import json

import pytest
from django.http import HttpRequest
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    COSEAlgorithmIdentifier,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from django_otp_webauthn.exceptions import CredentialNotFound
from django_otp_webauthn.helpers import WebAuthnHelper
from django_otp_webauthn.models import WebAuthnCredential
from tests.factories import WebAuthnCredentialFactory


@pytest.fixture
def helper(rf):
    return WebAuthnHelper(rf.get("/"))


# Dummy callable. Needs to be at an importable location to be useful.
def dummy_rp_callable(request):  # noqa
    assert isinstance(request, HttpRequest)
    return request.GET.get("rp")


def test_helper_generate_challenge(helper):
    challenge = helper.generate_challenge()
    assert isinstance(challenge, bytes)

    # The challenge should be at least 16 bytes long
    assert len(challenge) >= 16

    # The challenges should be unique - no replays
    challenges = [helper.generate_challenge() for _ in range(20)]
    assert len(set(challenges)) == len(challenges)


def test_helper_get_relying_party_domain__from_static_value(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "example.com"
    assert helper.get_relying_party_domain() == "example.com"


def test_helper_get_relying_party_domain__from_callable(rf, settings):
    request = rf.get("https://example.com?rp=needle")
    helper = WebAuthnHelper(request)

    # Lets test a custom callable that returns the rp id from the query string
    settings.OTP_WEBAUTHN_RP_ID_CALLABLE = "tests.unit.test_helpers.dummy_rp_callable"
    assert helper.get_relying_party_domain() == "needle"


def test_helper_get_relying_party_name__from_static_value(helper, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    assert helper.get_relying_party_name() == "Acme Inc."


def test_helper_get_relying_party_name__from_callable(rf, settings):
    request = rf.get("https://example.com?rp=needle")
    helper = WebAuthnHelper(request)

    # Lets test a custom callable that returns the rp id from the query string
    settings.OTP_WEBAUTHN_RP_NAME_CALLABLE = "tests.unit.test_helpers.dummy_rp_callable"
    assert helper.get_relying_party_name() == "needle"


def test_helper_get_relying_party_entity(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "example.com"
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    entity = helper.get_relying_party()
    assert entity.id == "example.com"
    assert entity.name == "Acme Inc."


def test_helper_get_discoverable_credentials_preference(helper, settings):
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    assert (
        helper.get_discoverable_credentials_preference()
        is ResidentKeyRequirement.REQUIRED
    )

    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    assert (
        helper.get_discoverable_credentials_preference()
        is ResidentKeyRequirement.PREFERRED
    )


def test_helper_get_attestation_conveyance_preference(helper):
    assert (
        helper.get_attestation_conveyance_preference()
        == AttestationConveyancePreference.NONE
    )


def test_helper_get_authenticator_attachment_preference(helper):
    assert helper.get_authenticator_attachment_preference() is None


def test_helper_get_credential_display_name(helper, user_in_memory, mocker):
    user = user_in_memory
    user.username = "johndoe"
    user.first_name = "John"
    user.last_name = "Doe"

    # If the user has a full name, it should be used
    assert helper.get_credential_display_name(user) == "John Doe (johndoe)"

    # We are being naughty (don't tell Santa) and remove the get_full_name
    # method from the user. We'll pretend this is a custom user model based on
    # AbstractBaseUser that does not implement get_full_name.
    mock_user = mocker.Mock(wraps=user)
    del mock_user.get_full_name

    # In the absence of a full name, the username should be used
    assert helper.get_credential_display_name(mock_user) == "johndoe"


def test_helper_get_credential_name(helper, user_in_memory):
    user_in_memory.username = "johndoe"
    assert helper.get_credential_name(user_in_memory) == "johndoe"


def test_helper_get_unique_anonymous_user_id(helper, user_in_memory):
    user_in_memory.id = 123
    id_hash = helper.get_unique_anonymous_user_id(user_in_memory)

    assert isinstance(id_hash, bytes)
    # Must not be longer than 64 bytes, requirement of the WebAuthn spec
    assert len(id_hash) <= 64
    # 123 -> sha256 -> hex
    assert (
        id_hash.hex()
        == "409a7f83ac6b31dc8c77e3ec18038f209bd2f545e0f4177c2e2381aa4e067b49"
    )


def test_helper_get_user_entity(helper, user_in_memory):
    user_in_memory.pk = 123
    user_in_memory.username = "johndoe"
    user_in_memory.first_name = "John"
    user_in_memory.last_name = "Doe"
    user_entity = helper.get_user_entity(user_in_memory)

    assert (
        user_entity.id.hex()
        == "409a7f83ac6b31dc8c77e3ec18038f209bd2f545e0f4177c2e2381aa4e067b49"
    )
    assert user_entity.name == "johndoe"
    assert user_entity.display_name == "John Doe (johndoe)"


def test_helper_get_supported_key_algorithms(helper, settings):
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = None
    # Special case: indicating to defer to whatever the py_webauthn library defaults are
    assert helper.get_supported_key_algorithms() is None

    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [
        COSEAlgorithmIdentifier.ECDSA_SHA_256.value,
        COSEAlgorithmIdentifier.ECDSA_SHA_512.value,
        COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256.value,
    ]

    assert helper.get_supported_key_algorithms() == [
        COSEAlgorithmIdentifier.ECDSA_SHA_256,
        COSEAlgorithmIdentifier.ECDSA_SHA_512,
        COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
    ]

    # Invalid algorithm
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [0]
    with pytest.raises(ValueError):
        helper.get_supported_key_algorithms()


def test_helper_get_allowed_origins(helper, settings):
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["https://example.com"]
    assert helper.get_allowed_origins() == ["https://example.com"]


def test_helper_get_registration_extensions(helper):
    extensions = helper.get_registration_extensions()
    assert isinstance(extensions, dict)

    # Default extension should be set
    assert extensions["credProps"] is True

    # The extensions should be JSON serializable
    assert json.dumps(helper.get_registration_extensions())


def test_helper_get_registration_state(helper):
    creation_options = {
        "challenge": b"challenge",
        "authenticatorSelection": {
            "userVerification": UserVerificationRequirement.REQUIRED.value
        },
    }
    state = helper.get_registration_state(creation_options)
    assert isinstance(state, dict)

    assert state["challenge"] == b"challenge"
    assert state["require_user_verification"] is True

    creation_options = {
        "challenge": b"challenge",
        "authenticatorSelection": {
            "userVerification": UserVerificationRequirement.PREFERRED.value
        },
    }
    state = helper.get_registration_state(creation_options)
    assert state["require_user_verification"] is False


def test_helper_get_authentication_extensions(helper):
    extensions = helper.get_authentication_extensions()
    assert isinstance(extensions, dict)

    assert extensions == {}


@pytest.mark.django_db
def test_helper_get_generate_registration_options_kwargs(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "example.com"
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = None

    credential = WebAuthnCredentialFactory(user=user)

    # There is an additional credential in the database belonging to another user
    WebAuthnCredentialFactory()

    # Get the kwargs and check that they are as expected
    kwargs = helper.get_generate_registration_options_kwargs(user=user)

    assert kwargs["attestation"] == helper.get_attestation_conveyance_preference()

    assert isinstance(kwargs["authenticator_selection"], AuthenticatorSelectionCriteria)
    assert (
        kwargs["authenticator_selection"].resident_key
        == helper.get_discoverable_credentials_preference()
    )
    assert (
        kwargs["authenticator_selection"].user_verification
        == UserVerificationRequirement.PREFERRED
    )
    assert kwargs["authenticator_selection"].require_resident_key is False

    # Confidence check the challenge - does this look like a challenge?
    assert isinstance(kwargs["challenge"], bytes)
    assert len(kwargs["challenge"]) >= 16

    # Only the user's registered credentials should be excluded. Other users' credentials should not appear here.
    assert len(kwargs["exclude_credentials"]) == 1

    # The credential should be excluded
    assert kwargs["exclude_credentials"][0].id == credential.credential_id

    # The relying party ID and name should be set
    assert kwargs["rp_id"] == helper.get_relying_party_domain()
    assert kwargs["rp_name"] == helper.get_relying_party_name()

    # The user's display name, id and name should be set
    assert kwargs["user_display_name"] == helper.get_credential_display_name(user)
    assert kwargs["user_id"] == helper.get_unique_anonymous_user_id(user)
    assert kwargs["user_name"] == helper.get_credential_name(user)

    # A timeout should be set
    assert isinstance(kwargs["timeout"], int)

    # We did not set any supported algorithms, so it should not appear in the kwargs
    assert "supported_algorithms" not in kwargs

    # Now we set some supported algorithms, and they should appear in the kwargs
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [-7]
    kwargs = helper.get_generate_registration_options_kwargs(user=user)
    assert kwargs["supported_pub_key_algs"] == [-7]


@pytest.mark.django_db
def test_helper_register_begin(helper, credential, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_DOMAIN = "example.com"
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = None
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    user = credential.user
    data, state = helper.register_begin(user=user)

    # Check data
    assert "rp" in data
    assert "name" in data["rp"]
    assert "id" in data["rp"]

    assert "user" in data
    assert "id" in data["user"]
    assert "name" in data["user"]
    assert "displayName" in data["user"]

    assert "challenge" in data
    assert "pubKeyCredParams" in data
    assert isinstance(data["pubKeyCredParams"], list)
    for param in data["pubKeyCredParams"]:
        assert param["type"] == "public-key"
        assert "alg" in param

    assert "timeout" in data
    assert "excludeCredentials" in data
    assert isinstance(data["excludeCredentials"], list)
    assert len(data["excludeCredentials"]) == 1
    assert "id" in data["excludeCredentials"][0]

    assert data["attestation"] == helper.get_attestation_conveyance_preference().value

    assert "authenticatorSelection" in data
    assert data["authenticatorSelection"] == {
        "residentKey": "preferred",
        "requireResidentKey": False,
        "userVerification": "preferred",
    }

    # Check state
    assert state["challenge"] == data["challenge"]
    assert state["require_user_verification"] is False


@pytest.mark.django_db
def test_helper_register_complete__happy(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    state = {
        "challenge": "gKlAk5mA10Fkzx35WddzRi8rKtKrSQx16_u-rw6EEs2VhBVJPqdQzEJxyGsCL5NRZ24mpLZwyyjqT_kcRJ61xQ",
        "require_user_verification": False,
    }
    data = {
        "id": "2bDv5PTpXNnah2WEZ1tBxIVcdCqTyKiYL04qepxPbyI",
        "rawId": "2bDv5PTpXNnah2WEZ1tBxIVcdCqTyKiYL04qepxPbyI",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAQAAAAAAAAAAAAAAAAAAAAAAINmw7-T06VzZ2odlhGdbQcSFXHQqk8iomC9OKnqcT28ipQECAyYgASFYIF6L2zKFU9a07dAupm0EE1NSNfBoeYGHTlKSd3mjbj1kIlggeFXz9JtP5n8_EItpP8OkmRd--RgJ-1ThixABoo3AJsA",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiZ0tsQWs1bUExMEZrengzNVdkZHpSaThyS3RLclNReDE2X3Utcnc2RUVzMlZoQlZKUHFkUXpFSnh5R3NDTDVOUloyNG1wTFp3eXlqcVRfa2NSSjYxeFEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["usb"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEXovbMoVT1rTt0C6mbQQTU1I18Gh5gYdOUpJ3eaNuPWR4VfP0m0_mfz8Qi2k_w6SZF375GAn7VOGLEAGijcAmwA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAQAAAAAAAAAAAAAAAAAAAAAAINmw7-T06VzZ2odlhGdbQcSFXHQqk8iomC9OKnqcT28ipQECAyYgASFYIF6L2zKFU9a07dAupm0EE1NSNfBoeYGHTlKSd3mjbj1kIlggeFXz9JtP5n8_EItpP8OkmRd--RgJ-1ThixABoo3AJsA",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": True}},
        "authenticatorAttachment": "cross-platform",
    }

    credential = helper.register_complete(user=user, data=data, state=state)

    assert isinstance(credential, WebAuthnCredential)

    assert credential.user == user
    assert (
        credential.credential_id_sha256
        == "d9099c12116f8e7d1b00d76936e2e8d49f01830cfd8523b89f812bd3df6c88de"
    )
    assert credential.aaguid == "00000000-0000-0000-0000-000000000000"

    assert credential.confirmed is True
    assert credential.sign_count == 1
    assert credential.backup_eligible is False
    assert credential.backup_state is False
    assert credential.last_used_at is None

    # The sample response has replied to the credProps extension
    assert credential.discoverable is True

    assert credential.attestation is not None
    assert credential.attestation.fmt == "none"


@pytest.mark.django_db
def test_helper_register_complete__credprops_extension_ignored(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    state = {
        "challenge": "_hnZe9LwvbGW0VhYe_Mw3sQyCtfJ1VPpq3DXtDaDnyJcKS8enG2WqolNwrtLDakQukbDuFpG15qRal1MEWy6Tw",
        "require_user_verification": False,
    }
    data = {
        "id": "BA5bsX5mOSL74AaDLLIOWdHEi2M",
        "rawId": "BA5bsX5mOSL74AaDLLIOWdHEi2M",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NZAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAQOW7F-Zjki--AGgyyyDlnRxItjpQECAyYgASFYIPdhxX3SIszua-7unjoIJx7vbdDj_kYWFdpEuZMTEaNSIlgg3bRBVy43HV4PmkIHc9wYMTkJtACxA4_eNs35Xd6Vnns",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiX2huWmU5THd2YkdXMFZoWWVfTXczc1F5Q3RmSjFWUHBxM0RYdERhRG55SmNLUzhlbkcyV3FvbE53cnRMRGFrUXVrYkR1RnBHMTVxUmFsMU1FV3k2VHciLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAifQ",
            "transports": ["internal"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE92HFfdIizO5r7u6eOggnHu9t0OP-RhYV2kS5kxMRo1LdtEFXLjcdXg-aQgdz3BgxOQm0ALEDj942zfld3pWeew",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NZAAAAAAAAAAAAAAAAAAAAAAAAAAAAFAQOW7F-Zjki--AGgyyyDlnRxItjpQECAyYgASFYIPdhxX3SIszua-7unjoIJx7vbdDj_kYWFdpEuZMTEaNSIlgg3bRBVy43HV4PmkIHc9wYMTkJtACxA4_eNs35Xd6Vnns",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "platform",
    }

    credential = helper.register_complete(user=user, data=data, state=state)

    assert isinstance(credential, WebAuthnCredential)
    assert credential.user == user
    assert credential.backup_eligible is True
    assert credential.backup_state is True

    # The sample response did not reply to the credProps extension so it should be None
    assert credential.discoverable is None


@pytest.mark.django_db
def test_helper_register_complete__unsupported_algorithm_used(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [-257]

    state = {
        "challenge": "gKlAk5mA10Fkzx35WddzRi8rKtKrSQx16_u-rw6EEs2VhBVJPqdQzEJxyGsCL5NRZ24mpLZwyyjqT_kcRJ61xQ",
        "require_user_verification": False,
    }
    # This response uses a COSE algorithm that is not supported by the server
    data = {
        "id": "2bDv5PTpXNnah2WEZ1tBxIVcdCqTyKiYL04qepxPbyI",
        "rawId": "2bDv5PTpXNnah2WEZ1tBxIVcdCqTyKiYL04qepxPbyI",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAQAAAAAAAAAAAAAAAAAAAAAAINmw7-T06VzZ2odlhGdbQcSFXHQqk8iomC9OKnqcT28ipQECAyYgASFYIF6L2zKFU9a07dAupm0EE1NSNfBoeYGHTlKSd3mjbj1kIlggeFXz9JtP5n8_EItpP8OkmRd--RgJ-1ThixABoo3AJsA",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiZ0tsQWs1bUExMEZrengzNVdkZHpSaThyS3RLclNReDE2X3Utcnc2RUVzMlZoQlZKUHFkUXpFSnh5R3NDTDVOUloyNG1wTFp3eXlqcVRfa2NSSjYxeFEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["usb"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEXovbMoVT1rTt0C6mbQQTU1I18Gh5gYdOUpJ3eaNuPWR4VfP0m0_mfz8Qi2k_w6SZF375GAn7VOGLEAGijcAmwA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAQAAAAAAAAAAAAAAAAAAAAAAINmw7-T06VzZ2odlhGdbQcSFXHQqk8iomC9OKnqcT28ipQECAyYgASFYIF6L2zKFU9a07dAupm0EE1NSNfBoeYGHTlKSd3mjbj1kIlggeFXz9JtP5n8_EItpP8OkmRd--RgJ-1ThixABoo3AJsA",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": True}},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidRegistrationResponse):
        helper.register_complete(user=user, data=data, state=state)


@pytest.mark.django_db
def test_helper_register_complete__invalid_challenge(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    state = {
        "challenge": "C5-M005a0ZvhiJSTyX38-sY0knREgF-wn4WCNMXUus3osBxh7GSlOZtQ9yE3cw49DUcheIHSW8bprNRuJcz7gA",
        "require_user_verification": True,
    }
    data = {
        "id": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "rawId": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiQzUtTTAwNWEwWnZoaUpTVHlYMzgtc1kwa25SRWdGLXduNFdDTk1YVXVzM29zQnhoN0dTbE9adFE5eUUzY3c0OURVY2hlSUhTVzhicHJOUnVKY3o3Z0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["nfc"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED-ztBRiOqHd9nVuLaXFJofd5ttVPW4o8n8VV5ycJ3LxGec0gzEWC3ZbOrO7oqUnx-iOxWslk9xUiUcNJZEAWFA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": False}},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidRegistrationResponse):
        helper.register_complete(user=user, data=data, state=state)


@pytest.mark.django_db
def test_helper_register_complete__invalid_rp_id(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "invalid_id"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    state = {
        "challenge": "C5-M005a0ZvhiJSTyX38-sY0knREgF-wn4WCNMXUus3osBxh7GSlOZtQ9yE3cw49DUcheIHSW8bprNRuJcz7gA",
        "require_user_verification": True,
    }
    data = {
        "id": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "rawId": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiQzUtTTAwNWEwWnZoaUpTVHlYMzgtc1kwa25SRWdGLXduNFdDTk1YVXVzM29zQnhoN0dTbE9adFE5eUUzY3c0OURVY2hlSUhTVzhicHJOUnVKY3o3Z0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["nfc"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED-ztBRiOqHd9nVuLaXFJofd5ttVPW4o8n8VV5ycJ3LxGec0gzEWC3ZbOrO7oqUnx-iOxWslk9xUiUcNJZEAWFA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": False}},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidRegistrationResponse):
        helper.register_complete(user=user, data=data, state=state)


@pytest.mark.django_db
def test_helper_register_complete__invalid_origin(helper, user, settings):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["https://doesnotmatch.example.com"]
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    state = {
        "challenge": "C5-M005a0ZvhiJSTyX38-sY0knREgF-wn4WCNMXUus3osBxh7GSlOZtQ9yE3cw49DUcheIHSW8bprNRuJcz7gA",
        "require_user_verification": True,
    }
    # This response is for localhost, but the allowed origins we set are different. This should fail.
    data = {
        "id": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "rawId": "kSc4jryTTcvXv9M3ja76mQLf-o7tBoUYCr591fdLiXk",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiQzUtTTAwNWEwWnZoaUpTVHlYMzgtc1kwa25SRWdGLXduNFdDTk1YVXVzM29zQnhoN0dTbE9adFE5eUUzY3c0OURVY2hlSUhTVzhicHJOUnVKY3o3Z0EiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["nfc"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED-ztBRiOqHd9nVuLaXFJofd5ttVPW4o8n8VV5ycJ3LxGec0gzEWC3ZbOrO7oqUnx-iOxWslk9xUiUcNJZEAWFA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAIJEnOI68k03L17_TN42u-pkC3_qO7QaFGAq-fdX3S4l5pQECAyYgASFYIA_s7QUYjqh3fZ1bi2lxSaH3ebbVT1uKPJ_FVecnCdy8IlggRnnNIMxFgt2Wzqzu6KlJ8fojsVrJZPcVIlHDSWRAFhQ",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": False}},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidRegistrationResponse):
        helper.register_complete(user=user, data=data, state=state)


@pytest.mark.django_db
def test_helper_register_complete__user_verification_required_but_missing(
    helper, user, settings
):
    settings.OTP_WEBAUTHN_RP_NAME = "Acme Inc."
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    state = {
        "challenge": "5YxycokkCrbhQt_oibIAosFyDk-bu4Xb1Axr_nFf-p8etAVgknq5a1vvmcEpaV9eQind2GOHSlgtVqyhWYYrJQ",
        "require_user_verification": True,
    }

    # This response indicates user verification was not performed
    data = {
        "id": "vLoYx8oKS2CFdjV_kFRxDJonBZdaL6frCoSDi8uU5ME",
        "rawId": "vLoYx8oKS2CFdjV_kFRxDJonBZdaL6frCoSDi8uU5ME",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAILy6GMfKCktghXY1f5BUcQyaJwWXWi-n6wqEg4vLlOTBpQECAyYgASFYICPtDdk8yBjjx3TtLf9Ggjn0yhrj-TTny8l0b8ybNKi_Ilgg54Ml1AP9Aw18XAotrYlhsQyKv1B9cIP2UtAE800tAhc",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiNVl4eWNva2tDcmJoUXRfb2liSUFvc0Z5RGstYnU0WGIxQXhyX25GZi1wOGV0QVZna25xNWExdnZtY0VwYVY5ZVFpbmQyR09IU2xndFZxeWhXWVlySlEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "transports": ["nfc"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEI-0N2TzIGOPHdO0t_0aCOfTKGuP5NOfLyXRvzJs0qL_ngyXUA_0DDXxcCi2tiWGxDIq_UH1wg_ZS0ATzTS0CFw",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NBAAAAAQAAAAAAAAAAAAAAAAAAAAAAILy6GMfKCktghXY1f5BUcQyaJwWXWi-n6wqEg4vLlOTBpQECAyYgASFYICPtDdk8yBjjx3TtLf9Ggjn0yhrj-TTny8l0b8ybNKi_Ilgg54Ml1AP9Aw18XAotrYlhsQyKv1B9cIP2UtAE800tAhc",
        },
        "type": "public-key",
        "clientExtensionResults": {"credProps": {"rk": False}},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidRegistrationResponse):
        helper.register_complete(user=user, data=data, state=state)


def test_helper_get_authentication_state(helper):
    options = {
        "challenge": b"challenge",
        "userVerification": UserVerificationRequirement.REQUIRED.value,
    }
    state = helper.get_authentication_state(options)
    assert isinstance(state, dict)

    assert state["challenge"] == b"challenge"
    assert state["require_user_verification"] is True

    options = {
        "challenge": b"challenge",
        "userVerification": UserVerificationRequirement.PREFERRED.value,
    }
    state = helper.get_authentication_state(options)
    assert state["require_user_verification"] is False


@pytest.mark.django_db
def test_helper_get_generate_authentication_options_kwargs__with_user(
    helper, credential
):
    user = credential.user

    kwargs = helper.get_generate_authentication_options_kwargs(
        user=user, require_user_verification=False
    )

    assert "challenge" in kwargs
    assert "timeout" in kwargs
    assert "rp_id" in kwargs
    assert kwargs["user_verification"] == UserVerificationRequirement.DISCOURAGED.value

    assert "allow_credentials" in kwargs
    assert len(kwargs["allow_credentials"]) == 1
    assert kwargs["allow_credentials"][0].id == credential.credential_id


def test_helper_get_generate_authentication_options_kwargs__anonymous_user(helper):
    kwargs = helper.get_generate_authentication_options_kwargs(
        require_user_verification=True
    )

    assert "challenge" in kwargs
    assert "timeout" in kwargs
    assert "rp_id" in kwargs
    assert kwargs["user_verification"] == UserVerificationRequirement.REQUIRED.value

    assert "allow_credentials" not in kwargs


def test_helper_authenticate_begin__anonymous_user(helper):
    data, state = helper.authenticate_begin(require_user_verification=True)

    assert "challenge" in data
    assert "timeout" in data
    assert "rpId" in data
    assert data["userVerification"] == UserVerificationRequirement.REQUIRED.value
    assert "extensions" in data
    assert data["allowCredentials"] == []

    assert "challenge" in state
    assert "require_user_verification" in state
    assert state["require_user_verification"] is True


@pytest.mark.django_db
def test_helper_authenticate_begin__with_user(helper, credential):
    data, state = helper.authenticate_begin(
        user=credential.user, require_user_verification=False
    )

    assert "challenge" in data
    assert "timeout" in data
    assert "rpId" in data
    assert data["userVerification"] == UserVerificationRequirement.DISCOURAGED.value
    assert "extensions" in data

    assert "allowCredentials" in data
    assert len(data["allowCredentials"]) == 1

    assert "challenge" in state
    assert "require_user_verification" in state
    assert state["require_user_verification"] is False


@pytest.mark.django_db
def test_helper_authenticate_complete__happy(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    credential = WebAuthnCredentialFactory(
        sign_count=1,
        last_used_at=None,
        credential_id=bytes.fromhex(
            "0afed23b93fd6930aa745545017ae25276bf9fdf1676a4b778421e30ac3bca50"
        ),
        public_key=bytes.fromhex(
            "a5010203262001215820672cca16efa8b8596dc19b14a0cda4c0f7c2edb3aaad3748cfa23b69b1540e0f22582068b53d73bed8d3457aaece764fbd453afe9e1286cb907c112545af4509dda508"
        ),
    )

    state = {
        "challenge": "hkZ8860Jpu3q3RfHizxEABl-iI67_nP4c2CTddba3E4tJPVsIW_vnnfO4QFRR7s95HKPTWpzzAMy2UKRmrzchA",
        "require_user_verification": False,
    }
    data = {
        "id": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "rawId": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MBAAAAAg",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiaGtaODg2MEpwdTNxM1JmSGl6eEVBQmwtaUk2N19uUDRjMkNUZGRiYTNFNHRKUFZzSVdfdm5uZk80UUZSUjdzOTVIS1BUV3B6ekFNeTJVS1JtcnpjaEEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEYCIQCiQxft61oYb42wHeeX0iC2s42ZyptLsR4JmufpwVg5RQIhANVZt9lZIrAnfBUZVanlpnm-PHyTreWhSiEs_youYp0i",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }

    device_used = helper.authenticate_complete(data=data, state=state, user=None)

    assert isinstance(device_used, WebAuthnCredential)
    assert device_used.pk == credential.pk

    # Check sign count has been incremented
    assert device_used.sign_count == 2
    # Check last used at has been updated
    assert device_used.last_used_at is not None


@pytest.mark.django_db
def test_helper_authenticate_complete__not_found(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    state = {
        "challenge": "hkZ8860Jpu3q3RfHizxEABl-iI67_nP4c2CTddba3E4tJPVsIW_vnnfO4QFRR7s95HKPTWpzzAMy2UKRmrzchA",
        "require_user_verification": False,
    }
    data = {
        "id": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "rawId": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MBAAAAAg",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiaGtaODg2MEpwdTNxM1JmSGl6eEVBQmwtaUk2N19uUDRjMkNUZGRiYTNFNHRKUFZzSVdfdm5uZk80UUZSUjdzOTVIS1BUV3B6ekFNeTJVS1JtcnpjaEEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEYCIQCiQxft61oYb42wHeeX0iC2s42ZyptLsR4JmufpwVg5RQIhANVZt9lZIrAnfBUZVanlpnm-PHyTreWhSiEs_youYp0i",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(CredentialNotFound):
        helper.authenticate_complete(data=data, state=state, user=None)


@pytest.mark.django_db
def test_helper_authenticate_complete__invalid_rp(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "invalid_rp"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    WebAuthnCredentialFactory(
        sign_count=1,
        last_used_at=None,
        credential_id=bytes.fromhex(
            "0afed23b93fd6930aa745545017ae25276bf9fdf1676a4b778421e30ac3bca50"
        ),
        public_key=bytes.fromhex(
            "a5010203262001215820672cca16efa8b8596dc19b14a0cda4c0f7c2edb3aaad3748cfa23b69b1540e0f22582068b53d73bed8d3457aaece764fbd453afe9e1286cb907c112545af4509dda508"
        ),
    )

    state = {
        "challenge": "hkZ8860Jpu3q3RfHizxEABl-iI67_nP4c2CTddba3E4tJPVsIW_vnnfO4QFRR7s95HKPTWpzzAMy2UKRmrzchA",
        "require_user_verification": False,
    }
    data = {
        "id": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "rawId": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MBAAAAAg",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiaGtaODg2MEpwdTNxM1JmSGl6eEVBQmwtaUk2N19uUDRjMkNUZGRiYTNFNHRKUFZzSVdfdm5uZk80UUZSUjdzOTVIS1BUV3B6ekFNeTJVS1JtcnpjaEEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEYCIQCiQxft61oYb42wHeeX0iC2s42ZyptLsR4JmufpwVg5RQIhANVZt9lZIrAnfBUZVanlpnm-PHyTreWhSiEs_youYp0i",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidAuthenticationResponse):
        helper.authenticate_complete(data=data, state=state, user=None)


@pytest.mark.django_db
def test_helper_authenticate_complete__invalid_origin(helper, settings):
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["https://doesnotmatch.example.com"]

    WebAuthnCredentialFactory(
        sign_count=1,
        last_used_at=None,
        credential_id=bytes.fromhex(
            "0afed23b93fd6930aa745545017ae25276bf9fdf1676a4b778421e30ac3bca50"
        ),
        public_key=bytes.fromhex(
            "a5010203262001215820672cca16efa8b8596dc19b14a0cda4c0f7c2edb3aaad3748cfa23b69b1540e0f22582068b53d73bed8d3457aaece764fbd453afe9e1286cb907c112545af4509dda508"
        ),
    )

    state = {
        "challenge": "hkZ8860Jpu3q3RfHizxEABl-iI67_nP4c2CTddba3E4tJPVsIW_vnnfO4QFRR7s95HKPTWpzzAMy2UKRmrzchA",
        "require_user_verification": False,
    }
    data = {
        "id": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "rawId": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MBAAAAAg",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiaGtaODg2MEpwdTNxM1JmSGl6eEVBQmwtaUk2N19uUDRjMkNUZGRiYTNFNHRKUFZzSVdfdm5uZk80UUZSUjdzOTVIS1BUV3B6ekFNeTJVS1JtcnpjaEEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEYCIQCiQxft61oYb42wHeeX0iC2s42ZyptLsR4JmufpwVg5RQIhANVZt9lZIrAnfBUZVanlpnm-PHyTreWhSiEs_youYp0i",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidAuthenticationResponse):
        helper.authenticate_complete(data=data, state=state, user=None)


@pytest.mark.django_db
def test_helper_authenticate_complete__user_verification_required_but_not_performed(
    helper, settings
):
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

    WebAuthnCredentialFactory(
        sign_count=1,
        last_used_at=None,
        credential_id=bytes.fromhex(
            "0afed23b93fd6930aa745545017ae25276bf9fdf1676a4b778421e30ac3bca50"
        ),
        public_key=bytes.fromhex(
            "a5010203262001215820672cca16efa8b8596dc19b14a0cda4c0f7c2edb3aaad3748cfa23b69b1540e0f22582068b53d73bed8d3457aaece764fbd453afe9e1286cb907c112545af4509dda508"
        ),
    )

    state = {
        "challenge": "hkZ8860Jpu3q3RfHizxEABl-iI67_nP4c2CTddba3E4tJPVsIW_vnnfO4QFRR7s95HKPTWpzzAMy2UKRmrzchA",
        "require_user_verification": True,
    }
    data = {
        "id": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "rawId": "Cv7SO5P9aTCqdFVFAXriUna_n98WdqS3eEIeMKw7ylA",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MBAAAAAg",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiaGtaODg2MEpwdTNxM1JmSGl6eEVBQmwtaUk2N19uUDRjMkNUZGRiYTNFNHRKUFZzSVdfdm5uZk80UUZSUjdzOTVIS1BUV3B6ekFNeTJVS1JtcnpjaEEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEYCIQCiQxft61oYb42wHeeX0iC2s42ZyptLsR4JmufpwVg5RQIhANVZt9lZIrAnfBUZVanlpnm-PHyTreWhSiEs_youYp0i",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }

    with pytest.raises(InvalidAuthenticationResponse):
        helper.authenticate_complete(data=data, state=state, user=None)
