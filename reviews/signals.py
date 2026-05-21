from django.db.models.signals import post_save
from django.dispatch import receiver

from artifacts.models import Artifact

from .models import ReviewState


@receiver(post_save, sender=Artifact)
def create_review_state(sender, instance, created, **kwargs):
    if created:
        ReviewState.objects.create(artifact=instance)
