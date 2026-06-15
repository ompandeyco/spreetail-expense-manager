"""
importer/urls.py

URL patterns for the importer app.
The main CSV upload endpoint is registered separately in core/urls.py
as POST /api/import/csv/ so it sits at a clean, memorable path.
"""

from django.urls import path
from .views import ImportIssueListView, ImportIssueDetailView

urlpatterns = [
    # GET  /api/importer/       — list all persisted issues (for audit dashboard)
    path("", ImportIssueListView.as_view(), name="importissue-list"),

    # GET  /api/importer/<pk>/  — single issue detail
    path("<int:pk>/", ImportIssueDetailView.as_view(), name="importissue-detail"),
]
