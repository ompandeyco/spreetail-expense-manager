"""
Users app models.

We extend Django's AbstractUser so we keep all built-in fields
(username, password, email, etc.) and can add custom fields later.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    Extending AbstractUser means Django handles password hashing,
    login, and permissions for us automatically.
    """

    # Extra fields we add on top of the default ones
    phone_number = models.CharField(max_length=20, blank=True)
    avatar_url   = models.URLField(blank=True)

    def __str__(self):
        # This is what shows up in the admin panel
        return self.email
