from django.urls import path

from . import views_test

app_name = "testsuite"

urlpatterns = [
    path(
        "tests-only/login-passkey-custom-next-input/",
        views_test.LoginWithPasskeyCustomNextInputView.as_view(),
        name="login-passkey-custom-next-input",
    ),
]
