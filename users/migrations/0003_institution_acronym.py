from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0002_institution_settings")]

    operations = [
        migrations.AddField(
            model_name="institutionsettings",
            name="institution_acronym",
            field=models.CharField(
                default="ESFORCA",
                max_length=50,
                verbose_name="Sigle de l’institut",
            ),
        ),
    ]
