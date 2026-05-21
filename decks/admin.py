from django.contrib import admin

from .models import Deck


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "source_language",
        "target_language",
        "is_default",
        "created_at",
    )
    list_filter = ("source_language", "target_language", "is_default")
    search_fields = ("name", "user__email")
