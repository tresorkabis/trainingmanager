from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0004_schedulepreset"),
    ]

    operations = [
        migrations.AddField(
            model_name="detailaction",
            name="a_passe_jury",
            field=models.BooleanField(default=False, verbose_name="A passé le jury"),
        ),
    ]
