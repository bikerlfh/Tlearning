import uuid

from django.conf import settings
from django.db import models

from .enums import ArtifactSource, ArtifactType


class Artifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="artifacts"
    )
    deck = models.ForeignKey("decks.Deck", on_delete=models.CASCADE, related_name="artifacts")
    type = models.CharField(max_length=20, choices=ArtifactType.choices)
    lemma = models.CharField(max_length=200)
    source_language = models.CharField(max_length=8)
    target_language = models.CharField(max_length=8)
    data = models.JSONField(default=dict)
    source = models.CharField(max_length=20, choices=ArtifactSource.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "deck", "type", "lemma"],
                name="unique_artifact_per_user_deck_type_lemma",
            )
        ]
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["user", "lemma"]),
        ]

    def __str__(self) -> str:
        return f"{self.lemma} ({self.type})"
