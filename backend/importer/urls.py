"""Importer URL routes."""

from django.urls import path
from .views import ImportJobListCreateView, ImportJobDetailView

urlpatterns = [
    path("",        ImportJobListCreateView.as_view(), name="importjob-list"),
    path("<int:pk>/", ImportJobDetailView.as_view(),    name="importjob-detail"),
]
