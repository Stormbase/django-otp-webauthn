.. _customizing-behavior:

Customizing behavior
====================

Django OTP WebAuthn is designed to work out of the box while remaining flexible enough to accommodate the specific requirements of large applications.

The key areas where you can tailor the library's behavior to meet your needs are as follows:

Customizing views
------------------------

You can override the built-in Django OTP WebAuthn views to use your own implementations. This lets you to:

* **Handle side effects:** Perform additional actions, such as updating an audit log, when registering or using a :term:`passkey`.
* **Control passkey availability:** Enforce conditions for registering or using passkeys. For example, you could require users to set up account recovery mechanisms before enabling passkeys.

To learn how to customize your Django views, see :ref:`Customize views <customize-views>`.

Customizing the helper class
----------------------------

The helper class acts as a wrapper for interacting with the underlying ``py_webauthn`` library. You can customize this class for the following purposes:

* Extend the WebAuthn implementation to support additional features.

* Modify how credentials are saved to suit your application's requirements.

* Change the way user account names are assigned during passkey registration.

* Adapt or extend parts of the WebAuthn processes to fit your specific use case.

* Configure options such as attestation conveyance preference and :term:`authenticator` attachment to match your application's security policies.

To learn how to customize the helper class, see :ref:`Customize helper class <customize-helper-class>`.

Customizing credential and attestation models
---------------------------------------------

To add additional fields or features to credentials and attestations, you can extend the base models provided by Django OTP WebAuthn. This is useful if your application requires storing custom data alongside :term:`WebAuthn credentials <WebAuthn credential>` or attestations.

To learn how to customize your models, see :ref:`Customize models <customize-models>`.

Customizing frontend
--------------------

The frontend implementation in this library supports customization only through CSS. For any additional customization, you have to create your own implementation. As long as you call the same API endpoints and use the same JSON structure, you can still use all other components of this package, including views and models.


.. toctree::
    :maxdepth: 2
    :hidden:

    Customize views <customize_views.rst>
    Customize helper class <customize_helper_class.rst>
    Customize models <customize_models.rst>
