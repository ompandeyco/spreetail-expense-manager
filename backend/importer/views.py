from rest_framework import generics
from .models import ImportIssue
from .serializers import ImportIssueSerializer

class ImportIssueListCreateView(generics.ListCreateAPIView):
    queryset = ImportIssue.objects.all()
    serializer_class = ImportIssueSerializer

class ImportIssueDetailView(generics.RetrieveAPIView):
    queryset = ImportIssue.objects.all()
    serializer_class = ImportIssueSerializer
