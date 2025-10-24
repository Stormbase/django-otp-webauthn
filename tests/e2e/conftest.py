import random
import re
from concurrent.futures import Future

import pytest
from django.test.client import Client as DjangoTestClient
from playwright.sync_api import CDPSession

from tests.e2e.fixtures import VirtualAuthenticator, VirtualCredential


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


@pytest.fixture
def cdpsession(page) -> CDPSession:
    session = page.context.new_cdp_session(page)
    session.send("WebAuthn.enable")
    return session


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
        nook = "".join([chr(97 + random.randint(0, 25)) for _ in range(25)])  # noqa: S311 (not used for secure purposes)

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
def wait_for_console_message(page):
    """Returns a function that blocks until a certain console message has been posted."""

    def _wait_for_console_message(message_text_regex: str, *, level="log"):
        future = FutureWrapper()

        def _handle_console_message(msg):
            if msg.type == level and re.match(message_text_regex, msg.text):
                future.set_result(msg)

        page.on("console", _handle_console_message)

        def _return():
            return future.get_result()

        return _return

    return _wait_for_console_message


@pytest.fixture
def virtual_authenticator(cdpsession):
    def _get_authenticator(authenticator: VirtualAuthenticator):
        resp = cdpsession.send(
            "WebAuthn.addVirtualAuthenticator",
            {
                "options": authenticator.as_cdp_options(),
            },
        )
        return resp

    return _get_authenticator


@pytest.fixture
def virtual_credential(cdpsession):
    def _get_credential(authenticator_id: str, credential: VirtualCredential):
        data = {
            "authenticatorId": authenticator_id,
            "credential": credential.as_cdp_options(),
        }
        resp = cdpsession.send("WebAuthn.addCredential", data)
        return resp

    return _get_credential


@pytest.fixture
def playwright_manipulate_session(live_server, context):
    """Fixture that allows direct manipulation of the session.

    Usage:
        def my_pytest_playwright_testcase(live_server, page, playwright_manipulate_session):
            # Update or add a specific key:
            playwright_manipulate_session(lambda session: session.update({"some_key": "some_value"}))

            # Remove a specific key:
            playwright_manipulate_session(lambda session: session.pop("some_key", None))

            # Clear the session entirely:
            playwright_manipulate_session(lambda session: session.clear())

            # Navigate the live server as normal, with the updated session:
            page.goto(live_server.url)
    """

    def _playwright_manipulate_session(modify_func):
        # Get the session id cookie from the browser context
        session_cookie_value = None
        for cookie in context.cookies():
            if cookie["name"] == "sessionid":
                session_cookie_value = cookie["value"]
                break

        # Instantiate a Django test client to gain access to the SessionStore
        # and load the session if we already have one
        client = DjangoTestClient()
        if session_cookie_value:
            client.cookies["sessionid"] = session_cookie_value

        session = client.session

        # let the caller modify the session
        modify_func(session)

        session.save()
        # Update the browser context with the new session id cookie
        context.add_cookies(
            [
                {
                    "url": live_server.url,
                    "name": "sessionid",
                    "value": session.session_key,
                }
            ]
        )

    return _playwright_manipulate_session


@pytest.fixture
def playwright_force_login(live_server, context, playwright_manipulate_session):
    """Fixture that forces the given user to be logged in by manipulating the session cookie."""

    def _playwright_force_login(user):
        login_helper = DjangoTestClient()
        login_helper.force_login(user)

        playwright_manipulate_session(
            lambda session: session.update(login_helper.session.items())
        )

    return _playwright_force_login
