# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Django OTP WebAuthn'
copyright = '2024'
author = ''

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Customize Alabaster theme -----------------------------------------------
# https://alabaster.readthedocs.io/en/latest/index.html

html_theme_options = {
    'logo': '',
    'github_button': 'true',
    'github_type': 'No text variant',
    'github_user': 'activus-d',
    'github_repo': 'django-otp-webauthn-doc',
    'page_width': '97%'
}
