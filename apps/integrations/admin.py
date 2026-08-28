from django.contrib import admin

from .models import (
    IntegrationCheckpoint,
    IntegrationStagingRecord,
    IntegrationSyncRun,
    IntegrationSystem,
    Warehouse,
)

admin.site.register(IntegrationSystem)
admin.site.register(IntegrationSyncRun)
admin.site.register(IntegrationCheckpoint)
admin.site.register(IntegrationStagingRecord)
admin.site.register(Warehouse)
