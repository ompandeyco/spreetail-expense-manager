"""
Importer serializers.
"""

from rest_framework import serializers
from .models import ImportJob


class ImportJobSerializer(serializers.ModelSerializer):
    """Serializes an import job for API responses."""

    class Meta:
        model  = ImportJob
        fields = ["id", "uploaded_by", "file_name", "status", "row_count", "error_log", "created_at", "updated_at"]
        read_only_fields = ["id", "uploaded_by", "status", "row_count", "error_log", "created_at", "updated_at"]
