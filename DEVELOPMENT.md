# Developing the project

A sandbox project is included in this repository to aid in development.

## Requirements

- ...everything in the [compatibility section](./README.md#compatibility) on the main README.
- [Hatch](https://hatch.pypa.io/)
- [Node.js](https://nodejs.org/) v20
- [Yarn](https://yarnpkg.com/)
- [Pre-commit](https://pre-commit.com/)
- [Caddy](https://caddyserver.com/) (optional, but recommended for https testing)

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

This project's documentation uses the [Sphinx](https://www.sphinx-doc.org) [Alabaster](https://alabaster.readthedocs.io/) theme.

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
