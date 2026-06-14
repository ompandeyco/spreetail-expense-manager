from rest_framework import viewsets
from .models import Settlement
from .serializers import SettlementSerializer

class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.select_related("from_user", "to_user")
    serializer_class = SettlementSerializer
