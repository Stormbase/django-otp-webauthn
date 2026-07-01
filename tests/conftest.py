import json
import pathlib

import pytest
from django.conf import settings
from django.test import Client

from django_otp_webauthn.models import (
    WebAuthnAttestation,
    WebAuthnCredential,
    WebAuthnUserHandle,
)
from tests.factories import (
    UserFactory,
    WebAuthnCredentialFactory,
    WebAuthnUserHandleFactory,
)


def _load_json_schema(path):
    json_schema_path = pathlib.Path(settings.BASE_DIR) / path

    with open(json_schema_path) as f:
        return json.load(f)


@pytest.fixture
def begin_registration_response_schema():
    return _load_json_schema("tests/fixtures/schemas/begin_registration_response.json")


@pytest.fixture
def begin_authentication_response_schema():
    return _load_json_schema(
        "tests/fixtures/schemas/begin_authentication_response.json"
    )


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def credential_model():
    return WebAuthnCredential


@pytest.fixture
def attestation_model():
    return WebAuthnAttestation


@pytest.fixture
def user_handle_model():
    return WebAuthnUserHandle


@pytest.fixture
def credential():
    return WebAuthnCredentialFactory()


@pytest.fixture
def user_handle():
    return WebAuthnUserHandleFactory()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_in_memory():
    return UserFactory.build()
