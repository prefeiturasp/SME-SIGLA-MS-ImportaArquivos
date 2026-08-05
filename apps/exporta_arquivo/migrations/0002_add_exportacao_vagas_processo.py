# Generated manually for ExportacaoVagasProcesso

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exporta_arquivo', '0001_add_exportacao_vagas_sigpec'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportacaoVagasProcesso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
                ('processo_uuid', models.UUIDField(verbose_name='UUID do processo de convocação')),
                ('cargo_uuid', models.UUIDField(verbose_name='UUID do cargo')),
                ('concurso_uuid', models.UUIDField(blank=True, null=True, verbose_name='UUID do concurso')),
                ('concurso_nome', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do concurso')),
            ],
            options={
                'verbose_name': 'Exportação de vagas processo',
                'verbose_name_plural': 'Exportações de vagas processo',
                'db_table': 'exportacao_vagas_processo',
                'ordering': ['-criado_em'],
            },
        ),
    ]
