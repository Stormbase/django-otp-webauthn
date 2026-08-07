from importlib import util


def is_identify_passkey_package_installed() -> bool:
    """Check if the 'identify_passkey' package is installed."""
    try:
        return util.find_spec("identify_passkey") is not None
    except ModuleNotFoundError:
        return False
