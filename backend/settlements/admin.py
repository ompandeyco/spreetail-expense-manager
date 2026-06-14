from django.contrib import admin
from .models import Settlement

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user", "amount", "created_at"]
