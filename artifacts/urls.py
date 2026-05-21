from django.urls import path

from .views import (
    ArtifactDetailView,
    ArtifactListCreateView,
    MarkLearnedView,
    SuspendView,
)

urlpatterns = [
    path("artifacts", ArtifactListCreateView.as_view()),
    path("artifacts/<uuid:pk>", ArtifactDetailView.as_view()),
    path("artifacts/<uuid:pk>/mark-learned", MarkLearnedView.as_view()),
    path("artifacts/<uuid:pk>/suspend", SuspendView.as_view()),
]
