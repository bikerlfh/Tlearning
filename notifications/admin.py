from django.contrib import admin

from .models import NotificationLog, NotificationPreference, PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "user_agent", "failure_count", "last_success_at", "created_at")
    list_filter = ("failure_count",)
    search_fields = ("user__email", "endpoint")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "enabled",
        "frequency_per_day",
        "quiet_hours_start",
        "quiet_hours_end",
        "weekdays_only",
    )
    list_filter = ("enabled", "weekdays_only")


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "artifact", "status", "sent_at", "clicked_at")
    list_filter = ("status",)
    search_fields = ("user__email",)
