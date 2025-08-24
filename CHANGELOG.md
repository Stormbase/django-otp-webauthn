# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - UNRELEASED

### Added

- Allow customizing the selector used to find the "next" field containing the URL to redirect to after successful Passkey authentication. This can be done using the new `next_field_selector` argument to the `render_otp_webauthn_auth_scripts` template tag. ([#78](https://github.com/Stormbase/django-otp-webauthn/pull/78) by [bprobian](https://github.com/bprobian))

### Changed

- Nothing yet

### Fixed

- Nothing yet

## [0.6.0] - 2025-05-03

### Added

- Add documentation for nearly all features and settings to the [Sphinx documentation site](https://django-otp-webauthn.readthedocs.io/en/stable/) ([#61](https://github.com/Stormbase/django-otp-webauthn/pull/61) by [activus-d](https://github.com/activus-d))
- Add support for [Related Origin Requests](https://www.w3.org/TR/webauthn-3/#sctn-related-origins), a feature defined in the level 3 working draft of the WebAuthn specification. It makes simple, cross-domain sharing of Passkeys possible ([#62](https://github.com/Stormbase/django-otp-webauthn/pull/62) by [Stormheg](https://github.com/Stormheg))
- Add support for redirecting after Passkey authentication by reading a `next` url parameter from the current view ([#64](https://github.com/Stormbase/django-otp-webauthn/pull/64) by [atlasrealm](https://github.com/atlasrealm))

## [0.5.0] - 2025-02-27

### Added

- Add support for Django 5.2 pending its final release ([#58](https://github.com/Stormbase/django-otp-webauthn/pull/58) by [Stormheg](https://github.com/Stormheg))
- All Python code is now 100% covered by tests ([#32](https://github.com/Stormbase/django-otp-webauthn/pull/32), [#33](https://github.com/Stormbase/django-otp-webauthn/pull/34), [#35](https://github.com/Stormbase/django-otp-webauthn/pull/35), [#36](https://github.com/Stormbase/django-otp-webauthn/pull/36) by [Stormheg](https://github.com/Stormheg))
- Browser automation tests using Playwright and Chromium have been added to ensure the JavaScript implementation works as expected ([#39](https://github.com/Stormbase/django-otp-webauthn/pull/39), [#43](https://github.com/Stormbase/django-otp-webauthn/pull/43) by [Stormheg](https://github.com/Stormheg))

### Fixed

- The API views provided now explicitly indicate they only render JSON, disabling the browsable API (see [#55](https://github.com/Stormbase/django-otp-webauthn/issues/55) and [#56](https://github.com/Stormbase/django-otp-webauthn/pull/56), by [atlasrealm](https://github.com/atlasrealm))
- Fixed an issue where the display name of a Passkey would have the username between parenthesis for users that have both an empty `first_name` and `last_name`.

### Changed

- **Noteworthy:** the way [WebAuthn user handles](https://www.w3.org/TR/webauthn-3/#user-handle) are generated has been changed to make them more privacy-friendly. There should be no breaking backward-compatibility issues. ([#44](https://github.com/Stormbase/django-otp-webauthn/pull/4) by [Stormheg](https://github.com/Stormheg))
  - For context: these are used by the browser to identify if it already has a Passkey stored for a given user account.
- After registering a new Passkey, users are now automatically marked as 'mfa verified' in the context of `django_otp.login` ([#57](https://github.com/Stormbase/django-otp-webauthn/pull/57) by [atlasrealm](https://github.com/atlasrealm))
- The default JavaScript implementation is now built using Node 22
- The default JavaScript implementation for interacting with the browser api has been updated to use [`@simplewebauthn/browser` v13.1.0](https://github.com/MasterKale/SimpleWebAuthn/releases/tag/v13.1.0)

## [0.4.0] - 2024-10-27

### Added

- An extra system check was added to prevent misconfiguration of `OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS` ([#27](https://github.com/Stormbase/django-otp-webauthn/pull/27) by [Stormheg](https://github.com/Stormheg))

### Fixed

- Explicitly define `AllowAny` permission class for API views ([#19](https://github.com/Stormbase/django-otp-webauthn/pull/19) by [nijel](https://github.com/nijel))
- Make `WebAuthnCredentialManager` inherit from `DeviceManager` ([#23](https://github.com/Stormbase/django-otp-webauthn/pull/23) by [nijel](https://github.com/nijel))
- Clarify `username_field_selector` example in README ([#20](https://github.com/Stormbase/django-otp-webauthn/pull/20) by [nijel](https://github.com/nijel))
- Clarify custom credential model usage instructions ([#26](https://github.com/Stormbase/django-otp-webauthn/pull/26) by [jmichalicek](https://github.com/jmichalicek))
- Avoid logging None as exception in the py_webauthn exception rewriter ([#28](https://github.com/Stormbase/django-otp-webauthn/pull/28) by [nijel](https://github.com/nijel))
- A crash during Passkey registration was fixed when custom list of supported algorithms was used ([#27](https://github.com/Stormbase/django-otp-webauthn/pull/27) by [Stormheg](https://github.com/Stormheg))
- You can now call `as_credential_descriptors` on a queryset of `WebAuthnCredential` objects ([#27](https://github.com/Stormbase/django-otp-webauthn/pull/27) by [Stormheg](https://github.com/Stormheg))

### Changed

- The custom `__str__` representation for `WebAuthnCredential` is removed because displaying a AAGUID is not a friendly representation. It now defaults back to the django-otp default: `name + (username)`([#27](https://github.com/Stormbase/django-otp-webauthn/pull/27) by [Stormheg](https://github.com/Stormheg))
- The default `ModelAdmin` for `WebAuthnCredential` credential is no longer automatically registered. ([#27](https://github.com/Stormbase/django-otp-webauthn/pull/27) by [Stormheg](https://github.com/Stormheg))

  - You can instead register it manually in your `admin.py` file

    ```python
    # admin.py
    from django.contrib import admin
    from django_otp_webauthn.admin import WebAuthnCredentialAdmin
    from django_otp_webauthn.models import WebAuthnCredential

    admin.site.register(WebAuthnCredential, WebAuthnCredentialAdmin)
    ```

## [0.3.0] - 2024-08-03

### Changed

- The built-in Passkey registration and verification views error handling has been reworked. ([#12](https://github.com/Stormbase/django-otp-webauthn/pull/12) by [Stormheg](https://github.com/Stormheg))

### Fixed

- A regression in v0.2.0 was fixed were `AuthenticationDisabled` would incorrectly be raised. (Issue [#10](https://github.com/Stormbase/django-otp-webauthn/issues/10) by [jmichalicek](https://github.com/jmichalicek); fixed in [#12](https://github.com/Stormbase/django-otp-webauthn/pull/12) by [Stormheg](https://github.com/Stormheg))
- Support for `CSRF_USE_SESSIONS = True` was added. (Issue [#14](https://github.com/Stormbase/django-otp-webauthn/issues/14) by [nijel](https://github.com/nijel); fixed in [#15](https://github.com/Stormbase/django-otp-webauthn/issues/15) by [nijel](https://github.com/nijel) and [Stormheg](https://github.com/Stormheg))
- An issue that prevented MySQL from being used as the database backend was fixed. (Issue [#17](https://github.com/Stormbase/django-otp-webauthn/issues/17) by [nijel](https://github.com/nijel); fixed in [#18](https://github.com/Stormbase/django-otp-webauthn/issues/18) by [Stormheg](https://github.com/Stormheg))

### Removed

- The unused `RegistrationDisabled`, `AuthenticationDisabled`, and `LoginRequired` exceptions are removed. ([#12](https://github.com/Stormbase/django-otp-webauthn/pull/12) by [Stormheg](https://github.com/Stormheg))

## [0.2.0] - 2024-07-18

### Changed

- Support for having multiple `AUTHENTICATION_BACKENDS` was added. ([#8](https://github.com/Stormbase/django-otp-webauthn/pull/8) by [jmichalicek](https://github.com/jmichalicek))
  - **Action required:** add `django_otp_webauthn.backends.WebAuthnBackend` to your `AUTHENTICATION_BACKENDS` setting if you want to use passwordless login.

## [0.1.3] - 2024-07-01

### Added

- The default manager for the `WebAuthnCredential` model now includes a `as_credential_descriptors` method to make it easier to format the credentials for use in custom implementations.

### Fixed

- A bug was fixed with Python 3.11 and older that caused an exception when authenticating with a WebAuthn credential. ([#6](https://github.com/Stormbase/django-otp-webauthn/pull/6) by [jmichalicek](https://github.com/jmichalicek))

### Changed

- The `http://localhost:8000` default value for `OTP_WEBAUTHN_ALLOWED_ORIGINS` was removed.
- Use more appropriate examples for the `OTP_WEBAUTHN_*` settings in the README.
- Update admonition in the README to reflect the current state of the project. We have moved from don't use in production to use at your own risk.

## [0.1.2] - 2024-06-12

### Fixed

- The helper classes' `get_credential_display_name` and `get_credential_name` methods are now correctly called. Previously, the users' full name was being used as the credential name, bypassing above methods.

### Changed

- Set discoverable credential policy to `required` at registration time when `OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN` is set to `True`. This is to ensure a credential capable of passwordless login is created.

### New

- Make is easier to override the helper class using the new `OTP_WEBAUTHN_HELPER_CLASS` setting. Pass it a dotted path to your custom helper class and it will be used instead of the default one.

## [0.1.1] - 2024-05-26

### Fixed

- An issue with the button label not showing any text was fixed.

### Changed

- `WebAuthnCredential` now inherits from `django_otp.models.TimestampMixin` to add a `created_at` and `last_used_at` fields. Subsequently, this raises the minimum `django-otp` version to `1.4.0+`.

### Maintenance

- Switch to [`hatch`](https://hatch.pypa.io/) for managing the project.

## [0.1.0] - 2024-05-12

- Initial release.
