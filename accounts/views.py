"""
Authentication views for Study Vault backend.
"""

import logging
import mimetypes

from django.db import IntegrityError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer
)


logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    Endpoint: POST /api/auth/register/
    Registers a new student user and returns JWT tokens + user profile.
    """
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            # Two sign-ups racing for the same username / email.
            return Response({"detail": "That username or email is already registered."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Registration failed while creating the user")
            return Response({"detail": "Could not create the account right now. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Generate tokens immediately upon registration
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data
        except Exception:
            logger.exception("Registration failed while issuing tokens for user %s", user.pk)
            return Response({"detail": "Account created. Please sign in."},
                            status=status.HTTP_201_CREATED)

        return Response({
            'user': user_data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully.'
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """
    Endpoint: POST /api/auth/login/
    Authenticates user credentials and returns access and refresh JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class LogoutView(generics.GenericAPIView):
    """
    Endpoint: POST /api/auth/logout/
    Blacklists the provided refresh token to securely log out.
    """
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK
        )


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Endpoint: GET /api/auth/me/, PATCH /api/auth/me/
    Retrieves or updates authenticated student profile.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


MAX_PHOTO_BYTES = 3 * 1024 * 1024  # 3 MB
ALLOWED_PHOTO_TYPES = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')


def _sniff_image_type(data):
    """Detect the real image type from the first bytes (phones often send a generic type)."""
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return ''


class ProfilePhotoView(APIView):
    """
    Endpoint: /api/auth/me/photo/
      GET    -> raw image bytes of the authenticated user's profile picture (404 if none)
      POST   -> multipart upload, field name "photo" (JPEG/PNG/WEBP/GIF, max 3 MB)
      DELETE -> remove the uploaded picture (falls back to the emoji avatar)
    """
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        if not user.photo_data:
            return Response({"detail": "No profile photo."}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(bytes(user.photo_data), content_type=user.photo_content_type or 'image/jpeg')
        response['Cache-Control'] = 'private, max-age=0, must-revalidate'
        return response

    def post(self, request):
        upload = request.FILES.get('photo') or request.FILES.get('file') or request.FILES.get('image')
        if upload is None:
            return Response({"detail": "No file uploaded (expected field 'photo')."},
                            status=status.HTTP_400_BAD_REQUEST)
        if upload.size > MAX_PHOTO_BYTES:
            return Response({"detail": "Photo is too large. Maximum size is 3 MB."},
                            status=status.HTTP_400_BAD_REQUEST)
        data = upload.read()
        content_type = _sniff_image_type(data) or (upload.content_type or '').lower()
        if content_type in ('', 'application/octet-stream'):
            content_type = mimetypes.guess_type(upload.name or '')[0] or ''
        if content_type not in ALLOWED_PHOTO_TYPES:
            return Response({"detail": "Unsupported image type. Use JPEG, PNG, WEBP or GIF."},
                            status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        user.photo_data = data
        user.photo_content_type = content_type
        user.photo_updated_at = timezone.now()
        user.save(update_fields=['photo_data', 'photo_content_type', 'photo_updated_at', 'updated_at'])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        user.photo_data = None
        user.photo_content_type = ''
        user.photo_updated_at = timezone.now()
        user.save(update_fields=['photo_data', 'photo_content_type', 'photo_updated_at', 'updated_at'])
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
