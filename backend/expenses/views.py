from rest_framework import viewsets
from .models import Expense
from .serializers import ExpenseSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related("group", "paid_by").prefetch_related("splits")
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(paid_by=self.request.user)
