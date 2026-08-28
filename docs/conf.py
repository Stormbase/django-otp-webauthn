import os
import sys

sys.path.insert(0, os.path.abspath("_ext"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Django OTP WebAuthn"
copyright = (
    "2024-present Stormbase and contributors. Licensed under the BSD-3-Clause License."
)
author = "Stormbase and individual contributors"

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
    "sphinxcontrib_django",
    "sphinx_design",
    "sphinx_copybutton",
    "myst_parser",
    "django_otp_webauthn_settings",
]

if on_rtd or os.environ.get("BUILD_LLMS_TXT", ""):
    extensions.append("sphinx_llm.txt")

ogp_social_cards = {
    "enable": os.environ.get("ENABLE_SOCIAL_CARDS", "1" if on_rtd else "0") == "1",
}
ogp_site_url = os.environ.get(
    "OGP_SITE_URL", "https://django-otp-webauthn.readthedocs.io/en/stable/"
)

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "venv"]


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

# Autodoc may need to import some models modules which require django settings
# be configured
django_settings = "sandbox.settings"

# sphinxcontrib_django requires legacy class-based autodoc to work properly with Django models
autodoc_use_legacy_class_based = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

# -- Customize Furo theme -----------------------------------------------
# https://pradyunsg.me/furo/

html_theme_options = {
    "source_repository": "https://github.com/Stormbase/django-otp-webauthn",
    "source_branch": "main",
    "source_directory": "docs/",
    "announcement": "<div><strong>📢Announcement:</strong> Django OTP WebAuthn is still pretty new. Report any issues or suggestions on <a href='https://github.com/Stormbase/django-otp-webauthn/issues/new?template=feedback.yml' target='_blank' rel='noopener noreferrer'>GitHub Issues</a>.</div>",
}

# sphinx.ext.intersphinx settings
intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        None,
    ),
    "python": (
        "https://docs.python.org/3/",
        None,
    ),
}
