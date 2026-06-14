from rest_framework import viewsets
from .models import ExpenseGroup
from .serializers import ExpenseGroupSerializer, ExpenseGroupCreateSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = ExpenseGroup.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ExpenseGroupCreateSerializer
        return ExpenseGroupSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
