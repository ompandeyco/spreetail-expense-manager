from django.db import models

class ImportIssue(models.Model):
    """
    Tracks errors or inconsistencies found during the CSV import process.
    This model exists to help users systematically review and resolve data issues
    (like missing fields or mismatched names) without failing the entire import.
    """
    row_number = models.PositiveIntegerField()
    issue_type = models.CharField(max_length=100)
    original_value = models.TextField(blank=True, null=True)
    suggested_action = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Row {self.row_number}: {self.issue_type} ({self.status})"
