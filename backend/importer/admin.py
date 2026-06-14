"""Register ImportJob in Django admin panel."""

from django.contrib import admin
from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display  = ["id", "uploaded_by", "file_name", "status", "row_count", "created_at"]
    list_filter   = ["status"]
