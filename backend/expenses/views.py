"""
Expenses views.
"""

from rest_framework import viewsets
from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    Handles all CRUD operations for expenses.
    GET    /api/expenses/         → list all expenses
    POST   /api/expenses/         → create an expense
    GET    /api/expenses/<id>/    → get a specific expense
    PUT    /api/expenses/<id>/    → update an expense
    DELETE /api/expenses/<id>/    → delete an expense
    """

    queryset = Expense.objects.select_related("group", "paid_by").prefetch_related("splits")
    # `select_related` fetches group and paid_by in the same SQL query (avoids N+1 queries)
    # `prefetch_related` fetches splits efficiently in a second query

    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        """Automatically set paid_by to the currently logged-in user."""
        serializer.save(paid_by=self.request.user)
