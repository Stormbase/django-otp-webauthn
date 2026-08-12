from django_otp_webauthn.contrib.identify.finders import PasskeyIconsFinder


class CustomPasskeyIconsFinder(PasskeyIconsFinder):
    """Custom static file finder for Passkey icons, used to check if the system check can detect subclasses of PasskeyIconsFinder."""
