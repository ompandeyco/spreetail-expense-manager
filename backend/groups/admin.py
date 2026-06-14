"""Register Group model in Django admin panel."""

from django.contrib import admin
from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ["name", "created_by", "created_at"]
    # `filter_horizontal` gives a nice UI for the ManyToMany members field
    filter_horizontal = ["members"]
