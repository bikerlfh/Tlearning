from django.db import models


class UiLanguage(models.TextChoices):
    SPANISH = "es", "Español"
    ENGLISH = "en", "English"
