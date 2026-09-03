from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0008_transportecorrida'),
    ]

    operations = [
        # 1. Tabela Dicionário De-Para
        migrations.CreateModel(
            name='TransporteProgramaAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_original', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='Nome Original / Variação')),
                ('nome_padronizado', models.CharField(db_index=True, max_length=255, verbose_name='Nome Padronizado Canônico')),
                ('centro_custo_codigo', models.CharField(blank=True, max_length=64, verbose_name='Código Centro de Custo')),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'De-Para de Programa / Projeto',
                'verbose_name_plural': 'De-Para de Programas / Projetos',
                'ordering': ['nome_padronizado', 'nome_original'],
            },
        ),

        # 2. View SQL 1: Fechamento Mensal
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW vw_transportes_fechamento_mensal AS
            SELECT
                CONCAT(arquivo_origem, '_', plataforma) AS id,
                arquivo_origem,
                plataforma,
                SUBSTRING(arquivo_origem FROM 1 FOR 4) AS ano,
                SUBSTRING(arquivo_origem FROM 6 FOR 2) AS mes,
                COUNT(id) AS total_viagens,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(SUM(distancia_km), 0) AS total_km,
                CASE 
                    WHEN COUNT(id) > 0 THEN ROUND(COALESCE(SUM(valor_total), 0) / COUNT(id), 2)
                    ELSE 0 
                END AS ticket_medio,
                CASE 
                    WHEN COUNT(id) > 0 THEN ROUND(COALESCE(SUM(distancia_km), 0) / COUNT(id), 2)
                    ELSE 0 
                END AS km_medio
            FROM integrations_transportecorrida
            GROUP BY arquivo_origem, plataforma
            ORDER BY ano DESC, mes DESC, plataforma;
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_transportes_fechamento_mensal;"
        ),

        # 3. View SQL 2: Por Programa / Projeto Social
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW vw_transportes_por_programa AS
            SELECT
                CONCAT(COALESCE(NULLIF(programa, ''), 'Não Informado'), '_', plataforma, '_', SUBSTRING(arquivo_origem FROM 1 FOR 4), '_', SUBSTRING(arquivo_origem FROM 6 FOR 2)) AS id,
                COALESCE(NULLIF(programa, ''), 'Não Informado') AS programa,
                plataforma,
                SUBSTRING(arquivo_origem FROM 1 FOR 4) AS ano,
                SUBSTRING(arquivo_origem FROM 6 FOR 2) AS mes,
                COUNT(id) AS total_viagens,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(SUM(distancia_km), 0) AS total_km,
                COUNT(DISTINCT nome_completo) AS total_colaboradores
            FROM integrations_transportecorrida
            GROUP BY programa, plataforma, ano, mes
            ORDER BY programa, ano DESC, mes DESC;
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_transportes_por_programa;"
        ),

        # 4. View SQL 3: Por Colaborador / Educador Social
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW vw_transportes_por_colaborador AS
            SELECT
                CONCAT(COALESCE(NULLIF(email, ''), NULLIF(nome_completo, ''), 'Anonimo'), '_', SUBSTRING(arquivo_origem FROM 1 FOR 4), '_', SUBSTRING(arquivo_origem FROM 6 FOR 2)) AS id,
                COALESCE(NULLIF(nome_completo, ''), 'Não informado') AS nome_completo,
                COALESCE(NULLIF(email, ''), '-') AS email,
                COALESCE(NULLIF(MAX(programa), ''), 'Geral') AS programa,
                SUBSTRING(arquivo_origem FROM 1 FOR 4) AS ano,
                SUBSTRING(arquivo_origem FROM 6 FOR 2) AS mes,
                COUNT(id) AS total_viagens,
                COALESCE(SUM(valor_total), 0) AS valor_total,
                COALESCE(SUM(distancia_km), 0) AS total_km
            FROM integrations_transportecorrida
            GROUP BY nome_completo, email, ano, mes
            ORDER BY nome_completo, ano DESC, mes DESC;
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_transportes_por_colaborador;"
        ),
    ]
