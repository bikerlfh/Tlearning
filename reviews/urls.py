from django.urls import path

from .views import AnswerView, QueueView, StatsView

urlpatterns = [
    path("reviews/queue", QueueView.as_view()),
    path("reviews/stats", StatsView.as_view()),
    path("reviews/<uuid:artifact_id>/answer", AnswerView.as_view()),
]
