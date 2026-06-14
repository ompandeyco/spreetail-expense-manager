from django.conf import settings
from django.db import models

class Settlement(models.Model):
    """
    Records a payment made between two users to resolve debts.
    This model exists to keep track of reimbursements, allowing the system
    to calculate the remaining net balances between members.
    """
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settlements_sent"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settlements_received"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} paid {self.to_user}: {self.amount}"
