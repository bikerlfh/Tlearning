from django.urls import include, path

from .views import HealthView, SentryDebugView

urlpatterns = [
    path("health", HealthView.as_view()),
    path("_debug/sentry", SentryDebugView.as_view()),
    path("auth/", include("accounts.urls")),
    path("", include("decks.urls")),
    path("", include("artifacts.urls")),
    path("", include("reviews.urls")),
    path("", include("notifications.urls")),
]
