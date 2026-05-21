from django.contrib import admin

from .models import ReviewLog, ReviewState


@admin.register(ReviewState)
class ReviewStateAdmin(admin.ModelAdmin):
    list_display = ("artifact", "state", "status", "due_at", "reps", "lapses", "last_reviewed_at")
    list_filter = ("state", "status")
    search_fields = ("artifact__lemma", "artifact__user__email")


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("artifact", "rating", "reviewed_at", "scheduled_days", "state_before")
    list_filter = ("rating", "state_before")
    search_fields = ("artifact__lemma",)
