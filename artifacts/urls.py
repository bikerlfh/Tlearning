from django.urls import path

from .views import ArtifactListCreateView

urlpatterns = [
    path("artifacts", ArtifactListCreateView.as_view()),
]
