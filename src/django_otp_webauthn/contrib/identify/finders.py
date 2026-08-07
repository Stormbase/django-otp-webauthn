from importlib.util import find_spec
from pathlib import Path

from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage

PACKAGE = "identify_passkey.icons"
STATIC_PATH_PREFIX = "django_otp_webauthn/passkey-icons"


class PasskeyIconsFinder(FileSystemFinder):
    """A staticfiles finder that finds any icons under the ``identify_passkey.icons``
    package and collects them under the ``django_otp_webauthn/passkey-icons``
    static file prefix.

    This allows icons from the ``identify-passkey`` package to be served as
    static files in a Django project.
    """

    def __init__(self, *args, **kwargs):
        # No need to check for import errors, there is a system check in place
        # that will warn if the package is not installed.
        spec = find_spec(PACKAGE)
        self.locations = [
            (STATIC_PATH_PREFIX, Path(location))
            for location in spec.submodule_search_locations
        ]

        self.storages = {}

        for prefix, root in self.locations:
            storage = FileSystemStorage(location=root)
            storage.prefix = prefix
            self.storages[root] = storage
