# Developing the project

A sandbox project is included in this repository to aid in development.

## Requirements

- ...everything in the [compatibility section](./README.md#compatibility) on the main README.
- [Hatch](https://hatch.pypa.io/)
- [Node.js](https://nodejs.org/) v20
- [Yarn](https://yarnpkg.com/)
- [Caddy](https://caddyserver.com/) (optional, but recommended for https testing)

## Installation (sandbox)

Clone the repository

    git clone git@github.com:Stormbase/django-otp-webauthn.git

Install the Node.js dependencies

    # in the client directory
    yarn install

Build the frontend

    # in the client directory
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
