import jsonschema
import pytest
from django.urls import reverse

from tests.factories import WebAuthnCredentialFactory

# REGISTRATION BEGIN VIEW TESTS


@pytest.mark.django_db
def test_registration_begin__http_verbs(api_client, user):
    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)

    # GET should NOT be allowed
    response = api_client.get(url)
    assert response.status_code == 405

    # OPTIONS should be allowed
    response = api_client.options(url)
    assert response.status_code == 200

    # POST should be allowed
    response = api_client.post(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_registration_begin__user_not_authenticated(api_client):
    url = reverse("otp_webauthn:credential-registration-begin")
    response = api_client.post(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_registration_begin__no_existing_credentials(
    api_client, user, begin_registration_response_schema, settings
):
    settings.OTP_WEBAUTHN_RP_ID = "example.com"
    settings.OTP_WEBAUTHN_RP_NAME = "Example Corp."

    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 200

    data = response.json()
    # Response should conform to the schema we established
    jsonschema.validate(data, begin_registration_response_schema)

    # There are no other credentials for this user, so the excludeCredentials list should be empty
    assert len(data["excludeCredentials"]) == 0

    # The user and RP data should be present and correct
    assert data["user"]["name"] == user.username
    assert data["rp"]["id"] == settings.OTP_WEBAUTHN_RP_ID
    assert data["rp"]["name"] == settings.OTP_WEBAUTHN_RP_NAME


@pytest.mark.django_db
def test_registration_begin__has_existing_credentials(
    api_client, user, begin_registration_response_schema, settings
):
    # If passwordless login is allowed, we should signal in the response that we want discoverable credentials to be created
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True

    credential_id = b"existing_credential_id"
    base64_credential_id = "ZXhpc3RpbmdfY3JlZGVudGlhbF9pZA"

    existing_credential = WebAuthnCredentialFactory(
        user=user, credential_id=credential_id
    )

    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 200

    data = response.json()
    # Response should conform to the schema we established
    jsonschema.validate(data, begin_registration_response_schema)

    # There is one existing credential for this user, so the excludeCredentials list should have one entry
    assert len(data["excludeCredentials"]) == 1
    assert data["excludeCredentials"][0]["id"] == base64_credential_id
    assert data["excludeCredentials"][0]["type"] == "public-key"
    assert data["excludeCredentials"][0]["transports"] == existing_credential.transports


@pytest.mark.django_db
def test_registration_begin__passwordless_login_enabled(
    api_client, user, begin_registration_response_schema, settings
):
    # If passwordless login is allowed, we should signal in the response that we prefer a discoverable credential be created
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True

    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 200

    data = response.json()
    # Response should conform to the schema we established
    jsonschema.validate(data, begin_registration_response_schema)

    assert data["authenticatorSelection"]["requireResidentKey"] is True
    assert data["authenticatorSelection"]["residentKey"] == "required"


@pytest.mark.django_db
def test_registration_begin__passwordless_login_disabled(
    api_client, user, begin_registration_response_schema, settings
):
    # If passwordless login is disallowed, we signal in the response that we do not require discoverable credentials
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 200

    data = response.json()
    # Response should conform to the schema we established
    jsonschema.validate(data, begin_registration_response_schema)

    assert data["authenticatorSelection"]["requireResidentKey"] is False
    assert data["authenticatorSelection"]["residentKey"] == "preferred"


@pytest.mark.django_db
def test_registration_begin__keeps_state(
    api_client, user, begin_registration_response_schema
):
    url = reverse("otp_webauthn:credential-registration-begin")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 200

    data = response.json()
    # Response should conform to the schema we established
    jsonschema.validate(data, begin_registration_response_schema)

    challenge = data["challenge"]
    assert "otp_webauthn_register_state" in api_client.session
    assert api_client.session["otp_webauthn_register_state"]["challenge"] == challenge


# REGISTRATION COMPLETE VIEW TESTS


@pytest.mark.django_db
def test_registration_complete__http_verbs(api_client, user):
    url = reverse("otp_webauthn:credential-registration-complete")
    api_client.force_login(user)

    # GET should NOT be allowed
    response = api_client.get(url)
    assert response.status_code == 405

    # OPTIONS should be allowed
    response = api_client.options(url)
    assert response.status_code == 200

    # POST should be allowed, though this response will be a 400 because we're not sending the right data
    response = api_client.post(url)
    assert response.status_code == 400


@pytest.mark.django_db
def test_registration_complete__user_not_authenticated(api_client):
    url = reverse("otp_webauthn:credential-registration-complete")
    response = api_client.post(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_registration_complete__no_state(api_client, user):
    url = reverse("otp_webauthn:credential-registration-complete")
    api_client.force_login(user)
    response = api_client.post(url)
    assert response.status_code == 400
    assert response.data["detail"].code == "invalid_state"


@pytest.mark.django_db
def test_registration_complete__no_reusing_state(api_client, user):
    url = reverse("otp_webauthn:credential-registration-complete")
    api_client.force_login(user)
    api_client.session["otp_webauthn_register_state"] = {"challenge": "challenge"}
    response = api_client.post(url)
    assert response.status_code == 400

    # The state should be removed from the session - there is no reusing it
    assert not api_client.session.get("otp_webauthn_register_state")


@pytest.mark.django_db
def test_registration_complete__valid_response(api_client, user, credential_model):
    url = reverse("otp_webauthn:credential-registration-complete")
    api_client.force_login(user)
    # Override state with a known value
    session = api_client.session
    session["otp_webauthn_register_state"] = {
        "challenge": "3ThyM30dpNEVLPWC9o53PGYTz1cEtkel2-20WKrE_YYhC2hn9DjpB8HzOZdpHr9-im5RkUlaWMugug7GsqNf9A",
        "require_user_verification": True,
    }
    session.save()

    payload = {
        "id": "wQHw7KNelqXG1fmEzfqINhTexhE",
        "rawId": "wQHw7KNelqXG1fmEzfqINhTexhE",
        "response": {
            "attestationObject": "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YViYSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAAAAAAAAAAAAAAAAAAAAAAAAFMEB8OyjXpalxtX5hM36iDYU3sYRpQECAyYgASFYIHdL14TTJhK8gZrgL88d5elYJRZjNVh6M9UP51wZzPltIlggwOAmqqFqFBBQ93kdkqRlxcKsMHol3UA7L6oP-SJOxsA",
            "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiM1RoeU0zMGRwTkVWTFBXQzlvNTNQR1lUejFjRXRrZWwyLTIwV0tyRV9ZWWhDMmhuOURqcEI4SHpPWmRwSHI5LWltNVJrVWxhV011Z3VnN0dzcU5mOUEiLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjgwMDAifQ",
            "transports": ["internal", "hybrid"],
            "publicKeyAlgorithm": -7,
            "publicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEd0vXhNMmEryBmuAvzx3l6VglFmM1WHoz1Q_nXBnM-W3A4CaqoWoUEFD3eR2SpGXFwqwweiXdQDsvqg_5Ik7GwA",
            "authenticatorData": "SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NdAAAAAAAAAAAAAAAAAAAAAAAAAAAAFMEB8OyjXpalxtX5hM36iDYU3sYRpQECAyYgASFYIHdL14TTJhK8gZrgL88d5elYJRZjNVh6M9UP51wZzPltIlggwOAmqqFqFBBQ93kdkqRlxcKsMHol3UA7L6oP-SJOxsA",
        },
        "type": "public-key",
        "api_clientExtensionResults": {},
        "authenticatorAttachment": "platform",
    }
    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == 200

    cred = credential_model.objects.first()
    assert cred.pk == response.data["id"]
    assert cred.user == user
    assert cred.transports == ["internal", "hybrid"]
