# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Django OTP WebAuthn"
copyright = "2024"
author = "Stormbase and individual contributors"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_design",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "venv"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

# -- Customize Furo theme -----------------------------------------------
# https://pradyunsg.me/furo/

html_theme_options = {
    "source_repository": "https://github.com/Stormbase/django-otp-webauthn",
    "source_branch": "main",
    "source_directory": "docs/",
    "announcement": "<div><strong>📢Announcement:</strong> Django OTP WebAuthn is currently in development. Please report any issues or suggestions on the <a href='https://github.com/Stormbase/django-otp-webauthn/issues'>GitHub Issues</a>.</div>",
}
