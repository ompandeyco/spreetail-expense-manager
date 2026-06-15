from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ImportIssue
from .serializers import ImportIssueSerializer
from .services import ImportService

class ImportIssueListCreateView(generics.ListCreateAPIView):
    queryset = ImportIssue.objects.all()
    serializer_class = ImportIssueSerializer

class ImportIssueDetailView(generics.RetrieveAPIView):
    queryset = ImportIssue.objects.all()
    serializer_class = ImportIssueSerializer

class CsvImportAPIView(APIView):
    """
    Endpoint for uploading a CSV file to import expenses.
    URL: /api/import/csv/
    Method: POST
    Expects: multipart/form-data with 'file' and 'group_id'
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        group_id = request.data.get('group_id')
        
        if not file_obj or not group_id:
            return Response({"error": "Both 'file' and 'group_id' are required"}, status=400)
            
        try:
            service = ImportService(file_obj, group_id, request.user)
            report = service.process()
            return Response(report, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
