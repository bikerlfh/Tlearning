from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mixins import UserScopedQuerysetMixin

from .models import NotificationLog, NotificationPreference, PushSubscription
from .serializers import NotificationPreferenceSerializer, PushSubscriptionSerializer
from .tasks import send_push_notification


class SubscriptionListCreateView(UserScopedQuerysetMixin, generics.ListCreateAPIView):
    queryset = PushSubscription.objects.all()
    serializer_class = PushSubscriptionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub, created = PushSubscription.objects.update_or_create(
            endpoint=serializer.validated_data["endpoint"],
            defaults={
                "user": request.user,
                "p256dh_key": serializer.validated_data["p256dh_key"],
                "auth_key": serializer.validated_data["auth_key"],
                "user_agent": serializer.validated_data.get("user_agent", ""),
            },
        )
        out = self.get_serializer(sub).data
        return Response(out, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SubscriptionDeleteView(UserScopedQuerysetMixin, generics.DestroyAPIView):
    queryset = PushSubscription.objects.all()
    serializer_class = PushSubscriptionSerializer
    lookup_field = "pk"


class PreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        return NotificationPreference.objects.get(user=self.request.user)


class TestNotificationView(APIView):
    def post(self, request):
        send_push_notification.delay(request.user.id)
        return Response({"detail": "dispatched"}, status=status.HTTP_202_ACCEPTED)


class NotificationClickedView(APIView):
    """Idempotent click-through recorder. Hit from the service worker on a
    `notificationclick` event — the request may not carry a session cookie if
    the user clicked the OS notification while no tab was open. We accept that
    and treat it as a best-effort metric: anonymous calls return 204 noop."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, log_id):
        user = request.user if request.user.is_authenticated else None
        if user is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        try:
            log = NotificationLog.objects.get(id=log_id, user=user)
        except NotificationLog.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not log.clicked_at:
            log.clicked_at = timezone.now()
            log.save(update_fields=["clicked_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
