from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('training', '0002_rename_metier_to_formation'),
    ]

    operations = [
        migrations.AddField(
            model_name='formation',
            name='type_formation',
            field=models.CharField(choices=[('qualifiante', 'Qualifiante'), ('continue', 'Continue')], default='qualifiante', max_length=20, verbose_name='Type de formation'),
        ),
    ]
