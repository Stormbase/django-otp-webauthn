from importlib import import_module

from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode


class SettingDomain(Domain):
    name = "django_otp_webauthn"
    label = "django-otp-webauthn"

    object_types = {
        "setting": ObjType("setting", "setting"),
    }

    roles = {
        "setting": XRefRole(),
    }

    initial_data = {
        "objects": {},
    }

    def resolve_xref(
        self,
        env,
        fromdocname,
        builder,
        typ,
        target,
        node,
        contnode,
    ):
        if target not in self.data["objects"]:
            return None

        docname, anchor = self.data["objects"][target]

        return make_refnode(
            builder,
            fromdocname,
            docname,
            anchor,
            contnode,
            target,
        )

    def get_objects(self):
        for name, (docname, anchor) in self.data["objects"].items():
            yield (
                name,
                name,
                "settings",
                docname,
                anchor,
                1,
            )


def register_settings(app, doctree):
    domain = app.env.get_domain("django_otp_webauthn")
    py_domain = app.env.get_domain("py")

    module = import_module("django_otp_webauthn.settings")

    settings_class = module.AppSettings

    for name in dir(settings_class):
        if not name.isupper():
            continue

        fullname = "django_otp_webauthn.settings.AppSettings." + name

        entry = py_domain.objects.get(fullname)

        if entry is None:
            continue

        domain.data["objects"][name] = (
            entry.docname,
            entry.node_id,
        )


def setup(app):
    app.add_domain(SettingDomain)
    app.connect(
        "doctree-read",
        register_settings,
    )

    return {
        "version": "1.0",
        "parallel_read_safe": True,
    }
