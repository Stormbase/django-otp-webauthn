# Generated by Django 5.0.6 on 2024-05-19 15:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_otp_webauthn", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="webauthncredential",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                help_text="The date and time when this device was initially created in the system.",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="webauthncredential",
            name="last_used_at",
            field=models.DateTimeField(
                blank=True,
                help_text="The most recent date and time this device was used.",
                null=True,
            ),
        ),
    ]
