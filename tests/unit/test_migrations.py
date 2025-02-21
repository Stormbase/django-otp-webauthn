from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_has_all_migrations():
    output = StringIO()

    try:
        call_command(
            "makemigrations",
            "--check",
            "--dry-run",
            verbosity=1,
            interactive=False,
            stdout=output,
            stderr=StringIO(),
        )
    except SystemExit:  # pragma: no cover
        raise AssertionError("Pending migrations:\n" + output.getvalue()) from None
