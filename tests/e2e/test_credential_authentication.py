from django.urls import reverse
from playwright.sync_api import expect
from webauthn import base64url_to_bytes

from tests.e2e.fixtures import StatusEnum, VirtualAuthenticator, VirtualCredential
from tests.factories import WebAuthnCredentialFactory

JS_EVENT_VERIFICATION_START = "otp_webauthn.verification_start"
JS_EVENT_VERIFICATION_COMPLETE = "otp_webauthn.verification_complete"
JS_EVENT_VERIFICATION_FAILED = "otp_webauthn.verification_failed"


def test_authenticate_credential__internal_passwordless_manual(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
):
    """Verify authentication with an 'internal' authenticator credential works
    by manually clicking the 'Authenticate with Passkey' button."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey"))

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # We should navigate back to the index page
    page.wait_for_url(live_server.url + reverse("index"))

    assert user.username in page.content()


def test_authenticate_credential__manual_signal_no_credential(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    wait_for_javascript_event,
    wait_for_console_message,
):
    """Verify that manually using the 'Authenticate with Passkey' button with a credential
    that does not exist signals an unknown credential to the browser."""

    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Remove the credential to simulate it was not found / unknown
    credential.delete()

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey"))
    await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()
    expected_url = live_server.url + reverse(
        "otp_webauthn:credential-authentication-complete"
    )

    # Looks for this message in the console log to confirm the signaling happened
    await_credential_not_found_message = wait_for_console_message(
        r"Credential not found", level="trace"
    )

    with page.expect_response(expected_url, timeout=5000) as response_info:
        assert response_info.value.status == 404  # Credential was not found

    # We must wait for the failure event. The signaling happens before the
    # failure event, so we know for sure is must have happened. If we don't wait
    # in this indirect way, we will block forever waiting for the console
    # message and timeout.
    await_failure_event()

    # If this does not return, most likely `auth.ts/signalPasskeyMissing()`
    # returned early and did not post a console message confirming the
    # signaling happened. We check for console messages because there is
    # no other way to confirm this using Chrome DevTools Protocol.
    message = await_credential_not_found_message()

    # Check the message contains the right arguments - the assumption is that
    # if the arguments are correct, the signaling was called correctly.
    message_values = message.args[1].json_value()
    assert message_values["rpId"] == "localhost"
    assert credential.credential_id == base64url_to_bytes(
        message_values["credentialId"]
    )


def test_authenticate_credential__manual_disable_signal_no_credential(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    wait_for_javascript_event,
    wait_for_console_message,
    settings,
):
    """Verify that manually using the 'Authenticate with Passkey' button with a credential with
    a credential that does not exist does NOT signal an unknown credential to the browser
    when ``OTP_WEBAUTHN_SIGNAL_UNKNOWN_CREDENTIAL = False``."""
    settings.OTP_WEBAUTHN_SIGNAL_UNKNOWN_CREDENTIAL = False
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Remove the credential to simulate it was not found / unknown
    credential.delete()

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey"))
    await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()
    expected_url = live_server.url + reverse(
        "otp_webauthn:credential-authentication-complete"
    )

    # Looks for this message in the console log to confirm the signaling happened
    await_credential_not_found_message = wait_for_console_message(
        r"Not signaling unknown credential to the browser as per configuration",
        level="trace",
    )

    with page.expect_response(expected_url, timeout=5000) as response_info:
        assert response_info.value.status == 404  # Credential was not found

    # We must wait for the failure event. The signaling happens before the
    # failure event, so we know for sure is must have happened. If we don't wait
    # in this indirect way, we will block forever waiting for the console
    # message and timeout.
    await_failure_event()

    # If this does not return, most likely `auth.ts/signalPasskeyMissing()`
    # returned early and did not post a console message confirming the
    # signaling happened. We check for console messages because there is
    # no other way to confirm this using Chrome DevTools Protocol.
    await_credential_not_found_message()


def test_authenticate_credential__internal_passwordless_using_autofill(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
):
    """Verify authentication with an 'internal' authenticator credential works
    by having the browser perform autofill on a username/password form."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("auth:login"))

    # The browser should now prompt the user to autofill the passwordless credential.
    # This prompt is immediately accepted, so we should be redirected back to the index page.
    # We should navigate back to the index page
    page.wait_for_url(live_server.url + reverse("index"))

    assert user.username in page.content()


def test_authenticate_credential__passwordless_signal_no_credential(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    wait_for_javascript_event,
    wait_for_console_message,
):
    """Verify that using autofill with a credential that does not exist
    signals an unknown credential to the browser."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Remove the credential to simulate it was not found / unknown
    credential.delete()

    # Looks for this message in the console log to confirm the signaling happened
    await_credential_not_found_message = wait_for_console_message(
        r"Credential not found", level="trace"
    )
    # Visit the login page with the autofill form
    expected_url = live_server.url + reverse(
        "otp_webauthn:credential-authentication-complete"
    )
    with page.expect_response(expected_url, timeout=5000) as response_info:
        page.goto(live_server.url + reverse("auth:login"))
        await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)
        assert response_info.value.status == 404  # Credential was not found

    # We must wait for the failure event. The signaling happens before the
    # failure event, so we know for sure is must have happened. If we don't wait
    # in this indirect way, we will block forever waiting for the console
    # message and timeout.
    await_failure_event()

    # If this does not return, most likely `auth.ts/signalPasskeyMissing()`
    # returned early and did not post a console message confirming the
    # signaling happened. We check for console messages because there is
    # no other way to confirm this using Chrome DevTools Protocol.
    message = await_credential_not_found_message()

    # Check the message contains the right arguments - the assumption is that
    # if the arguments are correct, the signaling was called correctly.
    message_values = message.args[1].json_value()
    assert message_values["rpId"] == "localhost"
    assert credential.credential_id == base64url_to_bytes(
        message_values["credentialId"]
    )


def test_authenticate_credential__internal_second_factor_fails_when_credential_is_disabled(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    wait_for_javascript_event,
):
    credential = WebAuthnCredentialFactory(
        user=user, discoverable=True, confirmed=False
    )
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey"))

    await_start_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_START)
    await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # Login fails, this credential is marked as disabled
    status_message = page.locator(
        f"#passkey-verification-status-message[data-status-enum='{StatusEnum.SERVER_ERROR}']"
    )

    expect(status_message).to_be_visible()

    assert "marked as disabled" in status_message.inner_text()

    # Did the right events fire?
    await_start_event()
    await_failure_event()


def test_authenticate_credential__u2f_passwordless_fails(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    wait_for_javascript_event,
):
    """Verify authentication with a U2F authenticator credential fails when not logged in yet."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=False)
    authenticator = virtual_authenticator(VirtualAuthenticator.u2f())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey"))

    await_start_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_START)
    await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # Login should fail, this is a U2F credential that requires the server to
    # provide a list of credential ids which we are not willing to do, as the
    # user is not authenticated.
    # As a result, the login attempt fails.
    page.wait_for_selector(
        f"#passkey-verification-status-message[data-status-enum='{StatusEnum.NOT_ALLOWED_OR_ABORTED}']",
        timeout=5000,
    )

    # Did the right events fire?
    await_start_event()

    # Did we fail for the right reason?
    res = await_failure_event()
    assert res["fromAutofill"] is False
    assert res["error"].name == "NotAllowedError"


def test_authenticate_credential__u2f_second_factor(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    playwright_force_login,
):
    """Verify authentication with a U2F authenticator credential works if used
    by an already authenticated user as  form of second factor."""
    # We must be authenticated already to use this credential, because the
    # server will provide us with the credential id we need for U2F to function.
    playwright_force_login(user)
    credential = WebAuthnCredentialFactory(user=user, discoverable=False, transports=[])
    authenticator = virtual_authenticator(VirtualAuthenticator.u2f())
    authenticator_id = authenticator["authenticatorId"]

    credential_data = VirtualCredential.from_model(credential, require_u2f=True)

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, credential_data)

    page.goto(live_server.url + reverse("second-factor-verification"))

    verify_button = page.locator("button#passkey-verification-button")
    expect(verify_button).to_be_visible()

    verify_button.click()

    # Login should succeed and return us to the index page
    page.wait_for_url(live_server.url + reverse("index"))


def test_authenticate_credential_second_factor_no_available_device(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
    playwright_force_login,
    wait_for_javascript_event,
):
    """Verify authentication with a U2F authenticator credential fails when no device is available."""
    playwright_force_login(user)

    # This credential belongs to someone else, we can't use it for authentication
    credential = WebAuthnCredentialFactory(discoverable=False, transports=[])
    assert credential.user != user

    authenticator = virtual_authenticator(VirtualAuthenticator.u2f())
    authenticator_id = authenticator["authenticatorId"]

    credential_data = VirtualCredential.from_model(credential, require_u2f=True)

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, credential_data)

    page.goto(live_server.url + reverse("second-factor-verification"))
    await_start_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_START)
    await_failure_event = wait_for_javascript_event(JS_EVENT_VERIFICATION_FAILED)

    verify_button = page.locator("button#passkey-verification-button")
    expect(verify_button).to_be_visible()

    verify_button.click()

    page.wait_for_selector(
        f"#passkey-verification-status-message[data-status-enum='{StatusEnum.NOT_ALLOWED_OR_ABORTED}']",
        timeout=5000,
    )

    # Did the right events fire?
    await_start_event()

    # Did we fail for the right reason?
    res = await_failure_event()
    assert res["fromAutofill"] is False
    assert res["error"].name == "NotAllowedError"


def test_authenticate_credential__next_url_parameter(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
):
    """Verify we can use the next URL parameter to redirect to a different page after authentication."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey") + "?next=/next-url/")

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # We should navigate to the url specified in the next parameter
    page.wait_for_url(live_server.url + "/next-url/")


def test_authenticate_credential__next_input_element(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
):
    """Verify we can use a input named next on the page to redirect to a different page after authentication."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("login-passkey") + "?next_input=/next-input/")

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # We should navigate to the url specified in the next parameter
    page.wait_for_url(live_server.url + "/next-input/")


def test_authenticate_credential__custom_next_input_element(
    live_server,
    django_db_serialized_rollback,
    page,
    user,
    virtual_authenticator,
    virtual_credential,
):
    """Verify we can use a input named next on the page to redirect to a different page after authentication."""
    credential = WebAuthnCredentialFactory(user=user, discoverable=True)
    authenticator = virtual_authenticator(VirtualAuthenticator.internal())
    authenticator_id = authenticator["authenticatorId"]

    # Create a virtual credential from our database model
    virtual_credential(authenticator_id, VirtualCredential.from_model(credential))

    # Go to the login with passkey page
    page.goto(live_server.url + reverse("testsuite:login-passkey-custom-next-input"))

    # Find the 'volgende' input and take its value, to confirm we redirect to that URL
    volgende_input = page.locator("input[name='volgende']")
    next_value = volgende_input.input_value()

    login_button = page.locator("button#passkey-verification-button")
    expect(login_button).to_be_visible()

    login_button.click()

    # We should now land on the URL specified in the 'volgende' input
    page.wait_for_url(live_server.url + next_value)
