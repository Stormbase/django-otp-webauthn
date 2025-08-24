"""Views only used by the testsuite, not actually by the sandbox app."""

from django.views.generic import TemplateView


class LoginWithPasskeyCustomNextInputView(TemplateView):
    """A view with a template that has a custom next_field_selector input field.

    Used to test that the next_field_selector option in the render_otp_webauthn_auth_scripts
    template tag works as expected.
    """

    template_name = "sandbox/login_passkey_custom_next_input.html"
