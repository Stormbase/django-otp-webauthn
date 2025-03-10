.. _contributing:

Contributing
============

This package is open source and is licensed under the BSD-3 Clause `License <https://github.com/Stormbase/django-otp-webauthn/blob/main/LICENSE>`_. We welcome all contributions, including code improvements, bug fixes, and documentation updates.

Propose changes
---------------

The following steps provide an overview of the process involved in proposing changes to Django OTP WebAuthn:

1. Create an issue in the repository to outline the proposed changes.

2. Fork the `repository <https://github.com/Stormbase/django-otp-webauthn>`_ and create a new branch for the changes.

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

11. If you're using Caddy, run it with the included ```Caddyfile`` to enable HTTPS:

    .. code-block:: console

        caddy run

12. If it's your first time using Caddy, trust the self-signed certificate:

    .. code-block:: console

        caddy trust

Build documentation
-------------------

The Django OTP WebAuthn documentation is built with `Sphinx <https://www.sphinx-doc.org/en/master/>`_ and `Furo <https://pradyunsg.me/furo/>`_.

To build the documentation on your local machine, follow these steps:

1. Complete steps 1 through 6 in :ref:`set-up-django-otp-webauthn` if you haven't done so already.

2. Navigate to the `docs` folder:

    .. code-block:: console

        cd docs

3. Build the documentation:

    .. code-block:: console

        make html

4. Serve and watch for changes:

    .. code-block:: console

        make run


.. toctree::
    :maxdepth: 2
    :hidden:

    Style guide <style_guide.rst>
