from rest_framework import serializers

from .models import NotificationPreference, PushSubscription


class PushSubscriptionSerializer(serializers.ModelSerializer):
    # Override to drop the auto-added UniqueValidator so upsert via
    # update_or_create works on repeat POSTs with the same endpoint.
    endpoint = serializers.CharField()

    class Meta:
        model = PushSubscription
        fields = [
            "id",
            "endpoint",
            "p256dh_key",
            "auth_key",
            "user_agent",
            "created_at",
            "last_success_at",
            "failure_count",
        ]
        read_only_fields = ["id", "created_at", "last_success_at", "failure_count"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "enabled",
            "frequency_per_day",
            "min_interval_minutes",
            "quiet_hours_start",
            "quiet_hours_end",
            "weekdays_only",
        ]
