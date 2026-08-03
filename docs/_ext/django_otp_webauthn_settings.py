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
        # Map the friendly setting name to the Python attribute
        fullname = "django_otp_webauthn.settings.AppSettings." + target

        py_domain = env.get_domain("py")

        entry = py_domain.objects.get(fullname)

        if entry is None:
            return None

        return make_refnode(
            builder,
            fromdocname,
            entry.docname,
            entry.node_id,
            contnode,
            target,
        )


def setup(app):
    app.add_domain(SettingDomain)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
    }
