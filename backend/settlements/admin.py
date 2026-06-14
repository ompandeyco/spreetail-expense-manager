"""Register Settlement in Django admin panel."""

from django.contrib import admin
from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["payer", "payee", "amount", "group", "date"]
