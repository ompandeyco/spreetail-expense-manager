from django.conf import settings
from django.db import models
from groups.models import ExpenseGroup

class Expense(models.Model):
    """
    Records a cost incurred by the group.
    This model exists to serve as the single source of truth for an expense event,
    tracking the total amount, currency, and the user who paid it.
    """
    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name="expenses"
    )
    description = models.CharField(max_length=255)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paid_expenses"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1.0)
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    status = models.CharField(max_length=50, default="active")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} ({self.amount} {self.currency})"

class ExpenseSplit(models.Model):
    """
    Defines how much a specific user owes for a specific expense.
    This model exists because expenses can be divided unequally (e.g., percentages, exact amounts)
    and we need to know the exact breakdown for every participant.
    """
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expense_splits"
    )
    split_type = models.CharField(max_length=50, default="equal")
    value = models.DecimalField(max_digits=12, decimal_places=2)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.user} owes {self.final_amount} for {self.expense.description}"
