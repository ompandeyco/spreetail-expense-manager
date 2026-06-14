"""
Users views.

`generics.CreateAPIView` gives us a POST endpoint for free —
we just tell it which serializer to use.
`AllowAny` means no JWT token required (users need to register first).
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Creates a new user account. No authentication needed.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # Anyone can register


class MeView(APIView):
    """
    GET /api/users/me/
    Returns the currently logged-in user's profile.
    Requires a valid JWT token.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # `request.user` is populated automatically by JWT authentication
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
