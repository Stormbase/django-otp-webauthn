import pytest

from django_otp_webauthn.backends import UnenrolledModelBackend, WebAuthnBackend
from tests.conftest import CORRECT_PASSWORD


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


@pytest.mark.django_db
def test_unenrolled_model_backend__authenticate__webauthn_credential(
    rf, credential_with_password
):
    request = rf.get("/")
    backend = UnenrolledModelBackend()

    user = backend.authenticate(
        request,
        username=credential_with_password.user.username,
        password=CORRECT_PASSWORD,
    )
    assert user is None

    user = backend.authenticate(
        request,
        username=credential_with_password.user.username,
        password="incorrect",  # noqa: S106
    )
    assert user is None


@pytest.mark.django_db
def test_unenrolled_model_backend__authenticate__unconfirmed_webauthn_credential(
    rf, credential_with_password
):
    request = rf.get("/")
    backend = UnenrolledModelBackend()
    credential_with_password.confirmed = False
    credential_with_password.save()

    user = backend.authenticate(
        request,
        username=credential_with_password.user.username,
        password=CORRECT_PASSWORD,
    )
    assert user == credential_with_password.user

    user = backend.authenticate(
        request,
        username=credential_with_password.user.username,
        password="incorrect",  # noqa: S106
    )
    assert user is None


@pytest.mark.django_db
def test_unenrolled_model_backend__authenticate__password_only(rf, user_with_password):
    request = rf.get("/")
    backend = UnenrolledModelBackend()

    authenticated_user = backend.authenticate(
        request,
        username=user_with_password.username,
        password=CORRECT_PASSWORD,
    )
    assert authenticated_user == user_with_password

    authenticated_user = backend.authenticate(
        request,
        username=user_with_password.username,
        password="incorrect",  # noqa: S106
    )
    assert authenticated_user is None


@pytest.mark.django_db
def test_unenrolled_model_backend__authenticate__enrolled_and_unenrolled_users(
    rf, user_with_password, credential
):
    request = rf.get("/")
    backend = UnenrolledModelBackend()

    authenticated_user = backend.authenticate(
        request,
        username=user_with_password.username,
        password=CORRECT_PASSWORD,
    )

    assert authenticated_user == user_with_password
    assert authenticated_user != credential.user
