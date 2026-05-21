from django.apps import AppConfig


class DecksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "decks"

    def ready(self):
        from . import signals  # noqa: F401
