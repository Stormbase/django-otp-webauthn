#!/bin/sh

# This script is used to update and manage translations.
# Usage:
#
# Update all languages:
# ./update_translations.sh --all
#
# Create or update existing language:
# ./update_translations.sh -l <language_code>

# If no arguments are provided, show usage
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 [--all | -l <language_code>]"
    exit 1
fi

set -e

IGNORE_PATHS="--ignore venv --ignore client --ignore .tox --ignore dist --ignore node_modules --ignore docs"

echo "Updating djangojs.po files..."
# Update JavaScript translations
# Note: static must be compiled before running this command: `cd client && yarn build`
# Note: source locations are omitted because they refer to the compiled files, not the source files
python manage.py makemessages $IGNORE_PATHS -d djangojs --no-location --no-obsolete $@

echo "\nUpdating django.po files..."
# Update Django translations
python manage.py makemessages $IGNORE_PATHS --no-obsolete $@
