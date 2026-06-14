from django.contrib import admin
from .models import Expense, ExpenseSplit

class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 0

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["description", "amount", "currency", "group", "paid_by", "expense_date", "status"]
    inlines = [ExpenseSplitInline]
