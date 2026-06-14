"""
Expenses app models.

An Expense belongs to a Group and is paid by one User.
ExpenseSplit tracks how much each member owes for that expense.
"""

from django.conf import settings
from django.db import models
from groups.models import Group


class Expense(models.Model):
    """
    A single shared expense (e.g., 'Dinner at Pizza Hut - $60').
    """

    # Category choices defined as constants so they're easy to read
    CATEGORY_FOOD       = "food"
    CATEGORY_TRAVEL     = "travel"
    CATEGORY_UTILITIES  = "utilities"
    CATEGORY_OTHER      = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_FOOD,      "Food"),
        (CATEGORY_TRAVEL,    "Travel"),
        (CATEGORY_UTILITIES, "Utilities"),
        (CATEGORY_OTHER,     "Other"),
    ]

    title       = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)  # e.g. 9999999.99
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    date        = models.DateField()
    description = models.TextField(blank=True)
    receipt_url = models.URLField(blank=True)

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paid_expenses",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (${self.amount})"


class ExpenseSplit(models.Model):
    """
    Tracks how much each user owes for a specific expense.
    One Expense → many ExpenseSplits (one per member).
    """

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expense_splits",
    )
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    is_settled  = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} owes ${self.amount_owed} for {self.expense.title}"
