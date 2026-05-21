from django.urls import path

from .views import (
    ApiTokenDeleteView,
    ApiTokenListCreateView,
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
]
