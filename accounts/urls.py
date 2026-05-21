from django.urls import path

from .views import (
    ApiTokenDeleteView,
    ApiTokenListCreateView,
    GoogleBeginView,
    GoogleCallbackView,
    LoginView,
    LogoutView,
    MeView,
    SignupView,
)

urlpatterns = [
    path("signup", SignupView.as_view()),
    path("login", LoginView.as_view()),
    path("logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
    path("api-tokens", ApiTokenListCreateView.as_view()),
    path("api-tokens/<uuid:pk>", ApiTokenDeleteView.as_view()),
    path("google/begin", GoogleBeginView.as_view()),
    path("google/callback", GoogleCallbackView.as_view()),
]
