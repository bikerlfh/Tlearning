from rest_framework import serializers

from .models import Deck


class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ["id", "name", "source_language", "target_language", "is_default", "created_at"]
        read_only_fields = ["id", "is_default", "created_at"]
