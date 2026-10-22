"""Views only used by the testsuite, not actually by the sandbox app."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView


class LoginWithPasskeyCustomNextInputView(TemplateView):
    """A view with a template that has a custom next_field_selector input field.

    Used to test that the next_field_selector option in the render_otp_webauthn_auth_scripts
    template tag works as expected.
    """

    template_name = "sandbox/login_passkey_custom_next_input.html"


@login_required
async def async_login_required_view(request):
    """An async view, which loads the user through the async authentication backend API.

    Used to test that a user who logged in with a Passkey can use async views.
    """
    user = await request.auser()
    return JsonResponse({"user_id": user.pk})
