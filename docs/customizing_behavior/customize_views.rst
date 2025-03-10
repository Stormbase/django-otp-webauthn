.. _customize-views:

Customize views
===============

Django OTP WebAuthn has four built-in views that manage registration and authentication. While these views provide default behavior, you can subclass them to meet specific requirements. For example, you can restrict registration based on custom conditions or add logging mechanisms during the authentication process.

Django OTP WebAuthn provides the following built-in views:

* ``BeginCredentialRegistrationView``

* ``CompleteCredentialRegistrationView``

* ``BeginCredentialAuthenticationView``

* ``CompleteCredentialAuthenticationView``

Create custom views
-------------------

To customize a view, subclass the relevant base class and override its methods. For more information, see the reference documentation on :ref:`Views <views>`.

For example, you can restrict :term:`passkey` registration by modifying the code in your ``<your-app>/views`` file like this:

.. code-block:: py

    from django_otp_webauthn.views import BeginCredentialRegistrationView as BaseBeginCredentialRegistration
    from django_otp_webauthn.exceptions import OTPWebAuthnApiError

    class PasskeyRegistrationUnavailableError(OTPWebAuthnApiError):
    	...

    class MyCustomBeginCredentialRegistrationView(BaseBeginCredentialRegistration):
    	def check_can_register(self):
    		user = self.get_user()

    # Perform some checks that may stop a user from registering
    # and raise a Django Rest Framework API error
    	if your_function_that_does_something(user)...:
            raise PasskeyRegistrationUnavailableError()

Register custom views
---------------------

To use your custom views, register their URLs in place of the URL patterns provided by Django OTP WebAuthn:

.. code-block:: py

    from django.urls import path
    from yourapp.views import MyCustomBeginCredentialRegistrationView

    urlpatterns = [
        # Place your customized view *before*
        # the django_otp_webauthn.urls include
        path(
                "webauthn/registration/begin/",
                MyCustomBeginCredentialRegistrationView.as_view(),
                name="credential-registration-begin"
            ),
        path(
                "webauthn/",
                include("django_otp_webauthn.urls",
                namespace="otp_webauthn")
            ),
    ]
