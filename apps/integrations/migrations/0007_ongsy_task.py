import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0006_ongsys_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OngsysTask",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tipo", models.CharField(choices=[("test_all", "Testar rotas de leitura"), ("sync_db", "Sincronizar banco")], max_length=16)),
                ("status", models.CharField(choices=[("queued", "Na fila"), ("running", "Em execução"), ("completed", "Concluída"), ("partial", "Concluída parcialmente"), ("error", "Com erro")], db_index=True, default="queued", max_length=16)),
                ("entidade", models.CharField(default="all", max_length=32)),
                ("paginas", models.PositiveSmallIntegerField(default=1)),
                ("progresso_pct", models.PositiveSmallIntegerField(default=0)),
                ("etapa_atual", models.CharField(blank=True, max_length=255)),
                ("total_itens", models.PositiveSmallIntegerField(default=0)),
                ("itens_concluidos", models.PositiveSmallIntegerField(default=0)),
                ("resultados", models.JSONField(blank=True, default=list)),
                ("erro", models.TextField(blank=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("iniciado_em", models.DateTimeField(blank=True, null=True)),
                ("finalizado_em", models.DateTimeField(blank=True, null=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("solicitante", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ongsys_tasks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Tarefa OngSys",
                "verbose_name_plural": "Tarefas OngSys",
                "ordering": ["-criado_em"],
            },
        ),
        migrations.AddConstraint(
            model_name="ongsystask",
            constraint=models.UniqueConstraint(condition=models.Q(status="running"), fields=("tipo", "entidade"), name="uniq_running_ongsys_task_entity"),
        ),
    ]
