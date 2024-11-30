Developing the Project
======================

A sandbox project is included in this repository to aid in development.

Requirements
------------

- Everything in the `compatibility section <README.rst#compatibility>`_ on the main README
- `Hatch <https://hatch.pypa.io/>`_
- `Node.js <https://nodejs.org/>`_ v20
- `Yarn <https://yarnpkg.com/>`_
- `Pre-commit <https://pre-commit.com/>`_
- `Caddy <https://caddyserver.com/>`_ (optional, but recommended for https testing)

Installation (Sandbox)
----------------------

Clone the repository::

    git clone git@github.com:Stormbase/django-otp-webauthn.git

Install the Node.js dependencies::

    yarn install

Build the frontend::

    yarn start

Let Hatch install the Python dependencies and create a virtual environment for you::

    hatch shell

Migrate the database::

    python manage.py migrate

Create a superuser::

    python manage.py createsuperuser

Start the development server::

    python manage.py runserver

If using Caddy, you can run it with the included ``Caddyfile``. This will set up a reverse proxy with https for the development server::

    caddy run
    # You can now access the sandbox at https://localhost/

If this is the first time you are running Caddy, you need to install the Caddy certificate authority (CA) certificate. This is needed to trust the self-signed certificates that Caddy generates for https::

    caddy trust

From here, you can login using the superuser you created. You can register a passkey by clicking the "*Register a passkey*" button. The "*verify now*" link will take you to the verification page where you can use your passkey to authenticate.

Additionally – once you've registered a passkey – your browser should prompt you to use your passkey when logging in. Completely passwordless!

Testing
-------

.. note::
   All commands must be run from the virtual environment created by Hatch. Use ``hatch shell`` to activate.

To run the tests, you can use the following command::

    pytest

If you are interested in test coverage, run the following commands::

    coverage run -m pytest
    coverage report

    # or, to generate a visual HTML report in the `htmlcov` directory
    coverage html

Linting and Formatting
----------------------

This project uses `pre-commit <https://pre-commit.com/>`_ to enforce code linting and formatting. This will automatically run certain checks *before* you are able to create a git commit.

To install the pre-commit hooks::

    pre-commit install

The pre-commit hooks will now run automatically when you try to commit changes. To run the checks manually::

    pre-commit run --all-files

Documentation
-------------

This project's documentation uses the `Sphinx <https://www.sphinx-doc.org>`_ `Alabaster <https://alabaster.readthedocs.io/>`_ theme.

To build the documentation:

1. Clone the repository::

    git clone git@github.com:Stormbase/django-otp-webauthn.git

2. Navigate to the docs folder::

    cd docs

3. Build the documentation::

    make html

4. Serve it, and watch for changes::

    make run

Releasing
---------

Releasing a new version is semi-automated. The following steps should be taken:

1. Ensure ``all-contributors`` is up to date:

   - Run ``npx all-contributors-cli check`` to compare contributors
   - If new contributors exist:

     a. Determine their contribution areas
     b. Run ``npx all-contributors-cli add <username> [code,bug]``
     c. Run ``npx all-contributors-cli generate`` to update ``CONTRIBUTORS.md``

2. Verify version in ``pyproject.toml``::

    hatch version major|minor|patch

3. Update ``CHANGELOG.md`` with new version number and date

4. Commit the changes

5. (Optional) Create a git tag::

    git tag -a v0.0.0 -m "v0.0.0"

6. Create a new release on GitHub

   - Use the tag created in the previous step
   - Allow GitHub to create the tag if not already created

7. Verify the GitHub action publishes to PyPI
