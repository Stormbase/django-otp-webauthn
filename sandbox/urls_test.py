from django.urls import path

from . import views_test

app_name = "testsuite"

urlpatterns = [
    path(
        "login-passkey-custom-next-input/",
        views_test.LoginWithPasskeyCustomNextInputView.as_view(),
        name="login-passkey-custom-next-input",
    ),
    path(
        "async-login-required/",
        views_test.async_login_required_view,
        name="async-login-required",
    ),
]
