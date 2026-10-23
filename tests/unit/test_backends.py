import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import aauthenticate

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


@pytest.mark.parametrize("is_active", [True, False])
@pytest.mark.django_db
def test_webauthn_backend__aauthenticate__same_result_as_authenticate(
    rf, credential, is_active
):
    credential.user.is_active = is_active
    credential.user.save()
    request = rf.get("/")
    backend = WebAuthnBackend()

    # Fresh instances, so the user is not yet cached on the credential and the
    # async path has to load it from the database.
    sync_credential = type(credential).objects.get(pk=credential.pk)
    async_credential = type(credential).objects.get(pk=credential.pk)

    sync_user = backend.authenticate(request, webauthn_credential=sync_credential)
    async_user = async_to_sync(backend.aauthenticate)(
        request, webauthn_credential=async_credential
    )

    assert async_user == sync_user
    assert async_user == (credential.user if is_active else None)


def test_webauthn_backend__aauthenticate__no_webauthn_credential_parameter(rf):
    request = rf.get("/")
    backend = WebAuthnBackend()
    assert async_to_sync(backend.aauthenticate)(request) is None


@pytest.mark.parametrize("is_active", [True, False])
@pytest.mark.django_db
def test_webauthn_backend__aget_user__same_result_as_get_user(user, is_active):
    user.is_active = is_active
    user.save()
    backend = WebAuthnBackend()

    async_user = async_to_sync(backend.aget_user)(user.pk)

    assert async_user == backend.get_user(user.pk)
    assert async_user == (user if is_active else None)


@pytest.mark.django_db
def test_webauthn_backend__aget_user__user_does_not_exist(user):
    user_id = user.pk
    user.delete()
    backend = WebAuthnBackend()

    assert backend.get_user(user_id) is None
    assert async_to_sync(backend.aget_user)(user_id) is None


def test_webauthn_backend__async_methods_use_overridden_sync_methods(rf):
    """Subclasses that customize the sync methods get the same behavior in async code."""
    sentinel = object()

    class CustomWebAuthnBackend(WebAuthnBackend):
        def authenticate(self, request, webauthn_credential=None, **kwargs):
            return sentinel

        def get_user(self, user_id):
            return sentinel

    request = rf.get("/")
    backend = CustomWebAuthnBackend()

    assert async_to_sync(backend.aauthenticate)(request) is sentinel
    assert async_to_sync(backend.aget_user)(1) is sentinel


@pytest.mark.django_db
def test_django_aauthenticate__webauthn_credential(rf, credential):
    request = rf.get("/")
    user = async_to_sync(aauthenticate)(request, webauthn_credential=credential)

    assert user == credential.user
    assert user.backend == "django_otp_webauthn.backends.WebAuthnBackend"


@pytest.mark.django_db
def test_django_aauthenticate__invalid_password(rf, user, mocker):
    """WebAuthnBackend accepts any credentials, so Django also tries it when
    another backend rejects a username and password."""
    spy = mocker.spy(WebAuthnBackend, "aauthenticate")
    request = rf.get("/")
    authenticated_user = async_to_sync(aauthenticate)(
        request,
        username=user.get_username(),
        password="wrong",  # noqa: S106
    )

    assert authenticated_user is None
    spy.assert_called_once()
