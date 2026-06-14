"""
Users serializers.

A serializer converts a Django model instance ↔ JSON.
It also validates incoming data before saving.
"""

from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes the User model for read operations (GET requests).
    We never expose the password field in responses.
    """

    class Meta:
        model  = User
        fields = ["id", "username", "email", "phone_number", "avatar_url", "date_joined"]
        # `read_only_fields` means these come out in responses but can't be set via API
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for user registration (POST /api/users/register/).
    We write the password separately so it gets properly hashed.
    """

    # `write_only=True` means this field is accepted on input but never sent back
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ["username", "email", "password", "phone_number"]

    def create(self, validated_data):
        """
        Override create() so we use `create_user()` which hashes the password.
        If we used `User.objects.create()` directly, the password would be stored as plain text!
        """
        return User.objects.create_user(**validated_data)
