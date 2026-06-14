from rest_framework import serializers
from .models import Expense, ExpenseSplit

class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = ["id", "user", "split_type", "value", "final_amount"]

class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id", "group", "description", "paid_by", "amount", 
            "currency", "exchange_rate", "converted_amount", 
            "expense_date", "status", "splits", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
