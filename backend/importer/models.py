"""
Importer app models.

Tracks CSV/file import jobs so users can upload bulk expenses.
"""

from django.conf import settings
from django.db import models


class ImportJob(models.Model):
    """
    Represents one file import attempt by a user.
    Stores the file and the current processing status.
    """

    STATUS_PENDING    = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_DONE       = "done"
    STATUS_FAILED     = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING,    "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_DONE,       "Done"),
        (STATUS_FAILED,     "Failed"),
    ]

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="import_jobs",
    )
    file_name  = models.CharField(max_length=255)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    row_count  = models.PositiveIntegerField(default=0)  # How many rows were in the file
    error_log  = models.TextField(blank=True)             # Any errors during processing

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Import #{self.pk} by {self.uploaded_by} [{self.status}]"
