.. _keep_passkeys_in_sync:

How-to: keep user details in sync with passkeys
===============================================

When your users make changes to their details, such as their email address or
username, these changes won't automatically be reflected in the passkeys they
have saved in their browser. This can lead to confusion as their old email or
username may still appear during passkey authentication.

To ensure a smooth user experience, it's important to keep the user details
associated with passkeys up to date. Django OTP WebAuthn has a template tag that
can help with this by calling the right browser APIs to update the stored
passkeys for you.


.. _the_render_otp_webauthn_sync_signals_scripts_template_tag:

The ``render_otp_webauthn_sync_signals_scripts`` template tag
-------------------------------------------------------------

This is a lightweight template tag that you can add to your base template. It
looks for a key in the session that indicates that user details have changed.
If so, then it renders the necessary JavaScript to update the stored Passkeys in
the user's browser. If no syncing is needed, it outputs nothing so it won't
bloat your pages.

To use the ``render_otp_webauthn_sync_signals_scripts`` template tag, add it
near the bottom of your base template, just before the closing ``</body>`` tag.
This way the template tag won't block the initial page load, but will still be
executed when the page is fully loaded.

.. code-block:: html

    <!-- base.html -->
    {% load otp_webauthn %}
    ...
    <html>
        ...
        <body>
            ...
            ...
            {% render_otp_webauthn_sync_signals_scripts %}
        </body>
    </html>

How it works
------------

When a user authenticates using a passkey or registers a new passkey, the
default authentication and registration views call
``django_otp_webauthn.utils.request_user_details_sync`` after successful
registration or authentication. This function sets a flag in the user's session
indicating that their details need to be synchronized. This is the official way
to request a user details sync from Django OTP WebAuthn.

On the next page load, the ``render_otp_webauthn_sync_signals_scripts`` template
tag sees this flag while rendering the templates. It then outputs JavaScript
that uses the appropriate WebAuthn API to update the stored Passkeys with the
latest user details. After the synchronization is complete, the flag is cleared
from the session to prevent rendering unnecessary the JavaScript on subsequent
page loads.

Remove deleted passkeys from the browser
----------------------------------------

If a user removes a passkey from your application, the removal won't
automatically be reflected in the passkeys stored in their browser. This means
that the passkey will show up the next time the user tries to authenticate.

To prevent this behavior, call the ``request_user_details_sync`` utility
function after a passkey is removed. This ensures that the next time the user
loads a page, their browser will be informed about the deleted passkey and can
remove it from storage. This may be accompanied by a prompt asking the user to
confirm the removal.

If the user tries to use a removed passkey during
authentication, the browser will be informed that the passkey is
no longer valid through the `PublicKeyCredential.signalUnknownCredential
<https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalUnknownCredential_static>`_
WebAuthn API.


How to trigger user details sync
--------------------------------

To trigger the user details synchronization process, call the
``request_user_details_sync`` utility function whenever the user's details are
updated. For example, if you have a view that allows users to update their email
address or username, then add a call to this function after the update is
successful. This ensures that the next time the user loads a page, their
passkeys will be updated with the new details.

.. code-block:: py

    # your_app/views.py
    from django_otp_webauthn.utils import request_user_details_sync

    def update_user_details(request):
        if request.method == "POST":
            # Assume we have a form that updates user details
            form = UserDetailsForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                # Request user details sync after updating details
                request_user_details_sync(request)
                # Redirect or render success response
                return redirect("profile")
        else:
            form = UserDetailsForm(instance=request.user)
        return render(request, "update_user_details.html", {"form": form})


You won't see any visible messages or indicators when the synchronization occurs, as
it happens silently in the background. However, you can check your browser's
console for any errors or logs related to the synchronization process if needed.

How it works from a technical perspective
-----------------------------------------

The ``render_otp_webauthn_sync_signals_scripts`` template tag is a convenience
wrapper that ends up calling the
``PublicKeyCredential.signalAllAcceptedCredentials`` and
``PublicKeyCredential.signalCurrentUserDetails`` WebAuthn browser APIs. It
retrieves a list of currently registered credentials and the
current user details in the format the WebAuthn browser APIs expect.

For more information about the WebAuthn browser APIs, see:

- `PublicKeyCredential.signalCurrentUserDetails <https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalCurrentUserDetails_static>`_
- `PublicKeyCredential.signalAllAcceptedCredentials <https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalAllAcceptedCredentials_static>`_

.. note::

    As of November 2025, the WebAuthn browser APIs are still new and don't enjoy
    broad support from all browsers. Please see `Web authentication signal
    methods on caniuse.com <https://caniuse.com/wf-webauthn-signals>`_ for the
    most up-to-date browser support information.
