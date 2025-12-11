#!/bin/sh

# -----------------------------------------------------------------------------
# Translation update helper for django_otp_webauthn
#
# This script updates translation catalogs for both Python/Template code
# (django.po) and JavaScript code (djangojs.po).
#
# Usage:
#
#   Update all languages:
#       ./update_translations.sh --all
#
#   Create or update a specific language:
#       ./update_translations.sh -l <language_code>
#
# JavaScript translations
# -----------------------
# JavaScript messages are extracted from the compiled Webpack output.
# Therefore, static assets must be built before updating djangojs.po.
#
#   Local Node/Yarn environment:
#       cd client && yarn install && yarn build
#
#   Without Node/Yarn installed on the host:
#       docker build -f client/Dockerfile.client -t otp-webauthn-client .
#       docker run --rm -v "$PWD:/app" otp-webauthn-client
#
# After compiling the static assets, run this script again normally.
#
# Python/Django translations
# --------------------------
# The django.po catalogs are extracted from Python sources and templates.
# -----------------------------------------------------------------------------

# If no arguments are provided, show usage
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 [--all | -l <language_code>]"
    exit 1
fi

set -e

IGNORE_PATHS="--ignore venv --ignore client --ignore .tox --ignore dist --ignore node_modules --ignore docs"

echo "Updating djangojs.po files..."
python manage.py makemessages $IGNORE_PATHS -d djangojs --no-location --no-obsolete $@

echo "\nUpdating django.po files..."
python manage.py makemessages $IGNORE_PATHS --no-obsolete $@
