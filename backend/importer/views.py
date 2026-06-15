"""
importer/views.py

Exposes two surfaces:
  1. CsvImportAPIView      — POST /api/import/csv/   (the main feature)
  2. ImportIssueListView   — GET  /api/importer/      (browse persisted issues)
  3. ImportIssueDetailView — GET  /api/importer/<pk>/ (single issue detail)
"""

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import ImportIssue
from .serializers import ImportIssueSerializer
from .services import ImportService


class ImportIssueListView(generics.ListAPIView):
    """
    GET /api/importer/
    Returns all persisted ImportIssue records, newest first.
    Useful for auditing past imports.
    """
    queryset = ImportIssue.objects.all().order_by("-created_at")
    serializer_class = ImportIssueSerializer


class ImportIssueDetailView(generics.RetrieveAPIView):
    """
    GET /api/importer/<pk>/
    Returns a single ImportIssue record.
    """
    queryset = ImportIssue.objects.all()
    serializer_class = ImportIssueSerializer


class CsvImportAPIView(APIView):
    """
    POST /api/import/csv/

    Accepts a multipart CSV file upload and runs the full ImportService pipeline.

    Request (multipart/form-data):
        file     — the CSV file to import
        group_id — integer PK of the ExpenseGroup to import into

    Response 200:
        {
            "total_rows":         int,
            "successful_imports": int,
            "issues": [
                {
                    "row":            int,
                    "problem":        str,
                    "original_value": str,
                    "action_taken":   str
                }
            ]
        }

    Response 400: missing file or group_id.
    Response 500: unexpected server error (should not normally occur — ImportService
                  is designed to catch and log all row-level errors internally).

    Interview note:
        We use IsAuthenticated so that request.user is always a real User object,
        which ImportService passes as the settlement "to_user" fallback.
        In a production system you would also check that request.user is a member
        of the target group before allowing the import.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file")
        group_id = request.data.get("group_id")

        # --- Input validation ---
        if not file_obj:
            return Response(
                {"error": "A CSV file is required. Send it as 'file' in multipart/form-data."},
                status=400,
            )
        if not group_id:
            return Response(
                {"error": "'group_id' is required. It must be the integer PK of the target ExpenseGroup."},
                status=400,
            )

        try:
            group_id = int(group_id)
        except (ValueError, TypeError):
            return Response({"error": "'group_id' must be an integer."}, status=400)

        # --- Run the import pipeline ---
        try:
            service = ImportService(
                file_obj=file_obj,
                group_id=group_id,
                uploaded_by=request.user,
            )
            report = service.process()
            return Response(report, status=200)

        except Exception as exc:
            # This branch should rarely be reached because ImportService catches
            # row-level errors internally. If we land here it's a systemic bug.
            return Response(
                {"error": f"Unexpected import failure: {str(exc)}"},
                status=500,
            )
