from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0005_ongsysauditlog"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ongsysendpointstatus",
            options={
                "ordering": ["endpoint_id"],
                "permissions": [
                    ("test_ongsys_api", "Pode executar testes de leitura na API OngSys"),
                    ("sync_ongsys_data", "Pode sincronizar dados da API OngSys"),
                    ("view_ongsys_report", "Pode visualizar relatórios da integração OngSys"),
                ],
                "verbose_name": "Status de Endpoint OngSys",
                "verbose_name_plural": "Status de Endpoints OngSys",
            },
        ),
    ]
