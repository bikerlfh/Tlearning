from django.urls import path

from .views import (
    NotificationClickedView,
    PreferenceView,
    SubscriptionDeleteView,
    SubscriptionListCreateView,
    TestNotificationView,
)

urlpatterns = [
    path("notifications/subscriptions", SubscriptionListCreateView.as_view()),
    path("notifications/subscriptions/<uuid:pk>", SubscriptionDeleteView.as_view()),
    path("notifications/preferences", PreferenceView.as_view()),
    path("notifications/test", TestNotificationView.as_view()),
    path("notifications/<uuid:log_id>/clicked", NotificationClickedView.as_view()),
]
