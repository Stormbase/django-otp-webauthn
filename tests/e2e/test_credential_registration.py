import pytest
from playwright.sync_api import expect
from webauthn import base64url_to_bytes

from tests.e2e.fixtures import StatusEnum, VirtualAuthenticator

JS_EVENT_REGISTER_START = "otp_webauthn.register_start"
JS_EVENT_REGISTER_COMPLETE = "otp_webauthn.register_complete"
JS_EVENT_REGISTER_FAILED = "otp_webauthn.register_failed"


def test_register_credential__legacy_u2f_passwordless_setting_enabled(
    live_server,
    django_db_serialized_rollback,
    page,
    playwright_force_login,
    user,
    settings,
    virtual_authenticator,
    credential_model,
    wait_for_javascript_event,
):
    """Verify that legacy U2F authenticator credential registration is
    impossible when passwordless login is enabled, as these devices can never be
    used to authenticate without a password.

    See comment in ``WebAuthnHelper.get_discoverable_credentials_preference``
    method for more information.
    """
    playwright_force_login(user)
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True

    # Create a virtual authenticator and listen for the credentialAdded event
    virtual_authenticator(VirtualAuthenticator.u2f())

    page.goto(live_server.url)
    await_start_event = wait_for_javascript_event(JS_EVENT_REGISTER_START)
    await_failed_event = wait_for_javascript_event(JS_EVENT_REGISTER_FAILED)
    register_button = page.locator("button#passkey-register-button")
    expect(register_button).to_be_visible()

    register_button.click()

    page.wait_for_selector(
        f"#passkey-register-status-message[data-status-enum='{StatusEnum.NOT_ALLOWED_OR_ABORTED}']",
        timeout=2000,
    )

    # Did the right events fire?
    await_start_event()
    res = await_failed_event()

    # The registration should have failed, because the authenticator cannot
    # create a credential that meets our requirements, the only option the user
    # has is to close the dialog and cancel the operation.
    assert "error" in res
    assert res["error"].name == "NotAllowedError"

    assert credential_model.objects.count() == 0


def test_register_credential__legacy_u2f_passwordless_setting_disabled(
    live_server,
    django_db_serialized_rollback,
    page,
    playwright_force_login,
    user,
    cdpsession,
    settings,
    virtual_authenticator,
    event_waiter,
    credential_model,
    wait_for_javascript_event,
):
    """Verify that legacy U2F authenticator credential registration is possible when
    passwordless login is disabled. In this configuration, it makes sense to
    allow the registration of U2F authenticators, as they can be used to verify
    the user as a second verification step."""
    playwright_force_login(user)
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False

    # Create a virtual authenticator and listen for the credentialAdded event
    virtual_authenticator(VirtualAuthenticator.u2f())
    get_credential, set_credential = event_waiter()
    cdpsession.once("WebAuthn.credentialAdded", set_credential)

    page.goto(live_server.url)
    await_start_event = wait_for_javascript_event(JS_EVENT_REGISTER_START)
    await_complete_event = wait_for_javascript_event(JS_EVENT_REGISTER_COMPLETE)
    register_button = page.locator("button#passkey-register-button")
    expect(register_button).to_be_visible()

    register_button.click()

    page.wait_for_selector(
        f"#passkey-register-status-message[data-status-enum='{StatusEnum.SUCCESS}']",
        timeout=2000,
    )

    browser_credential = get_credential()

    # Did we store the same information as the browser?
    credential = credential_model.objects.first()
    assert credential.user == user
    assert credential.credential_id == base64url_to_bytes(
        browser_credential["credential"]["credentialId"]
    )
    assert credential.discoverable is False
    assert credential.transports == ["usb"]
    assert (
        credential.backup_eligible
        == browser_credential["credential"]["backupEligibility"]
    )
    assert credential.backup_state == browser_credential["credential"]["backupState"]

    # Did the right events fire?
    await_start_event()
    res = await_complete_event()

    # Check the event contents
    assert res["response"]["id"] == credential.pk
    assert res["id"] == credential.pk


@pytest.mark.parametrize("support_passwordless", [True, False])
def test_register_credential__internal_success(
    live_server,
    django_db_serialized_rollback,
    page,
    playwright_force_login,
    user,
    cdpsession,
    settings,
    virtual_authenticator,
    event_waiter,
    credential_model,
    wait_for_javascript_event,
    support_passwordless,
):
    playwright_force_login(user)
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = support_passwordless

    # Create a virtual authenticator and listen for the credentialAdded event
    virtual_authenticator(VirtualAuthenticator.internal())

    # Listen for the credentialAdded event
    get_credential, set_credential = event_waiter()
    cdpsession.once("WebAuthn.credentialAdded", set_credential)

    page.goto(live_server.url)
    await_start_event = wait_for_javascript_event(JS_EVENT_REGISTER_START)
    await_complete_event = wait_for_javascript_event(JS_EVENT_REGISTER_COMPLETE)
    register_button = page.locator("button#passkey-register-button")
    expect(register_button).to_be_visible()

    register_button.click()
    # Wait for the page to display a success message, afterwards it is likely
    # safe to get the credential without being trapped waiting for eternity..
    page.wait_for_selector(
        f"#passkey-register-status-message[data-status-enum='{StatusEnum.SUCCESS}']",
        timeout=2000,
    )
    browser_credential = get_credential()

    # Did we store the same information as the browser?
    credential = credential_model.objects.first()
    assert credential.user == user
    assert credential.credential_id == base64url_to_bytes(
        browser_credential["credential"]["credentialId"]
    )
    assert credential.discoverable is True
    assert credential.transports == ["internal"]
    assert (
        credential.backup_eligible
        == browser_credential["credential"]["backupEligibility"]
    )
    assert credential.backup_state == browser_credential["credential"]["backupState"]

    # Did the right events fire?
    await_start_event()
    res = await_complete_event()

    # Check the event contents
    assert res["response"]["id"] == credential.pk
    assert res["id"] == credential.pk


def test_register_credential__fail_bad_user_presence(
    live_server,
    django_db_serialized_rollback,
    settings,
    page,
    playwright_force_login,
    user,
    cdpsession,
    virtual_authenticator,
    event_waiter,
    credential_model,
    wait_for_javascript_event,
):
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    playwright_force_login(user)

    # Create a virtual authenticator and listen for the credentialAdded event
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())

    # Override the response parameters to force a failure
    cdpsession.send(
        "WebAuthn.setResponseOverrideBits",
        {"authenticatorId": authenticator["authenticatorId"], "isBadUp": True},
    )

    page.goto(live_server.url)
    await_start_event = wait_for_javascript_event(JS_EVENT_REGISTER_START)
    await_failure_event = wait_for_javascript_event(JS_EVENT_REGISTER_FAILED)
    register_button = page.locator("button#passkey-register-button")
    expect(register_button).to_be_visible()

    register_button.click()
    page.wait_for_selector(
        "#passkey-register-status-message[data-status-enum]", timeout=2000
    )
    # Did the right events fire?
    await_start_event()
    await_failure_event()


# Sometimes the browser will take a very long time to respond with the expected SecurityError, other times it works fine.
@pytest.mark.flaky(reruns=3)
def test_register_credential__fail_bad_rpid(
    live_server,
    django_db_serialized_rollback,
    settings,
    page,
    playwright_force_login,
    user,
    cdpsession,
    virtual_authenticator,
    wait_for_javascript_event,
):
    settings.OTP_WEBAUTHN_RP_ID = "example.com"
    playwright_force_login(user)

    # Create a virtual authenticator and listen for the credentialAdded event
    virtual_authenticator(VirtualAuthenticator.internal())

    page.goto(live_server.url)
    await_start_event = wait_for_javascript_event(JS_EVENT_REGISTER_START)
    await_failure_event = wait_for_javascript_event(JS_EVENT_REGISTER_FAILED)
    register_button = page.locator("button#passkey-register-button")
    expect(register_button).to_be_visible()

    register_button.click()
    page.wait_for_selector(
        f"#passkey-register-status-message[data-status-enum='{StatusEnum.SECURITY_ERROR.value}']",
        timeout=2000,
    )
    # Did the right events fire?
    await_start_event()
    await_failure_event()
