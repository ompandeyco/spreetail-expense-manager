"""
Expenses serializers.
"""

from rest_framework import serializers
from .models import Expense, ExpenseSplit


class ExpenseSplitSerializer(serializers.ModelSerializer):
    """Serializes how the expense is split among users."""

    class Meta:
        model  = ExpenseSplit
        fields = ["id", "user", "amount_owed", "is_settled"]


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Serializes a full expense including its splits.
    `splits` is a reverse FK relation — Django creates it automatically
    because we set `related_name='splits'` on the ExpenseSplit model.
    """

    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model  = Expense
        fields = [
            "id", "title", "amount", "category", "date",
            "description", "receipt_url", "group", "paid_by",
            "splits", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
