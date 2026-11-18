from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0005_detailaction_a_passe_jury"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActionEvaluation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_evaluation", models.DateField(verbose_name="Date réelle de séance évaluée")),
                ("constat", models.TextField(verbose_name="Constat")),
                ("recommandation", models.TextField(verbose_name="Recommandation")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evaluations_pedagogiques", to="progress.action")),
                ("evaluateur", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="evaluations_actions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Évaluation pédagogique d’action",
                "verbose_name_plural": "Évaluations pédagogiques d’actions",
                "constraints": [models.UniqueConstraint(fields=("action", "date_evaluation"), name="action_evaluation_unique_date")],
            },
        ),
    ]
