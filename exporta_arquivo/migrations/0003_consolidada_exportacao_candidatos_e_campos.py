# Migration consolidada: ExportacaoCandidatosProcesso (state) + colunas faltantes em todos os modelos.
# A tabela exportacao_candidatos_processo já pode existir (criada pela antiga 0003); não recriamos.
# Colunas são adicionadas com IF NOT EXISTS para não falhar se 0004/0005 já foram aplicadas.

import uuid
from django.db import migrations, models


def add_missing_columns(apps, schema_editor):
    """Cria a tabela exportacao_candidatos_processo se não existir; adiciona colunas faltantes (IF NOT EXISTS)."""
    from django.db import connection

    vendor = connection.vendor
    with connection.cursor() as cursor:
        if vendor == "sqlite":
            cursor.execute("""
                SELECT 1 FROM sqlite_master
                WHERE type='table' AND name='exportacao_candidatos_processo'
            """)
            table_exists = cursor.fetchone() is not None
            if not table_exists:
                cursor.execute("""
                    CREATE TABLE exportacao_candidatos_processo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uuid CHAR(32) NOT NULL UNIQUE,
                        criado_em DATETIME NOT NULL,
                        atualizado_em DATETIME NOT NULL,
                        processo_uuid CHAR(32) NOT NULL,
                        cargo_uuid CHAR(32) NOT NULL,
                        concurso_uuid CHAR(32) NULL,
                        concurso_nome VARCHAR(255) NULL,
                        concurso_codigo INTEGER NULL,
                        concurso_data_criacao VARCHAR(50) NULL,
                        processo_nome VARCHAR(500) NULL,
                        cargo_nome VARCHAR(255) NULL,
                        cargo_codigo INTEGER NULL,
                        conteudo_arquivo TEXT NULL,
                        nome_arquivo VARCHAR(255) NULL
                    )
                """)
            else:
                _sqlite_add_columns(cursor, "exportacao_candidatos_processo", [
                    "concurso_codigo INTEGER NULL",
                    "concurso_data_criacao VARCHAR(50) NULL",
                    "processo_nome VARCHAR(500) NULL",
                    "cargo_nome VARCHAR(255) NULL",
                    "cargo_codigo INTEGER NULL",
                    "conteudo_arquivo TEXT NULL",
                    "nome_arquivo VARCHAR(255) NULL",
                ])
            for table in ("exportacao_vagas_sigpec", "exportacao_vagas_processo"):
                _sqlite_add_columns(cursor, table, [
                    "processo_nome VARCHAR(500) NULL",
                    "cargo_nome VARCHAR(255) NULL",
                    "cargo_codigo INTEGER NULL",
                    "conteudo_arquivo TEXT NULL",
                    "nome_arquivo VARCHAR(255) NULL",
                ])
            return
        # PostgreSQL
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'exportacao_candidatos_processo'
        """)
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            cursor.execute("""
                CREATE TABLE exportacao_candidatos_processo (
                    id BIGSERIAL PRIMARY KEY,
                    uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
                    criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    processo_uuid UUID NOT NULL,
                    cargo_uuid UUID NOT NULL,
                    concurso_uuid UUID NULL,
                    concurso_nome VARCHAR(255) NULL,
                    concurso_codigo INTEGER NULL,
                    concurso_data_criacao VARCHAR(50) NULL,
                    processo_nome VARCHAR(500) NULL,
                    cargo_nome VARCHAR(255) NULL,
                    cargo_codigo INTEGER NULL,
                    conteudo_arquivo TEXT NULL,
                    nome_arquivo VARCHAR(255) NULL
                )
            """)
        else:
            for col, sql in [
                ('concurso_codigo', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS concurso_codigo INTEGER NULL'),
                ('concurso_data_criacao', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS concurso_data_criacao VARCHAR(50) NULL'),
                ('processo_nome', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS processo_nome VARCHAR(500) NULL'),
                ('cargo_nome', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS cargo_nome VARCHAR(255) NULL'),
                ('cargo_codigo', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS cargo_codigo INTEGER NULL'),
                ('conteudo_arquivo', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS conteudo_arquivo TEXT NULL'),
                ('nome_arquivo', 'ALTER TABLE exportacao_candidatos_processo ADD COLUMN IF NOT EXISTS nome_arquivo VARCHAR(255) NULL'),
            ]:
                cursor.execute(sql)
        for col, sql in [
            ('processo_nome', 'ALTER TABLE exportacao_vagas_sigpec ADD COLUMN IF NOT EXISTS processo_nome VARCHAR(500) NULL'),
            ('cargo_nome', 'ALTER TABLE exportacao_vagas_sigpec ADD COLUMN IF NOT EXISTS cargo_nome VARCHAR(255) NULL'),
            ('cargo_codigo', 'ALTER TABLE exportacao_vagas_sigpec ADD COLUMN IF NOT EXISTS cargo_codigo INTEGER NULL'),
            ('conteudo_arquivo', 'ALTER TABLE exportacao_vagas_sigpec ADD COLUMN IF NOT EXISTS conteudo_arquivo TEXT NULL'),
            ('nome_arquivo', 'ALTER TABLE exportacao_vagas_sigpec ADD COLUMN IF NOT EXISTS nome_arquivo VARCHAR(255) NULL'),
        ]:
            cursor.execute(sql)
        for col, sql in [
            ('processo_nome', 'ALTER TABLE exportacao_vagas_processo ADD COLUMN IF NOT EXISTS processo_nome VARCHAR(500) NULL'),
            ('cargo_nome', 'ALTER TABLE exportacao_vagas_processo ADD COLUMN IF NOT EXISTS cargo_nome VARCHAR(255) NULL'),
            ('cargo_codigo', 'ALTER TABLE exportacao_vagas_processo ADD COLUMN IF NOT EXISTS cargo_codigo INTEGER NULL'),
            ('conteudo_arquivo', 'ALTER TABLE exportacao_vagas_processo ADD COLUMN IF NOT EXISTS conteudo_arquivo TEXT NULL'),
            ('nome_arquivo', 'ALTER TABLE exportacao_vagas_processo ADD COLUMN IF NOT EXISTS nome_arquivo VARCHAR(255) NULL'),
        ]:
            cursor.execute(sql)


def _sqlite_add_columns(cursor, table_name, column_defs):
    """Adiciona colunas em SQLite se não existirem. column_defs: lista de 'nome_tipo NULL'."""
    cursor.execute("PRAGMA table_info(%s)" % table_name)
    existing = {row[1] for row in cursor.fetchall()}
    for col_def in column_defs:
        col_name = col_def.split()[0]
        if col_name in existing:
            continue
        try:
            cursor.execute("ALTER TABLE %s ADD COLUMN %s" % (table_name, col_def))
        except Exception:
            pass


def noop_reverse(apps, schema_editor):
    """Não removemos colunas no rollback para evitar perda de dados."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('exporta_arquivo', '0002_add_exportacao_vagas_processo'),
    ]

    operations = [
        # 1. Estado: criar modelo ExportacaoCandidatosProcesso. BD: não criar tabela; só adicionar colunas faltantes.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='ExportacaoCandidatosProcesso',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                        ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                        ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
                        ('processo_uuid', models.UUIDField(verbose_name='UUID do processo de convocação')),
                        ('cargo_uuid', models.UUIDField(verbose_name='UUID do cargo')),
                        ('concurso_uuid', models.UUIDField(blank=True, null=True, verbose_name='UUID do concurso')),
                        ('concurso_nome', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do concurso')),
                        ('concurso_codigo', models.IntegerField(blank=True, null=True, verbose_name='Código do concurso')),
                        ('concurso_data_criacao', models.CharField(blank=True, max_length=50, null=True, verbose_name='Data de criação do concurso')),
                        ('processo_nome', models.CharField(blank=True, max_length=500, null=True, verbose_name='Nome do processo')),
                        ('cargo_nome', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do cargo')),
                        ('cargo_codigo', models.IntegerField(blank=True, null=True, verbose_name='Código do cargo (integração)')),
                        ('conteudo_arquivo', models.TextField(blank=True, null=True, verbose_name='Conteúdo do arquivo exportado')),
                        ('nome_arquivo', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do arquivo na exportação')),
                    ],
                    options={
                        'verbose_name': 'Exportação de candidatos processo',
                        'verbose_name_plural': 'Exportações de candidatos processo',
                        'db_table': 'exportacao_candidatos_processo',
                        'ordering': ['-criado_em'],
                    },
                ),
            ],
            database_operations=[
                migrations.RunPython(add_missing_columns, noop_reverse),
            ],
        ),
    ]
