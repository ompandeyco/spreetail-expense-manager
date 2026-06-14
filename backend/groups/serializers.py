from rest_framework import serializers
from .models import ExpenseGroup, Membership
from users.serializers import UserSerializer

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Membership
        fields = ["id", "group", "user", "joined_at", "left_at"]

class ExpenseGroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = ExpenseGroup
        fields = ["id", "name", "created_by", "memberships", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

class ExpenseGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseGroup
        fields = ["name"]
