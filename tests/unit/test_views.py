import pytest
from django.contrib.auth.models import AnonymousUser

from django_otp_webauthn import exceptions
from django_otp_webauthn.helpers import WebAuthnHelper
from django_otp_webauthn.views import (
    BeginCredentialAuthenticationView,
    BeginCredentialRegistrationView,
    CompleteCredentialAuthenticationView,
    CompleteCredentialRegistrationView,
    _get_pywebauthn_logger,
)


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialRegistrationView,
        CompleteCredentialRegistrationView,
        BeginCredentialAuthenticationView,
        CompleteCredentialAuthenticationView,
    ],
)
def test_views__no_caching_headers_present(rf, view_class, user_in_memory):
    request = rf.post("/")
    request.user = user_in_memory

    view = view_class()
    view.setup(request)

    response = view.dispatch(request)
    assert (
        response.headers["Cache-Control"]
        == "max-age=0, no-cache, no-store, must-revalidate, private"
    )
    assert "Expires" in response.headers


def test_pywebauthn_logger(settings):
    settings.OTP_WEBAUTHN_EXCEPTION_LOGGER_NAME = "test_logger"
    _get_pywebauthn_logger.cache_clear()
    logger = _get_pywebauthn_logger()
    assert logger.name == "test_logger"

    _get_pywebauthn_logger.cache_clear()
    # Indicating 'do not log'
    settings.OTP_WEBAUTHN_EXCEPTION_LOGGER_NAME = None
    logger = _get_pywebauthn_logger()
    assert logger is None


# REGISTRATION MIXIN TESTS


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialRegistrationView,
        CompleteCredentialRegistrationView,
    ],
)
def test_registration__get_user(rf, view_class, user_in_memory):
    request = rf.post("/")
    request.user = AnonymousUser()

    view = view_class()
    view.setup(request)
    user = view.get_user()
    assert user is None

    # Now test with an authenticated user
    request.user = user_in_memory
    view = view_class()
    view.setup(request)
    user = view.get_user()
    assert user == user_in_memory


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialRegistrationView,
        CompleteCredentialRegistrationView,
    ],
)
def test_registration__get_helper(rf, view_class):
    request = rf.post("/")
    request.user = AnonymousUser()

    view = view_class()
    view.setup(request)
    helper = view.get_helper()
    assert isinstance(helper, WebAuthnHelper)


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialRegistrationView,
        CompleteCredentialRegistrationView,
    ],
)
def test_registration__check_can_register(rf, view_class, user_in_memory):
    request = rf.post("/")
    request.user = user_in_memory

    view = view_class()
    view.setup(request)
    view.check_can_register()


# AUTHENTICATION MIXIN TESTS


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialAuthenticationView,
        CompleteCredentialAuthenticationView,
    ],
)
def test_authentication__get_user(rf, view_class, user_in_memory):
    request = rf.post("/")
    request.user = AnonymousUser()

    view = view_class()
    view.setup(request)
    user = view.get_user()
    assert user is None

    # Now test with an authenticated user
    request.user = user_in_memory
    view = view_class()
    view.setup(request)
    user = view.get_user()
    assert user == user_in_memory


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialAuthenticationView,
        CompleteCredentialAuthenticationView,
    ],
)
def test_authentication__get_helper(rf, view_class):
    request = rf.post("/")
    request.user = AnonymousUser()

    view = view_class()
    view.setup(request)
    helper = view.get_helper()
    assert isinstance(helper, WebAuthnHelper)


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialAuthenticationView,
        CompleteCredentialAuthenticationView,
    ],
)
def test_authentication__check_can_authenticate__user_logged_in(
    rf, view_class, user_in_memory, settings
):
    """Verify that we allow the authentication ceremonies to proceed if the user is logged in and passwordless login is disabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    request = rf.post("/")
    request.user = user_in_memory

    view = view_class()
    view.setup(request)

    # This should not raise an exception
    view.check_can_authenticate()


@pytest.mark.parametrize(
    "view_class",
    [
        BeginCredentialAuthenticationView,
        CompleteCredentialAuthenticationView,
    ],
)
@pytest.mark.parametrize("allow_passwordless", [True, False])
def test_authentication__check_can_authenticate__passwordless(
    rf, view_class, allow_passwordless, settings
):
    """Verify that we allow the authentication ceremonies to proceed if the user is logged in and passwordless login is disabled."""
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = allow_passwordless
    request = rf.post("/")
    request.user = AnonymousUser()

    view = view_class()
    view.setup(request)

    if allow_passwordless:
        view.check_can_authenticate()
    else:
        with pytest.raises(exceptions.PasswordlessLoginDisabled):
            view.check_can_authenticate()
