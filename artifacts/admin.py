from django.contrib import admin

from .models import Artifact


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ("lemma", "type", "user", "deck", "source", "created_at")
    list_filter = ("type", "source", "source_language", "target_language")
    search_fields = ("lemma", "user__email")
