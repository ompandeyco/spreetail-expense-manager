"""
Groups app models.

A Group is a collection of users who share expenses together
(e.g., a trip, a household, a team).
"""

from django.conf import settings
from django.db import models


class Group(models.Model):
    """
    Represents a shared expense group.
    `settings.AUTH_USER_MODEL` always points to our custom User model.
    """

    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,         # If creator is deleted, delete the group too
        related_name="created_groups",
    )

    # ManyToMany: one group has many members, one user can be in many groups
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="expense_groups",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)  # Set once on creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated on every save

    def __str__(self):
        return self.name
