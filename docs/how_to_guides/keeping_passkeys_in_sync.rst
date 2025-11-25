.. _keep_passkeys_up_to_date:

Keep passkeys up to date with user details
==========================================

When users update their details, such as their email address or username, the changes don't automatically reflect in their stored :term:`passkeys <passkey/discoverable credential>`. This can cause confusion because outdated information still appears during authentication.

To keep passkeys up to date with user details, Django OTP WebAuthn provides the ``render_otp_webauthn_sync_signals_scripts`` template tag. It calls the appropriate browser APIs to update stored passkeys.


.. _what_is_render_otp_webauthn_sync_signals_scripts:

What is ``render_otp_webauthn_sync_signals_scripts``?
-----------------------------------------------------

``render_otp_webauthn_sync_signals_scripts`` is a lightweight template tag that you can add to your base template to check for a key in the session. The key indicates that user details have changed. If the template tag detects the key, it renders the JavaScript needed to update the stored passkeys in the user's browser.

To use the ``render_otp_webauthn_sync_signals_scripts`` template tag, add it near the bottom of your base template, just before the closing ``</body>`` tag. This ensures it doesn't block the initial page load, but still executes once the page is fully loaded.

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

How ``render_otp_webauthn_sync_signals_scripts`` works
------------------------------------------------------

When a user authenticates using a passkey or registers a new one, the default authentication and registration views call the ``django_otp_webauthn.utils.request_user_details_sync`` function. This function sets a flag in the user's session, indicating that their details require synchronization.

On the next page load, when the templates are rendered, ``render_otp_webauthn_sync_signals_scripts`` checks this flag and outputs JavaScript that uses the appropriate WebAuthn API to update the stored passkeys with the latest user details. After the synchronization is complete, the flag is cleared from the session to prevent rendering the JavaScript on subsequent page loads.

Remove deleted Passkeys from the browser
----------------------------------------

When a user removes a passkey from your application, the browser doesn't automatically update its stored passkeys. So, the deleted passkey may still appear the next time the user tries to authenticate.

To handle, call the ``request_user_details_sync`` utility function after you remove a passkey. This ensures that on the next page load, the browser receives the information it needs to remove the deleted passkey from storage. Depending on the browser’s implementation, the user may be prompted to confirm the removal.

If the user tries to use a removed passkey during authentication, the browser automatically determines that the passkey is
no longer valid through the `PublicKeyCredential.signalUnknownCredential
<https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalUnknownCredential_static>`_
WebAuthn API.


How to trigger user details sync
--------------------------------

To trigger the user details synchronization process, call the ``request_user_details_sync`` utility function whenever a user updates their details. For example, if you have a view that lets users change their email address or username, add a call to this function after the update succeeds. This ensures that the next time the user loads a page, their passkeys are updated with the new details.

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

The synchronization happens in the background, so you won't see any messages or indicators when it occurs. If needed, you can check your browser’s console for any errors or logs related to the synchronization process.

How does this work from a technical perspective?
------------------------------------------------

The ``render_otp_webauthn_sync_signals_scripts`` template tag is a convenience
wrapper that ends up calling the
``PublicKeyCredential.signalAllAcceptedCredentials`` and
``PublicKeyCredential.signalCurrentUserDetails`` WebAuthn browser APIs. It
automatically retrieves a list of currently registered credentials and the
current user details in the format these APIs expect.

For more information about these APIs, refer to the following resources:

- `PublicKeyCredential.signalCurrentUserDetails <https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalCurrentUserDetails_static>`_
- `PublicKeyCredential.signalAllAcceptedCredentials <https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential/signalAllAcceptedCredentials_static>`_

.. note::

    As of November 2025, these APIs are still relatively new and don't enjoy
    broad support from all browsers. Please see `Web authentication signal
    methods on caniuse.com <https://caniuse.com/wf-webauthn-signals>`_ for the
    most up-to-date browser support information.
