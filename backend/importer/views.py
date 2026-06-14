"""
Importer views.

Only list and create — you don't edit or delete import jobs.
"""

from rest_framework import generics
from .models import ImportJob
from .serializers import ImportJobSerializer


class ImportJobListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/importer/   → list all import jobs for the current user
    POST /api/importer/   → start a new import job
    """

    serializer_class = ImportJobSerializer

    def get_queryset(self):
        """Only return import jobs that belong to the logged-in user."""
        return ImportJob.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        """Automatically attach the logged-in user to the import job."""
        serializer.save(uploaded_by=self.request.user)


class ImportJobDetailView(generics.RetrieveAPIView):
    """
    GET /api/importer/<id>/  → check the status of a single import job
    """

    serializer_class = ImportJobSerializer

    def get_queryset(self):
        return ImportJob.objects.filter(uploaded_by=self.request.user)
