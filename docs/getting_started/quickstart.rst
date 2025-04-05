.. _quickstart:

Quickstart
==========

You can start using Django OTP WebAuthn in your Django projects by following these steps:

Install Django OTP WebAuthn from PyPI
-------------------------------------

First, install Django OTP WebAuthn from PyPI by running the following command:

.. code-block:: console

    pip install django-otp-webauthn

Add it to installed apps
------------------------

Go to your ``<project>/settings.py`` file and add ``django_otp_webauthn`` to ``INSTALLED_APPS``:

.. code-block:: py

    INSTALLED_APPS = [
        ...
        "django_otp_webauthn",
        ...
    ]

Include URLs
------------

Modify your ``<project>/urls.py`` file and add the required URL configuration:

.. code-block:: py

    from django.urls import include, path

    urlpatterns = [
        ...
        path(
            "webauthn/",
            include("django_otp_webauthn.urls", namespace="otp_webauthn")
        ),
        ...
    ]

Configure settings for local and production environments
--------------------------------------------------------

If you are configuring Django OTP WebAuthn for a production environment, update your ``<project>/settings.py`` file as follows:

.. code-block:: py

    # The name of the relying party (RP).
    #This is sometimes shown to the user when they register a passkey.
    OTP_WEBAUTHN_RP_NAME = "My Website Inc."

    # This is necessary to bind the passkey to a specific domain.
    # This should be the domain of your website.
    OTP_WEBAUTHN_RP_ID = "your-domain.com"

    # This is used to check the origin of the request and
    # is used for security. It’s similar to Django's
    # CSRF_TRUSTED_ORIGINS setting.
    # The origins must always be a subdomain of
    # the RP ID or the RP ID itself.
    OTP_WEBAUTHN_ALLOWED_ORIGINS = [
        "https://your-domain.com",
        "https://subdomain.your-domain.com"
    ]

However, if you’re configuring Django OTP WebAuthn for local development, use the following settings in your ``<project>/settings.py`` file:

.. code-block:: py

    # The name of the relying party (RP). This is sometimes
    # shown to the user when they register a passkey.
    OTP_WEBAUTHN_RP_NAME = "My Website Inc."

    # This is necessary to bind the passkey to a specific
    # domain. This should be the domain of your website.
    OTP_WEBAUTHN_RP_ID = "localhost"

    # This is used to check the origin of the request and
    # is used for security. It’s similar to
    # Django's CSRF_TRUSTED_ORIGINS setting.
    # The origins must always be a subdomain
    # of the RP ID or the RP ID itself.
    OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]

Update authentication backends
------------------------------

Modify your ``<project>/settings.py`` file to use ``django_otp_webauthn.backends.WebAuthnBackend`` in ``AUTHENTICATION_BACKENDS``:

.. code-block:: py

    AUTHENTICATION_BACKENDS = [
        ...
        # Django’s default authentication backend
        "django.contrib.auth.backends.ModelBackend",
        "django_otp_webauthn.backends.WebAuthnBackend",
        ...
    ]

Add registration code
---------------------

Now add your Django OTP WebAuthn registration snippet into your project. For example, add the following code in ``account_settings.html`` or a similar page where users manage their authentication methods:

.. code-block:: html

    <!-- account_settings.html -->
    {% load otp_webauthn %}

    {% comment %}
    This template is displayed when WebAuthn registration
    is supported. The template must contain a button
    with the id `passkey-register-button`. To display status
    and error messages, include an element with the id
    `passkey-register-status-message`.
    {% endcomment %}
    <template id="passkey-registration-available-template">
        <div>
            <button type="button" id="passkey-register-button">
                Register Passkey
            </button>
            <div id="passkey-register-status-message"></div>
        </div>
    </template>

    {% comment %}
    This template is displayed when WebAuthn registration
    is not supported.
    {% endcomment %}
    <template id="passkey-registration-unavailable-template">
        <p>Sorry, your browser has no Passkey support</p>
    </template>

    {% comment %}
    This placeholder element will be replaced with either the
    contents of the `passkey-registration-available-template` or
    the `passkey-registration-unavailable-template` template.
    {% endcomment %}
    <span id="passkey-registration-placeholder"></span>

    {% comment %}
    This template tag renders all the necessary <script> tags
    for the default registration implementation
    {% endcomment %}
    {% render_otp_webauthn_register_scripts %}

Update login template for passwordless authentication
-----------------------------------------------------

Now modify your login template to turn on passkey-based login:

.. code-block:: html

    {% load otp_webauthn %}

    <form method="post">
        {% comment %} Suppose there is an username field on your page
        that has CSS selector: input[name="username"] {% endcomment %}
        <label for="id_username">Username</label>
        <input id="id_username" type="text" name="username" autocomplete="username">
        {% comment %} Other fields omitted for brevity {% endcomment %}

        {% comment %} This placeholder element will be replaced with either the
        contents of the `passkey-verification-available-template`
        or the `passkey-verification-unavailable-template` template. {% endcomment %}
        <span id="passkey-verification-placeholder"></span>

        {% comment %}
        This template is displayed when WebAuthn authentication
        is supported. Typically, you would want to display a button
        that the user can click to authenticate using a passkey.
        The template must contain a button with the id
        `passkey-verification-button`. To display status and
        error messages, include an element with the id
        `passkey-verification-status-message`.
        {% endcomment %}
        <template id="passkey-verification-available-template">
            <button type="button" id="passkey-verification-button">
                Login using a Passkey
            </button>
            <div id="passkey-verification-status-message"></div>
        </template>

        {% comment %}
        This template is displayed when WebAuthn is not supported.
        {% endcomment %}
        <template id="passkey-verification-unavailable-template">
            <p>Sorry, your browser has no Passkey support</p>
        </template>

        {% comment %}
        This template tag renders all the necessary <script> tags
        for the default verification implementation.

        To make browsers automatically suggest a passkey when you
        focus the username field, make sure `username_field_selector`
        is a valid CSS selector.

        The username_field_selector parameter is only required to
        make 'passwordless authentication' work.
        {% endcomment %}
        {% render_otp_webauthn_auth_scripts username_field_selector="input[name='username']" %}
    </form>

Migrate your database
---------------------

Finally, run the following command to apply database migrations:

.. code-block:: console

    python manage.py migrate

Now, if you configured your project for local environment and you run your server, you should see:

* a **Register Passkey** button on the login page

* a **Login using a Passkey** button on the login page
