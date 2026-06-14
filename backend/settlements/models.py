"""
Settlements app models.

A Settlement records that one user paid another user back,
clearing some or all of their shared expense debt.
"""

from django.conf import settings
from django.db import models
from groups.models import Group


class Settlement(models.Model):
    """
    Records a payment from one user (payer) to another (payee).
    Example: Alice pays Bob $30 to settle their Restaurant bill.
    """

    group  = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="settlements",
    )
    payer  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",    # settlements where this user paid
    )
    payee  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_received", # settlements where this user was paid
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note   = models.TextField(blank=True)
    date   = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payer} → {self.payee}: ${self.amount}"
