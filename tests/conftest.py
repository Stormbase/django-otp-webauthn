import pytest

from django_otp_webauthn.models import WebAuthnAttestation, WebAuthnCredential
from tests.factories import UserFactory, WebAuthnCredentialFactory


@pytest.fixture
def credential_model():
    return WebAuthnCredential


@pytest.fixture
def attestations_model():
    return WebAuthnAttestation


@pytest.fixture
def credential():
    return WebAuthnCredentialFactory()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_in_memory():
    return UserFactory.build()
