from django.db import models


class FsrsState(models.TextChoices):
    """State machine. NEW is our own marker for 'never reviewed' (fsrs library
    doesn't have a New state — fresh Card() starts in Learning). After the first
    review, the state will be one of LEARNING/REVIEW/RELEARNING as set by FSRS.
    """

    NEW = "new", "New"
    LEARNING = "learning", "Learning"
    REVIEW = "review", "Review"
    RELEARNING = "relearning", "Relearning"


class ReviewStatus(models.TextChoices):
    """User-facing status. Derived from FsrsState + stability, but suspended/learned
    can be set manually (overrides). Never derive over a SUSPENDED status.
    """

    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In progress"
    LEARNED = "learned", "Learned"
    SUSPENDED = "suspended", "Suspended"


class ReviewRating(models.IntegerChoices):
    AGAIN = 1, "Again"
    HARD = 2, "Hard"
    GOOD = 3, "Good"
    EASY = 4, "Easy"
