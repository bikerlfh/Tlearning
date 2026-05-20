from django.contrib import admin
from django.urls import path

# api.urls included once the api app exists (Task 9).
urlpatterns = [
    path("admin/", admin.site.urls),
]
