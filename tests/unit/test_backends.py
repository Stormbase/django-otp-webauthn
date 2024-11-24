import pytest

from django_otp_webauthn.backends import WebAuthnBackend


def test_webauthn_backend__authenticate__no_webauthn_credential_parameter(rf):
    request = rf.get("/")
    backend = WebAuthnBackend()
    assert backend.authenticate(request) is None


@pytest.mark.django_db
def test_webauthn_backend__authenticate__webauthn_credential_parameter(rf, credential):
    request = rf.get("/")
    backend = WebAuthnBackend()

    user = backend.authenticate(request, webauthn_credential=credential)
    assert user == credential.user


def test_webauthn_backend__user_can_authenticate__user_is_active(rf, user_in_memory):
    assert user_in_memory.is_active

    backend = WebAuthnBackend()
    assert backend.user_can_authenticate(user_in_memory)


def test_webauthn_backend__user_can_authenticate__user_is_not_active(
    rf, user_in_memory
):
    user_in_memory.is_active = False

    backend = WebAuthnBackend()
    assert not backend.user_can_authenticate(user_in_memory)


@pytest.mark.django_db
def test_webauthn_backend__get_user__user_does_not_exist():
    backend = WebAuthnBackend()
    assert backend.get_user(1) is None


@pytest.mark.django_db
def test_webauthn_backend__get_user__user_exists(user):
    backend = WebAuthnBackend()
    assert backend.get_user(user.pk) == user
