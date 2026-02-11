import jsonschema
import pytest
from django.urls import reverse
from webauthn import base64url_to_bytes

from tests.factories import WebAuthnCredentialFactory


@pytest.mark.parametrize(
    "url",
    [
        reverse("otp_webauthn:credential-authentication-begin"),
        reverse("otp_webauthn:credential-authentication-complete"),
    ],
)
def test_authentication__anonymous_user_passwordless_login_disallowed(
    api_client, settings, url
):
    """Test that an anonymous user is not allowed to begin authentication if passwordless login is disabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    response = api_client.post(url)
    assert response.status_code == 403, response.data
    assert response.data["detail"].code == "passwordless_login_disabled"


@pytest.mark.parametrize(
    "url",
    [
        reverse("otp_webauthn:credential-authentication-begin"),
        reverse("otp_webauthn:credential-authentication-complete"),
    ],
)
@pytest.mark.django_db
def test_authentication__http_verbs(api_client, user, url):
    api_client.force_login(user)

    # GET should NOT be allowed
    response = api_client.get(url)
    assert response.status_code == 405

    # OPTIONS should be allowed
    response = api_client.options(url)
    assert response.status_code == 200, response.data

    # POST should be allowed
    response = api_client.post(url)
    # We expect either a 200 or a 400 response (because we are not passing any data)
    assert response.status_code == 200 or response.status_code == 400, response.data


# BEGIN AUTHENTICATION VIEW
def test_authentication_begin__anonymous_user_passwordless_login_allowed(
    api_client, begin_authentication_response_schema, settings
):
    """Test that an anonymous user is allowed to begin authentication if passwordless login is enabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    # Even if the default permission class is set to IsAuthenticated, we should
    # still be able to begin authentication.
    # Ref: #19
    settings.REST_FRAMEWORK = {
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ]
    }
    response = api_client.post(reverse("otp_webauthn:credential-authentication-begin"))
    assert response.status_code == 200, response.data
    data = response.json()
    session = api_client.session

    # Validate the response schema
    jsonschema.validate(data, begin_authentication_response_schema)

    # Since an anonymous user is trying to authenticate, we require user verification
    assert (
        session["otp_webauthn_authentication_state"]["require_user_verification"]
        is True
    )

    challenge = data["challenge"]
    assert session["otp_webauthn_authentication_state"]["challenge"] == challenge
    assert data["userVerification"] == "required"
    assert data["allowCredentials"] == []


@pytest.mark.django_db
def test_authentication_begin__logged_in_user(
    api_client, begin_authentication_response_schema, user
):
    """Test that an anonymous user are allowed to begin authentication if passwordless login is enabled."""

    api_client.force_authenticate(user)
    credential_id = b"existing_credential_id"
    hashed_credential_id = "ZXhpc3RpbmdfY3JlZGVudGlhbF9pZA"
    WebAuthnCredentialFactory(user=user, credential_id=credential_id)

    response = api_client.post(reverse("otp_webauthn:credential-authentication-begin"))
    assert response.status_code == 200, response.data
    data = response.json()
    session = api_client.session

    # Validate the response schema
    jsonschema.validate(data, begin_authentication_response_schema)

    # Since a logged in user is trying to authenticate, we do not require user verification.
    assert (
        session["otp_webauthn_authentication_state"]["require_user_verification"]
        is False
    )

    challenge = data["challenge"]
    assert session["otp_webauthn_authentication_state"]["challenge"] == challenge
    assert data["userVerification"] == "discouraged"
    assert data["allowCredentials"][0]["id"] == hashed_credential_id


# COMPLETE AUTHENTICATION VIEW


@pytest.mark.django_db
def test_authentication_complete__no_state(api_client, user):
    url = reverse("otp_webauthn:credential-authentication-complete")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 400, response.data
    assert response.data["detail"].code == "invalid_state"


@pytest.mark.django_db
def test_authentication_complete__no_reusing_state(api_client, user):
    url = reverse("otp_webauthn:credential-authentication-complete")
    api_client.force_login(user)
    api_client.session["otp_webauthn_authentication_state"] = {"challenge": "challenge"}
    response = api_client.post(url)
    assert response.status_code == 400, response.data

    # The state should be removed from the session - there is no reusing it
    assert not api_client.session.get("otp_webauthn_authentication_state")


def setup_complete_authentication(*, api_client, user):
    """Abstract away repetitive boilerplate code for the authentication complete tests.

    Returns:
        Tuple: (payload: dict, credential: WebAuthnCredential, session)
    """

    challenge = "_ukfVX3634AMvNLIK4rJZcs7inYC7lQvs4g46loR3cpwTUmHpL0KwmP-4-qix_4gPo3lT3PVWaO3v3vClMEvBw"
    credential_id = "gKNdADy_EdYWlnMF17eSTb4EbJOPUGqzhc4qsofNomE"
    session = api_client.session
    session["otp_webauthn_authentication_state"] = {
        "challenge": challenge,
        "require_user_verification": True,
    }
    session.save()

    credential = WebAuthnCredentialFactory(
        credential_id=base64url_to_bytes(credential_id),
        user=user,
        public_key=bytes.fromhex(
            "a5010203262001215820a6d7c6bbc8416f99189af6f86e203d8f8154702e3f989adefe93f2461855e005225820adca8acb88e17990937a430cfdc97bf3e80ab0ab6a705a5b9826b20523ba9f2c"
        ),
    )

    payload = {
        "id": credential_id,
        "rawId": "gKNdADy_EdYWlnMF17eSTb4EbJOPUGqzhc4qsofNomE",
        "response": {
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2MFAAAAFQ",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0IiwiY2hhbGxlbmdlIjoiX3VrZlZYMzYzNEFNdk5MSUs0ckpaY3M3aW5ZQzdsUXZzNGc0NmxvUjNjcHdUVW1IcEwwS3dtUC00LXFpeF80Z1BvM2xUM1BWV2FPM3YzdkNsTUV2QnciLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAiLCJjcm9zc09yaWdpbiI6ZmFsc2V9",
            "signature": "MEUCIQDTUKJV-1YkLWBmWpn5UbN-5B1fbNhabBjZqEd-xUsfmgIgA6sjohXSsQ1FsR6MvaLo-Dim6zxwq5wErt28C2Pq7xw",
            "userHandle": "bjQLnP-zepicpUTmu3gKLHiQHT-zNzh2hRGjBhevoB0",
        },
        "type": "public-key",
        "clientExtensionResults": {},
        "authenticatorAttachment": "cross-platform",
    }
    return payload, credential, session


@pytest.mark.django_db
def test_authentication_complete__anonymous_user_passwordless_login_allowed(
    api_client, settings, user
):
    """Test that an anonymous user is allowed to complete authentication if passwordless login is enabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True

    # Even if the default permission class is set to IsAuthenticated, we should
    # still be able to complete the authentication.
    # Ref: #19
    settings.REST_FRAMEWORK = {
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ]
    }

    payload, credential, session = setup_complete_authentication(
        api_client=api_client, user=user
    )

    response = api_client.post(
        reverse("otp_webauthn:credential-authentication-complete"),
        data=payload,
        format="json",
    )
    assert response.status_code == 200, response.data
    data = response.json()
    assert data["id"] == credential.pk
    session = api_client.session
    assert "otp_webauthn_authentication_state" not in session
    assert session["otp_device_id"] == credential.persistent_id
    assert session["_auth_user_id"] == str(user.pk)
    assert (
        session["_auth_user_backend"] == "django_otp_webauthn.backends.WebAuthnBackend"
    )
    # Signaled that user details sync is needed
    assert session["otp_webauthn_sync_needed"] is True


@pytest.mark.django_db
def test_authentication_complete__verify_existing_user(api_client, settings, user):
    """Test that an existing users' django-otp verification state is updated with the device ID."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    api_client.force_authenticate(user)

    payload, credential, session = setup_complete_authentication(
        api_client=api_client, user=user
    )

    response = api_client.post(
        reverse("otp_webauthn:credential-authentication-complete"),
        data=payload,
        format="json",
    )
    assert response.status_code == 200, response.data
    data = response.json()
    assert data["id"] == credential.pk
    session = api_client.session
    assert "otp_webauthn_authentication_state" not in session
    assert session["otp_device_id"] == credential.persistent_id
    # Signaled that user details sync is needed
    assert session["otp_webauthn_sync_needed"] is True


@pytest.mark.django_db
def test_authentication_complete_device_usable__unconfirmed(api_client, user):
    """Test that the authentication complete view prevents the authentication from succeeding if the credential is not confirmed."""
    api_client.force_authenticate(user)

    payload, credential, session = setup_complete_authentication(
        api_client=api_client, user=user
    )
    credential.confirmed = False
    credential.save()

    response = api_client.post(
        reverse("otp_webauthn:credential-authentication-complete"),
        data=payload,
        format="json",
    )
    assert response.status_code == 403, response.data
    assert response.data["detail"].code == "credential_disabled"
    session = api_client.session
    assert "otp_webauthn_authentication_state" not in session
    assert "otp_device_id" not in session
    # No user details sync should be requested
    assert "otp_webauthn_sync_needed" not in session


@pytest.mark.django_db
def test_authentication_complete_device_usable__user_disabled(
    api_client, settings, user
):
    """Test that the authentication complete view prevents the authentication from succeeding if the user associated with the credential is disabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    # Mark the user as inactive - this will prevent the authentication from
    # succeeding once we identify the Passkey belongs to a disabled user
    user.is_active = False
    user.save()

    payload, _, session = setup_complete_authentication(
        api_client=api_client, user=user
    )

    response = api_client.post(
        reverse("otp_webauthn:credential-authentication-complete"),
        data=payload,
        format="json",
    )
    assert response.status_code == 403, response.data
    assert response.data["detail"].code == "user_disabled"
    session = api_client.session
    assert "otp_webauthn_authentication_state" not in session
    assert "otp_device_id" not in session
    # No user details sync should be requested
    assert "otp_webauthn_sync_needed" not in session


@pytest.mark.django_db
def test_authentication_complete_get_success_url__understands_next_url_parameter(
    api_client, user
):
    """Test that the authentication complete view understands the `next` URL parameter and uses it to set the redirect url."""
    api_client.force_authenticate(user)
    payload, _, _ = setup_complete_authentication(api_client=api_client, user=user)

    response = api_client.post(
        reverse("otp_webauthn:credential-authentication-complete") + "?next=/admin",
        data=payload,
        format="json",
    )
    assert response.status_code == 200, response.data
    data = response.json()
    assert data["redirect_url"] == "/admin"
