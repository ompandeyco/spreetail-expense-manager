"""
Root URL configuration.

Every app registers its own URLs here.
JWT token endpoints are provided by simplejwt out of the box.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # POST /api/token/         -> returns access + refresh
    TokenRefreshView,      # POST /api/token/refresh/ -> returns new access token
)

urlpatterns = [
    # Django admin panel
    path("admin/", admin.site.urls),

    # JWT authentication endpoints
    path("api/token/",         TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(),    name="token_refresh"),

    # App-level routes — each app manages its own URL file
    path("api/users/",       include("users.urls")),
    path("api/groups/",      include("groups.urls")),
    path("api/expenses/",    include("expenses.urls")),
    path("api/importer/",    include("importer.urls")),
    path("api/settlements/", include("settlements.urls")),
]
