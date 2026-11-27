from django.db import migrations, models


DEFAULT_NAME = "École Supérieure de Formation des Cadres"


def create_institution_settings(apps, schema_editor):
    InstitutionSettings = apps.get_model("users", "InstitutionSettings")
    InstitutionSettings.objects.get_or_create(
        pk=1,
        defaults={"institution_name": DEFAULT_NAME},
    )


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="InstitutionSettings",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("institution_name", models.CharField(default=DEFAULT_NAME, max_length=200, verbose_name="Nom officiel de l'institut")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Réglage de l'institut",
                "verbose_name_plural": "Réglages de l'institut",
            },
        ),
        migrations.RunPython(create_institution_settings, migrations.RunPython.noop),
    ]
