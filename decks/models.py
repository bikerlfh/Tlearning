import uuid

from django.conf import settings
from django.db import models


class Deck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="decks"
    )
    name = models.CharField(max_length=100)
    source_language = models.CharField(max_length=8)
    target_language = models.CharField(max_length=8)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="one_default_deck_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.source_language}->{self.target_language})"
