"""
Groups serializers.
"""

from rest_framework import serializers
from .models import Group
from users.serializers import UserSerializer


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializes a Group with nested member details.
    `members` is a nested list of user objects (read-only).
    """

    # Show full user objects for members instead of just their IDs
    members    = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model  = Group
        fields = ["id", "name", "description", "created_by", "members", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupCreateSerializer(serializers.ModelSerializer):
    """
    Used when creating a group (only needs name and description).
    `created_by` will be set automatically from the logged-in user.
    """

    class Meta:
        model  = Group
        fields = ["name", "description"]
