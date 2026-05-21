from django.urls import path

from .views import ArtifactDetailView, ArtifactListCreateView

urlpatterns = [
    path("artifacts", ArtifactListCreateView.as_view()),
    path("artifacts/<uuid:pk>", ArtifactDetailView.as_view()),
]
