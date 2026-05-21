from django.db import models


class NotificationStatus(models.TextChoices):
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"
