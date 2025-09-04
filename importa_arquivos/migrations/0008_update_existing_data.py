# Generated manually to update existing data

from django.db import migrations


def update_candidatos_to_habilitados(apps, schema_editor):
    """Update existing CANDIDATOS_CLASSIFICADOS records to HABILITADOS."""
    ImportacaoArquivos = apps.get_model('importa_arquivos', 'ImportacaoArquivos')
    ImportacaoArquivos.objects.filter(tipo_de_layout='CANDIDATOS_CLASSIFICADOS').update(tipo_de_layout='HABILITADOS')


def reverse_update_habilitados_to_candidatos(apps, schema_editor):
    """Reverse the update for rollback."""
    ImportacaoArquivos = apps.get_model('importa_arquivos', 'ImportacaoArquivos')
    ImportacaoArquivos.objects.filter(tipo_de_layout='HABILITADOS').update(tipo_de_layout='CANDIDATOS_CLASSIFICADOS')


class Migration(migrations.Migration):
    dependencies = [
        ('importa_arquivos', '0007_update_layout_choices'),
    ]

    operations = [
        migrations.RunPython(
            update_candidatos_to_habilitados,
            reverse_update_habilitados_to_candidatos
        ),
    ]
