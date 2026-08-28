from django.db import models


class IntegrationSystem(models.Model):
    class Direction(models.TextChoices):
        SOURCE = "source", "Fonte de dados"
        DESTINATION = "destination", "Destino de dados"
        BIDIRECTIONAL = "bidirectional", "Bidirecional"

    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class IntegrationSyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Em execução"
        SUCCEEDED = "succeeded", "Concluída"
        FAILED = "failed", "Falhou"

    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    dataset = models.CharField(max_length=64)
    correlation_id = models.UUIDField(unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    contract_version = models.CharField(max_length=16, default="v1")
    modified_since = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    pages_processed = models.PositiveIntegerField(default=0)
    records_received = models.PositiveIntegerField(default=0)
    records_inserted = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    last_cursor = models.TextField(blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]


class IntegrationCheckpoint(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=64)
    completed_through = models.DateTimeField(null=True, blank=True)
    resume_cursor = models.TextField(blank=True)
    resume_modified_since = models.DateTimeField(null=True, blank=True)
    last_run = models.ForeignKey(
        IntegrationSyncRun, on_delete=models.SET_NULL, null=True, blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "dataset"), name="uniq_checkpoint_system_dataset"
            )
        ]


class IntegrationStagingRecord(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    dataset = models.CharField(max_length=64)
    source_name = models.CharField(max_length=255)
    source_modified = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField()
    contract_version = models.CharField(max_length=16)
    imported_by_run = models.ForeignKey(IntegrationSyncRun, on_delete=models.PROTECT)
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "dataset", "source_name"),
                name="uniq_staging_source_dataset_name",
            )
        ]
        indexes = [models.Index(fields=("system", "dataset", "source_modified"))]


class Warehouse(models.Model):
    system = models.ForeignKey(IntegrationSystem, on_delete=models.PROTECT)
    source_name = models.CharField(max_length=255)
    warehouse_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=120, blank=True)
    source_modified = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    imported_by_run = models.ForeignKey(IntegrationSyncRun, on_delete=models.PROTECT)
    ingested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("system", "source_name"), name="uniq_warehouse_system_name"
            )
        ]
