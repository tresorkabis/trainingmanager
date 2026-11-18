from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("progress", "0003_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SchedulePreset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("schedules", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuration de créneaux",
                "verbose_name_plural": "Configurations de créneaux",
                "ordering": ["name"],
            },
        ),
    ]
