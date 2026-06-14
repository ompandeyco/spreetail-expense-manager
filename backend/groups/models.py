from django.conf import settings
from django.db import models

class ExpenseGroup(models.Model):
    """
    Represents a shared expense group (e.g., Trip, Household).
    This model exists to group expenses together and serve as the boundary
    for shared liabilities.
    """
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_expense_groups"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    """
    Tracks which users belong to which ExpenseGroup over time.
    This model exists because membership dates decide who participates in an expense.
    Users are only liable for expenses incurred between their joined_at and left_at dates.
    """
    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} in {self.group}"
