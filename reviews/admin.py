from django.contrib import admin

from .models import ReviewState


@admin.register(ReviewState)
class ReviewStateAdmin(admin.ModelAdmin):
    list_display = ("artifact", "state", "status", "due_at", "reps", "lapses", "last_reviewed_at")
    list_filter = ("state", "status")
    search_fields = ("artifact__lemma", "artifact__user__email")
