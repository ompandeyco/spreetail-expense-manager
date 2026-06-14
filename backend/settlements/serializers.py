"""
Settlements serializers.
"""

from rest_framework import serializers
from .models import Settlement


class SettlementSerializer(serializers.ModelSerializer):
    """Serializes a settlement record."""

    class Meta:
        model  = Settlement
        fields = ["id", "group", "payer", "payee", "amount", "note", "date", "created_at"]
        read_only_fields = ["id", "created_at"]
