from django.urls import path

from .views import PreferenceView, SubscriptionDeleteView, SubscriptionListCreateView

urlpatterns = [
    path("notifications/subscriptions", SubscriptionListCreateView.as_view()),
    path("notifications/subscriptions/<uuid:pk>", SubscriptionDeleteView.as_view()),
    path("notifications/preferences", PreferenceView.as_view()),
]
