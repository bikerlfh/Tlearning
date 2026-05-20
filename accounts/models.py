import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone as django_timezone

from .enums import UiLanguage
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    preferred_ui_language = models.CharField(
        max_length=8, choices=UiLanguage.choices, default=UiLanguage.SPANISH
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=django_timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email
