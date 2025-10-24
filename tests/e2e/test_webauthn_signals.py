import pytest
from playwright.sync_api import expect

from tests.factories import WebAuthnCredentialFactory


def test_webauthn_signals_triggered(
    live_server,
    django_db_serialized_rollback,
    page,
    playwright_force_login,
    playwright_manipulate_session,
    user,
    wait_for_console_message,
):
    """Verify the ``PublicKeyCredential.signalCurrentUserDetails`` and
    ``PublicKeyCredential.signalAllAcceptedCredentials`` browser signals are
    triggered.
    """

    playwright_force_login(user)
    playwright_manipulate_session(
        lambda session: session.update({"otp_webauthn_sync_needed": True})
    )

    # Create some credentials for the user
    WebAuthnCredentialFactory(user=user)
    WebAuthnCredentialFactory(user=user)

    # Set up signal waiters
    await_signal_accepted_credentials = wait_for_console_message(
        r"Signaled accepted credentials to the browser."
    )
    await_signal_user_details = wait_for_console_message(
        r"Signaled current user details to the browser."
    )

    page.goto(live_server.url)

    # Since we updated the session to indicate user details were requested,
    # the page should have a script tag with the config in it. It it does not
    # there isn't any point continuing the test.
    expect(page.locator("script[id='otp_webauthn_sync_signals_config']")).to_be_hidden()

    # Double check that PublicKeyCredential.signalCurrentUserDetails and
    # PublicKeyCredential.signalAllAcceptedCredentials apis are available in this browser
    assert page.evaluate("() => 'signalCurrentUserDetails' in PublicKeyCredential"), (
        "PublicKeyCredential.signalCurrentUserDetails does not exist in this browser, cannot test this feature!"
    )
    assert page.evaluate(
        "() => 'signalAllAcceptedCredentials' in PublicKeyCredential"
    ), (
        "PublicKeyCredential.signalAllAcceptedCredentials does not exist in this browser, cannot test this feature!"
    )

    # Wait for the signals to be sent
    try:
        await_signal_accepted_credentials()
    except TimeoutError:
        pytest.fail(
            "sync_signals.ts did not post console message indicating PublicKeyCredential.signalAllAcceptedCredentials was called."
        )
    try:
        await_signal_user_details()
    except TimeoutError:
        pytest.fail(
            "sync_signals.ts did not post console message indicating PublicKeyCredential.signalCurrentUserDetails was called."
        )
