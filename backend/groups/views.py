"""
Groups views.

`ModelViewSet` gives us all 5 CRUD actions for free:
  list()     → GET    /api/groups/
  create()   → POST   /api/groups/
  retrieve() → GET    /api/groups/<id>/
  update()   → PUT    /api/groups/<id>/
  destroy()  → DELETE /api/groups/<id>/
"""

from rest_framework import viewsets
from .models import Group
from .serializers import GroupSerializer, GroupCreateSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """Handles all CRUD operations for expense groups."""

    queryset = Group.objects.all()

    def get_serializer_class(self):
        """
        Use a simpler serializer when creating/updating,
        and the full nested serializer when reading.
        """
        if self.action in ["create", "update", "partial_update"]:
            return GroupCreateSerializer
        return GroupSerializer

    def perform_create(self, serializer):
        """
        Override perform_create so Django automatically sets
        `created_by` to the currently logged-in user.
        """
        serializer.save(created_by=self.request.user)
