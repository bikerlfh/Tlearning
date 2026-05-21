import uuid

from django.db import models
from django.utils import timezone

from .enums import FsrsState, ReviewStatus


class ReviewState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact = models.OneToOneField(
        "artifacts.Artifact",
        on_delete=models.CASCADE,
        related_name="review_state",
    )
    state = models.CharField(max_length=16, choices=FsrsState.choices, default=FsrsState.NEW)
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    stability = models.FloatField(null=True, blank=True)
    difficulty = models.FloatField(null=True, blank=True)
    due_at = models.DateTimeField(default=timezone.now)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    reps = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["status", "due_at"]),
            models.Index(fields=["state", "due_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.artifact.lemma} [{self.state}/{self.status}]"
