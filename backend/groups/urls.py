"""
Groups URL routes.

`DefaultRouter` automatically generates the following URLs for a ViewSet:
  GET    /api/groups/        → list
  POST   /api/groups/        → create
  GET    /api/groups/<id>/   → retrieve
  PUT    /api/groups/<id>/   → update
  DELETE /api/groups/<id>/   → destroy
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet

# Create a router and register our ViewSet with it
router = DefaultRouter()
router.register(r"", GroupViewSet, basename="group")

urlpatterns = [
    path("", include(router.urls)),
]
