"""Register User model in Django admin panel."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    We extend Django's built-in UserAdmin so the admin panel
    still shows the password change form and all default fields.
    """
    # Add our custom fields to the admin display
    list_display = ["username", "email", "phone_number", "is_staff"]
