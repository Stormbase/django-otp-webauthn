from typing import TYPE_CHECKING, Literal, NamedTuple

from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import SafeString

from .finders import STATIC_PATH_PREFIX

if TYPE_CHECKING:
    from identify_passkey import PasskeyIcon as _InternalPasskeyIcon


class PasskeyIcon(NamedTuple):
    ref: "_InternalPasskeyIcon"

    @property
    def static_url(self) -> str:
        """Django static file url to the icon file, using your configured staticfiles storage. Example: ``/static/django_otp_webauthn/passkey-icons/apple-passwords-icon.svg``"""
        return staticfiles_storage.url(f"{STATIC_PATH_PREFIX}/{self.ref.path.name}")

    @property
    def mime_type(self) -> str:
        """The MIME type of the icon file. Example: ``image/png`` or ``image/svg+xml``"""
        return self.ref.mime_type

    @property
    def theme(self) -> Literal["light", "dark"]:
        """If the icon is meant for light or dark themes. Due to poor upstream data hygiene, the same icon may be used for both themes."""
        return self.ref.theme

    @property
    def data_uri(self) -> str:
        """Data URI version of the icon. Example: ``data:image/png;base64,...``"""
        return self.ref.data_uri


class PasskeyDescriptor(NamedTuple):
    aaguid: str
    """The AAGUID of the passkey's authenticator. This is an identifier for the authenticator model that created the credential."""
    name: str
    """Human-readable name for the authenticator that created the credential."""
    icon_light: PasskeyIcon | None = None
    """Icon for light themes. May be None if no icon is available."""
    icon_dark: PasskeyIcon | None = None
    """Icon for dark themes. May be None if no icon is available."""

    def icon_data_uri(self, theme: Literal["light", "dark"] = "light") -> str | None:
        """Returns a data URI for the icon. Like ``data:image/png;base64,...`` If no icon is available, returns None.

        You can specify the ``theme`` argument ("light" or "dark") to get the corresponding icon.
        Due to poor upstream data hygiene, the same icon may be used for both themes and not match the requested theme.
        """
        if theme not in ("light", "dark"):
            raise ValueError(f"Invalid theme: {theme}. Must be 'light' or 'dark'.")

        if theme == "light" and self.icon_light is not None:
            return self.icon_light.data_uri
        if theme == "dark" and self.icon_dark is not None:
            return self.icon_dark.data_uri
        return None

    @property
    def has_icon(self) -> bool:
        """True if the passkey descriptor has at least one icon (light or dark)."""
        return self.icon_light is not None or self.icon_dark is not None

    def picture_html(
        self,
        img_attrs: dict[str, str] | None = None,
        picture_attrs: dict[str, str] | None = None,
    ) -> SafeString:
        """Returns a `prefers-color-scheme <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-color-scheme>`_
        aware HTML `<picture> <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/picture>`_
        tag for the icon, or an empty string if no icon is available.

        Args:
            img_attrs (dict[str, str] | None): Optional HTML attributes to include on the <img>. Defaults to ``{"width": "32", "alt": self.name}``.

            picture_attrs (dict[str, str] | None): Optional HTML attributes to include on the <picture> tag. Defaults to ``{}``.
        Returns:
            :class:`SafeString <django.utils.safestring.SafeString>`: The HTML <picture> tag as a SafeString, or empty string if no icon is available.

        Warning:
            The attributes are passed through :func:`django.forms.utils.flatatt`, which assumes keys are already XML escaped.
            You are responsible for ensuring that the attributes are safe – don't allow user controllable data to be
            passed in here without proper escaping.
        """
        if img_attrs is None:
            img_attrs = {}
        if picture_attrs is None:
            picture_attrs = {}

        img_attrs = {} if img_attrs is None else img_attrs.copy()
        img_attrs.setdefault("width", "32")
        img_attrs.setdefault("alt", escape(self.name))

        if self.icon_light is None and self.icon_dark is None:
            return SafeString("")

        icon_light_url = None
        icon_dark_url = None
        if self.icon_light:
            icon_light_url = self.icon_light.static_url
        if self.icon_dark:
            icon_dark_url = self.icon_dark.static_url

        return render_to_string(
            "django_otp_webauthn/contrib/identify/passkey_icon_picture.html",
            {
                "name": escape(self.name),
                "icon_light_url": icon_light_url,
                "icon_dark_url": icon_dark_url,
                "picture_attrs": flatatt(picture_attrs),
                "img_attrs": flatatt(img_attrs),
            },
        )
