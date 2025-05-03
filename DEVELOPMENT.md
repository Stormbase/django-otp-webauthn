# Developing the project

A sandbox project is included in this repository to aid in development.

## Requirements

- ...everything in the [compatibility section](./README.md#compatibility) on the main README.
- [Hatch](https://hatch.pypa.io/)
- [Node.js](https://nodejs.org/) v20
- [Yarn v1](https://classic.yarnpkg.com/en/docs)
- [Pre-commit](https://pre-commit.com/)
- [Caddy](https://caddyserver.com/) (optional, but recommended for https testing)
- [GNU Make](https://www.gnu.org/software/make/) (to build documentation on Linux and MacOS)
- [GNU gettext](https://www.gnu.org/software/gettext/) (for translations)

## Installation (sandbox)

Clone the repository

    git clone git@github.com:Stormbase/django-otp-webauthn.git

Install the Node.js dependencies

    yarn install

Build the frontend

    yarn start

Let Hatch install the Python dependencies and create a virtual environment for you

    hatch shell

Migrate the database

    python manage.py migrate

Create a superuser

    python manage.py createsuperuser

Start the development server

    python manage.py runserver

If using Caddy, you can run it with the included `Caddyfile`. This will set up a reverse proxy with https for the development server.

    caddy run
    # You can now access the sandbox at https://localhost/

If this is the first time you are running Caddy, you need to install the Caddy certificate authority (CA) certificate. This is needed to trust the self-signed certificates that Caddy generates for https.

    caddy trust

From here, you can login using the superuser you created. You can register a passkey by clicking the "_Register a passkey_" button. The "_verify now_" link will take you to the verification page where you can use your passkey to authenticate.

Additionally – once you've registered a passkey – your browser should prompt you to use your passkey when logging in. Completely passwordless!

### About the sandbox

The sandbox is used to test the functionality of the package. It is a Django project that uses the package as a dependency. The package is installed in the sandbox as a local package. This allows you to make changes to the package and see the effects in the sandbox.

In addition, the same sandbox is also used by the E2E browser automation tests (see `tests/e2e` folder) to automate the testing of JavaScript functionality and make sure all the pieces work together.

## Testing

_All commands must be run from the virtual environment created by Hatch. Use `hatch shell` to activate._

To run the tests, you can use the following command:

    pytest

If you are interested in test coverage, run the following commands:

    coverage run -m pytest
    coverage report

    # or, to generate a visual HTML report in the `htmlcov` directory
    coverage html

## Linting and formatting

This project uses [pre-commit](https://pre-commit.com/) to enforce code linting and formatting. This will automatically run certain checks _before_ you are able to create a git commit.

To install the pre-commit hooks, run the following command:

    pre-commit install

The pre-commit hooks will now run automatically when you try to commit changes. If you want to run the checks manually, you can use the following command:

    pre-commit run --all-files

## Documentation

This project's documentation uses the [Sphinx](https://www.sphinx-doc.org) [Furo](https://pradyunsg.me/furo/) theme.

To build the documentation, follow these steps:

1. Clone the repository:

   ```
   git clone git@github.com:Stormbase/django-otp-webauthn.git
   ```

2. Navigate to the docs folder:

   ```
   cd docs
   ```

3. Build the documentation:

   ```
   make html
   ```

4. Serve it, and watch for changes:

   ```
   make run
   ```

## Translations

This project uses the [standard Django translation system](https://docs.djangoproject.com/en/5.1/topics/i18n/translation/) based on GNU gettext.

We have a two script files in place that wrap the standard Django commands to make it easier to create and update the translations. See the next sections for more information.

### Updating translations

Translations are stored in `.po` files. These files are used to store the translation strings for each language. The `.po` files are located in the `src/django_otp_webauthn/locale/<locale_code>/LC_MESSAGES/` directory.

To update all translations files based on the current source code, run the following command:

```bash
./scripts/update_translations.sh --all
```

Or, to update only the translations for your locale, run the following command:

```bash
./scripts/update_translations.sh -l <locale_code>
```

Replace `<locale_code>` with the locale code you used to create the translation messages file. This is quicker than updating all translations.

### Creating new translations

To create a new translation messages file for a specific language, run the following command:

```bash
./scripts/update_translations.sh -l <locale_code>
```

Replace `<locale_code>` with a locale code like `de` for German or `fr` for French.
This will create a `django.po` and `djangojs.po` message files located in `src/django_otp_webauthn/locale/<locale_code>/LC_MESSAGES/django.po`. Please translate the messages in these files. There is also a separate `django.po` file for the sandbox located in `sandbox/locale/<locale_code>/LC_MESSAGES/django.po`, which is used for the sandbox project. You don't have to translate this file, feel free to leave it untranslated.

To make your translations visible, you need to compile the `.po` files into `.mo` files. See the next section for how to do this.

### Compiling translations

In order to make the translations usable, they need to be compiled into `.mo` files. This project has a wrapper script around `compilemessages` that will compile all `.po` files in the project.

To compile all translations, run the following command:

```bash
./scripts/compile_translations.sh
```

Or, to compile only the translations for your locale, run the following command:

```bash
./scripts/compile_translations.sh -l <locale_code>
```

Replace `<locale_code>` with the locale code you used to create the translation messages file. This is quicker than compiling all translations.

**Note:** when perfecting your translations, you may find that the translation is not updated even after you recompile the `.po` files. This is because the `.mo` files are cached by Django. Try restarting the development server to see your changes.

**Note:** compiled .mo files are not checked into git. This is intentional, as they are generated files.

## Releasing

Releasing a new version is semi-automated. The following steps should be taken:

1. Make sure `all-contributors` is up to date. Run `npx all-contributors-cli check` to compare the contributors in `all-contributorsrc` with the contributors in the git history.
   1. If there are new contributors, figure out what areas they contributed in and a run `npx all-contributors-cli add <username> [code,bug]`. [Refer to emoji key in the All Contributors specification for the appropriate emoji.](https://allcontributors.org/docs/en/emoji-key)
   2. `npx all-contributors-cli generate` to update the `CONTRIBUTORS.md` file.
2. Ensure that the version in `pyproject.toml` is correct. If not update using, `hatch version major|minor|patch`.
3. Ensure `CHANGELOG.md` is up to date. Fill in the new version number and date.
4. Commit the changes.
5. (optional) create a git tag for the new version: `git tag -a v0.0.0 -m "v0.0.0"`. Replace `0.0.0` with the appropriate version number.
6. Create a new release on GitHub. Use the tag you created in the previous step. Or allow GitHub to create the tag for you if you didn't create one.
7. Creating the release will trigger a GitHub action that will publish the new version to PyPI. View the action to ensure it completes successfully.
