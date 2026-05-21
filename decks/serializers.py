from rest_framework import serializers

from .models import Deck


class DeckSerializer(serializers.ModelSerializer):
    artifact_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = [
            "id",
            "name",
            "source_language",
            "target_language",
            "is_default",
            "created_at",
            "artifact_count",
        ]
        read_only_fields = ["id", "is_default", "created_at", "artifact_count"]

    def get_artifact_count(self, obj: Deck) -> int:
        # Use annotated value when the view sets it; otherwise fall back to a
        # straight COUNT (cheap because we only hit this on the detail view).
        if hasattr(obj, "_artifact_count"):
            return obj._artifact_count
        return obj.artifacts.count()
