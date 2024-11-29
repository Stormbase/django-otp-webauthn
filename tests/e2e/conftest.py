import random
from concurrent.futures import Future

import pytest
from django.test.client import Client as DjangoTestClient
from playwright.sync_api import CDPSession

from tests.e2e.fixtures import VirtualAuthenticator


class FutureWrapper:
    def __init__(self):
        self.future = Future()

    def get_result(self):
        return self.future.result(timeout=5)

    def set_result(self, value):
        self.future.set_result(value)


@pytest.fixture
def event_waiter():
    def _event_waiter():
        future = FutureWrapper()
        return future.get_result, future.set_result

    return _event_waiter


@pytest.fixture(scope="function")
def cdpsession(page) -> CDPSession:
    return page.context.new_cdp_session(page)


@pytest.fixture(autouse=True)
def configure_otp_webauthn(settings, live_server):
    settings.OTP_WEBAUTHN_RP_NAME = "OTP WebAuthn Testsuite"
    settings.OTP_WEBAUTHN_RP_ID = "localhost"
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = [live_server.url]


@pytest.fixture
def wait_for_javascript_event(page):
    """Returns a function that blocks until a JavaScript event has been fired."""

    def _wait_for_javascript_event(event_name: str):
        # Hot mess - why is there no Playwright API for this?

        # We need to generate a unique name for the nook to store the event result in
        nook = "".join([chr(97 + random.randint(0, 25)) for _ in range(25)])

        # Setup the listener, that stores the event detail in the nook
        page.evaluate(f"""
            window._event_{nook} = undefined;
            document.addEventListener("{event_name}", event => {{
                console.log("Event fired", event);
                window._event_{nook} = event.detail;
            }});
        """)

        # Return a function that will block until the event has been fired and
        # the detail has been stored in the nook. It is indirect like this
        # because we circumvent the Content Security Policy that is active for
        # the sandbox.
        def _return():
            page.wait_for_function(
                "payload => payload !== undefined",
                arg="window._event_" + nook,
                timeout=5000,
            )
            return page.evaluate("window._event_" + nook)

        return _return

    return _wait_for_javascript_event


@pytest.fixture
def virtual_authenticator(cdpsession):
    def _get_authenticator(authenticator: VirtualAuthenticator):
        cdpsession.send("WebAuthn.enable")
        resp = cdpsession.send(
            "WebAuthn.addVirtualAuthenticator",
            {
                "options": authenticator.as_cdp_options(),
            },
        )
        return resp

    return _get_authenticator


@pytest.fixture
def playwright_force_login(live_server, context):
    """Fixture that forces the given user to be logged in by manipulating the session cookie."""

    def _playwright_force_login(user):
        login_helper = DjangoTestClient()
        login_helper.force_login(user)

        context.add_cookies(
            [
                {
                    "url": live_server.url,
                    "name": "sessionid",
                    "value": login_helper.cookies["sessionid"].value,
                }
            ]
        )
        return user

    return _playwright_force_login
