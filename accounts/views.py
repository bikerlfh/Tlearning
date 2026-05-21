from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
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


class SocialAccountListView(APIView):
    def get(self, request):
        rows = SocialAccount.objects.filter(user=request.user)
        results = [
            {
                "id": str(r.id),
                "provider": r.provider,
                "uid": r.uid,
                "email": (r.extra_data or {}).get("email"),
                "name": (r.extra_data or {}).get("name"),
                "connected_at": r.date_joined.isoformat() if r.date_joined else None,
            }
            for r in rows
        ]
        return Response({"count": len(results), "results": results})


class SocialAccountDisconnectView(APIView):
    def post(self, request, pk):
        account = SocialAccount.objects.filter(user=request.user, pk=pk).first()
        if not account:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        # Block the user from locking themselves out: require a usable password if this
        # is their last login method.
        has_password = request.user.has_usable_password()
        other_socials = SocialAccount.objects.filter(user=request.user).exclude(pk=pk).exists()
        if not has_password and not other_socials:
            return Response(
                {"detail": "Set a password before disconnecting your only sign-in method."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    """Always returns 204 to avoid leaking which emails are registered."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend = settings.FRONTEND_URL.rstrip("/")
            reset_url = f"{frontend}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject="Reset your Tlearning password",
                message=(
                    "Someone (hopefully you) requested a password reset. "
                    f"Click the link to choose a new password:\n\n{reset_url}\n\n"
                    "If you didn't ask for this, you can safely ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid_b64 = request.data.get("uid", "")
        token = request.data.get("token", "")
        password = request.data.get("password", "")

        if not uid_b64 or not token or not password:
            return Response(
                {"detail": "uid, token, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = urlsafe_base64_decode(uid_b64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, UnicodeDecodeError):
            return Response(
                {"detail": "Invalid or expired link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password, user)
        except ValidationError as exc:
            return Response({"password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)
