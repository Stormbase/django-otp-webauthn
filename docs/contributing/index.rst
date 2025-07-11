.. _contributing:

Contributing
============

This package is open source and is licensed under the BSD-3 Clause `License <https://github.com/Stormbase/django-otp-webauthn/blob/main/LICENSE>`_. We welcome all contributions, including translations, bug reports, tutorials, code improvements, and documentation updates.

Propose changes
---------------

The following steps provide an overview of the process involved in proposing changes to Django OTP WebAuthn:

1. Create an issue in the `repository <https://github.com/Stormbase/django-otp-webauthn>`_ to outline the proposed changes.

2. Fork the repository and create a new branch for the changes.

3. :ref:`set-up-django-otp-webauthn`.

4. Implement the changes and ensure they pass all tests and pre-commit checks.

5. Submit a pull request using your newly created branch.

6. Ensure your pull request has a clear and detailed description of the changes and include a link to the previously opened issue.

7. Update documentation if your changes affect it.

.. _set-up-django-otp-webauthn:

Set up Django OTP WebAuthn
--------------------------

To set up the Django OTP WebAuthn on your local machine, follow these steps:

1. Install the following dependencies:
    * All requirements listed in the :ref:`compatibility <compatibility>` section
    * `Hatch <https://hatch.pypa.io/>`_
    * `Node.js <https://nodejs.org/>`_ v20
    * `Yarn <https://yarnpkg.com/>`_
    * `pre-commit <https://pre-commit.com/>`_
    * `Caddy <https://caddyserver.com/>`_ (optional, recommended for HTTPS testing)
    * `GNU Make <https://www.gnu.org/software/make/>`_

2. Fork the `repository <https://github.com/Stormbase/django-otp-webauthn>`_.

3. Clone your forked repository:

    .. code-block:: console

        # Using SSH
        git clone git@github.com:<your-github-username>/django-otp-webauthn.git

        # Using HTTPS
        git clone https://github.com/<your-github-username>/django

    .. hint:: Replace <your-github-username> with your actual GitHub username.

4. Navigate to the ``django-otp-webauthn`` directory:

    .. code-block:: console

        cd django-otp-webauthn

5. Install Node.js dependencies:

    .. code-block:: console

        yarn install

6. Install Python dependencies and create a virtual environment:

    .. code-block:: console

        hatch shell

7. Build the frontend:

    .. code-block:: console

        yarn start

8. Migrate the database:

    .. code-block:: console

        python manage.py migrate

9. Create a superuser:

    .. code-block:: console

        python manage.py createsuperuser

10. Start the development server:

    .. code-block:: console

        python manage.py runserver

11. If you're using Caddy, run it with the included ```Caddyfile`` to turn on HTTPS:

    .. code-block:: console

        caddy run

12. If it's your first time using Caddy, trust the self-signed certificate:

    .. code-block:: console

        caddy trust

Test project
------------

You should run all commands from the virtual environment created by running the ``hatch shell`` command.

Run tests with the following command:

.. code-block:: console

    pytest

For test coverage, use these commands:

.. code-block:: console

    coverage run manage.py test
    coverage report

Generate a visual HTML report in the htmlcov directory with the following command:

.. code-block:: console

    coverage html

Lint and format
---------------

This project uses ``pre-commit`` to enforce code linting and formatting. ``pre-commit`` automatically runs checks before allowing a Git commit.

Install the pre-commit hooks with:

.. code-block:: console

    pre-commit install

Now the hooks will run automatically on each commit. To trigger checks manually, run:

.. code-block:: console

    pre-commit run --all-files

Translations
------------

This project uses the `standard Django translation system <https://docs.djangoproject.com/en/5.1/topics/i18n/translation/>`_ system for translations, which based on GNU `gettext <https://www.gnu.org/software/gettext/>`_.

Two script files wrap the standard Django translation commands, making it easier to create and update translations.  For more details, see :ref:`update-translations`

.. _update-translations:

Update translations
~~~~~~~~~~~~~~~~~~~~~

Translations are stored in ``.po`` files. These files contain the translation strings for each language. You can find the ``.po`` files in the ``src/django_otp_webauthn/locale/<locale_code>/LC_MESSAGES/`` directory.

To update the all translations based on the current source code, run the command:

.. code-block:: console

    ./scripts/update_translations.sh --all

Updating a single locale is faster than updating all translations. To update translations for a specific locale only, run the command:

.. code-block:: console

    ./scripts/update_translations.sh -l <locale_code>

.. attention::

    Replace ``<locale_code>`` with the appropriate locale code you used when creating the translation file.

Create new translations
~~~~~~~~~~~~~~~~~~~~~~~~~

To create a new translation file for a specific language, run:

.. code-block:: console

    ./scripts/update_translations.sh -l <locale_code>

.. attention::

    Replace ``<locale_code>`` with the appropriate locale code like ``de`` for German or ``fr`` for French.

Running the preceding command will create a ``django.po`` and ``djangojs.po`` files. You will find the created files in the ``src/django_otp_webauthn/locale/<locale_code>/LC_MESSAGES/django.po`` directory. Ensure you translate the messages in these files.

There is also a separate ``django.po`` file for the sandbox, which is located in the ``sandbox/locale/<locale_code>/LC_MESSAGES/django.po`` directory.  The ``django.po`` file is used for the sandbox project, but translating it is optional.

To make your translations visible, you have to compile the ``.po`` files into ``.mo`` files. To learn how to compile the ``.po`` files, see :ref:`compile-translations`.

.. _compile-translations:

Compile translations
~~~~~~~~~~~~~~~~~~~~

This project includes a wrapper script for ``compilemessages`` that compiles all ``.po`` files in the project. To compile all translations, run:

.. code-block:: console

    ./scripts/compile_translations.sh

If you want to compile translations for a specific locale only, run the following command:

.. code-block:: console

    ./scripts/compile_translations.sh -l <locale_code>

.. note::

    Sometimes, translation updates don’t appear after recompiling the ``.po`` files because Django caches the .mo files. Try restarting the development server to apply your changes.

    Also, Compiled ``.mo`` files are intentionally not checked into Git, as they are generated files.

Build documentation
-------------------

The Django OTP WebAuthn documentation is built with `Sphinx <https://www.sphinx-doc.org/en/master/>`_ and `Furo <https://pradyunsg.me/furo/>`_.

To build the documentation on your local machine, follow these steps:

1. Complete steps 1 through 6 in :ref:`set-up-django-otp-webauthn` if you haven't done so already.

2. Navigate to the `docs` folder:

    .. code-block:: console

        cd docs

3. Build and serve the documentation, then watch for changes :

    .. code-block:: console

        make run

Other guidelines
----------------

Please, also follow these guidelines when contributing to the documentation:

.. toctree::
    :maxdepth: 1

    Style guide <style_guide.rst>
    reStructuredText usage <restructuredtext_usage.rst>
