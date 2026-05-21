from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import oauth
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


class GoogleBeginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        state = oauth.sign_state()
        redirect_uri = request.build_absolute_uri("/api/v1/auth/google/callback")
        url = oauth.build_auth_url(redirect_uri=redirect_uri, state=state)
        response = Response({"url": url})
        response.set_cookie(
            "oauth_state",
            state,
            httponly=True,
            samesite="Lax",
            max_age=oauth.STATE_MAX_AGE,
            secure=not settings.DEBUG,
        )
        return response


class GoogleCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.query_params.get("code", "")
        state = request.query_params.get("state", "")
        cookie_state = request.COOKIES.get("oauth_state", "")
        frontend = settings.FRONTEND_URL.rstrip("/")

        if not code or not state or state != cookie_state:
            return redirect(f"{frontend}/login?error=oauth_state")
        try:
            oauth.verify_state(state)
        except Exception:
            return redirect(f"{frontend}/login?error=oauth_expired")

        try:
            redirect_uri = request.build_absolute_uri("/api/v1/auth/google/callback")
            token_payload = oauth.exchange_code_for_token(code, redirect_uri)
            access_token = token_payload.get("access_token", "")
            if not access_token:
                return redirect(f"{frontend}/login?error=oauth_no_token")
            userinfo = oauth.fetch_userinfo(access_token)
        except Exception:
            return redirect(f"{frontend}/login?error=oauth_exchange")

        email = (userinfo.get("email") or "").strip().lower()
        if not email or not userinfo.get("email_verified", False):
            return redirect(f"{frontend}/login?error=oauth_email")

        sub = userinfo.get("sub", "")
        name = userinfo.get("name", "")

        user, _created = User.objects.get_or_create(
            email=email,
            defaults={"name": name},
        )
        if not user.is_active:
            return redirect(f"{frontend}/login?error=oauth_inactive")

        SocialAccount.objects.update_or_create(
            provider="google",
            uid=sub,
            defaults={
                "user": user,
                "extra_data": userinfo,
            },
        )

        user.backend = "allauth.account.auth_backends.AuthenticationBackend"
        login(request, user)

        response = redirect(f"{frontend}/dashboard")
        response.delete_cookie("oauth_state")
        return response
