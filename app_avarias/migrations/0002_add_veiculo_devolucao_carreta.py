from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('app_avarias', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='avaria',
            name='veiculo_devolucao_carreta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='avarias_devolucao_carreta', to='app_avarias.veiculo', verbose_name='Carreta Devolução'),
        ),
    ]
