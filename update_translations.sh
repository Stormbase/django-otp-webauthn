#!/bin/sh

# This script is used to update and manage translations.
# Usage:
#
# Update all languages:
# ./update_translations.sh --all
#
# Create or update existing language:
# ./update_translations.sh -l <language_code>

set -e

echo "Updating djangojs.po files..."
# Update JavaScript translations
# Note: static must be compiled before running this command: `cd client && yarn build`
# Note: source locations are omitted because they refer to the compiled files, not the source files
python manage.py makemessages --ignore venv --ignore client -d djangojs --no-location --no-obsolete $@

echo "\nUpdating django.po files..."
# Update Django translations
python manage.py makemessages --ignore venv --ignore client -d django --no-obsolete $@
