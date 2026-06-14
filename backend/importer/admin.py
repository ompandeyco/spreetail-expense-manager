from django.contrib import admin
from .models import ImportIssue

@admin.register(ImportIssue)
class ImportIssueAdmin(admin.ModelAdmin):
    list_display = ["row_number", "issue_type", "status"]
