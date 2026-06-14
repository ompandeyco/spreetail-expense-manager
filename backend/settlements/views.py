"""
Settlements views.
"""

from rest_framework import viewsets
from .models import Settlement
from .serializers import SettlementSerializer


class SettlementViewSet(viewsets.ModelViewSet):
    """
    Handles all CRUD operations for settlements.
    GET    /api/settlements/        → list all settlements
    POST   /api/settlements/        → record a new settlement
    GET    /api/settlements/<id>/   → get a single settlement
    """

    queryset = Settlement.objects.select_related("group", "payer", "payee")
    serializer_class = SettlementSerializer
