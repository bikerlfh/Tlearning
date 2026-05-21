from django.contrib.auth import authenticate, login, logout
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ApiToken
from accounts.tokens import generate_token, hash_token

from .models import User
from .serializers import (
    ApiTokenCreateSerializer,
    ApiTokenSerializer,
    SignupSerializer,
    UpdateMeSerializer,
    UserSerializer,
)


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UpdateMeSerializer
        return UserSerializer


class ApiTokenListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return ApiToken.objects.filter(user=self.request.user, revoked_at__isnull=True)

    def get_serializer_class(self):
        return ApiTokenCreateSerializer if self.request.method == "POST" else ApiTokenSerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get("name", "").strip()
        if not name:
            return Response(
                {"name": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST
            )
        raw = generate_token()
        token = ApiToken.objects.create(user=request.user, token_hash=hash_token(raw), name=name)
        data = ApiTokenCreateSerializer(token).data
        data["token"] = raw  # show raw exactly once
        return Response(data, status=status.HTTP_201_CREATED)


class ApiTokenDeleteView(generics.DestroyAPIView):
    def get_queryset(self):
        return ApiToken.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        from django.utils import timezone

        instance.revoked_at = timezone.now()
        instance.save(update_fields=["revoked_at"])
