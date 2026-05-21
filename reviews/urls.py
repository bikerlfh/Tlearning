from django.urls import path

from .views import QueueView

urlpatterns = [
    path("reviews/queue", QueueView.as_view()),
]
