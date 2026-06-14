"""Register Expense and ExpenseSplit models in Django admin panel."""

from django.contrib import admin
from .models import Expense, ExpenseSplit


class ExpenseSplitInline(admin.TabularInline):
    """
    Shows splits directly inside the Expense admin page.
    Inline means you can see and edit splits without navigating away.
    """
    model = ExpenseSplit
    extra = 0  # Don't show empty placeholder rows


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["title", "amount", "category", "group", "paid_by", "date"]
    inlines      = [ExpenseSplitInline]
