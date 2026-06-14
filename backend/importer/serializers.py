from rest_framework import serializers
from .models import ImportIssue

class ImportIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportIssue
        fields = ["id", "row_number", "issue_type", "original_value", "suggested_action", "status", "created_at"]
