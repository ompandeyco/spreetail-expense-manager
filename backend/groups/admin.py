from django.contrib import admin
from .models import ExpenseGroup, Membership

@admin.register(ExpenseGroup)
class ExpenseGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at"]

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["group", "user", "joined_at", "left_at"]
