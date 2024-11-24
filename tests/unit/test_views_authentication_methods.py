import pytest

from django_otp_webauthn.views import CompleteCredentialAuthenticationView


def test_authentication_get_success_url__fallback(rf, user_in_memory, settings):
    settings.LOGIN_REDIRECT_URL = "/login-redirect/"
    request = rf.post("/")
    request.user = user_in_memory

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    assert view.get_success_url() == "/login-redirect/"


def test_authentication_get_success_url__next_param(rf, user_in_memory):
    request = rf.post("/?next=/next-redirect/")
    request.user = user_in_memory

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    assert view.get_success_url() == "/next-redirect/"


def test_authentication_get_success_url__next_param_insecure(
    rf, user_in_memory, settings
):
    """Verify that we require HTTPS for the redirect URL if the request is secure."""
    settings.LOGIN_REDIRECT_URL = "/login-redirect/"
    request = rf.post("/?next=http://example.com/next-redirect/")
    request.user = user_in_memory

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    # The URL is not safe, so we should fall back to the default
    assert view.get_success_url() == "/login-redirect/"


def test_authentication_get_success_url__next_param_host_in_allowed_hosts(
    rf, user_in_memory, settings
):
    """Verify that we allow the redirect URL if the host is in the allowed hosts list."""
    settings.LOGIN_REDIRECT_URL = "/login-redirect/"
    request = rf.post("/?next=http://example.com/next-redirect/")
    request.user = user_in_memory

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    view.success_url_allowed_hosts = {"example.com"}
    assert view.get_success_url() == "http://example.com/next-redirect/"


def test_authentication_get_success_url__next_require_https(
    rf, user_in_memory, settings
):
    """Verify that we require HTTPS for the redirect URL if the request is secure."""
    settings.LOGIN_REDIRECT_URL = "/login-redirect/"
    request = rf.post("/?next=http://example.com/next-redirect/")
    request.is_secure = lambda: True
    request.user = user_in_memory

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    view.success_url_allowed_hosts = {"example.com"}
    assert view.get_success_url() == "/login-redirect/"


@pytest.mark.django_db
def test_authentication_get_success_data(rf, credential):
    request = rf.post("/")

    view = CompleteCredentialAuthenticationView()
    view.setup(request)
    data = view.get_success_data(credential)
    assert data["id"] == credential.pk
