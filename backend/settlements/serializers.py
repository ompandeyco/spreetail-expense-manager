from rest_framework import serializers
from .models import Settlement

class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ["id", "from_user", "to_user", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]
