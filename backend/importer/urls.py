from django.urls import path
from .views import ImportIssueListCreateView, ImportIssueDetailView

urlpatterns = [
    path("", ImportIssueListCreateView.as_view(), name="importissue-list"),
    path("<int:pk>/", ImportIssueDetailView.as_view(), name="importissue-detail"),
]
