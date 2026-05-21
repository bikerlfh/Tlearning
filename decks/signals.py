from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Deck


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_deck(sender, instance, created, **kwargs):
    if not created:
        return
    target = "en" if instance.preferred_ui_language != "en" else "es"
    Deck.objects.create(
        user=instance,
        name="My deck",
        source_language=instance.preferred_ui_language,
        target_language=target,
        is_default=True,
    )
