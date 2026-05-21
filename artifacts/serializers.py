from pydantic import ValidationError
from rest_framework import serializers

from decks.models import Deck

from .enums import ArtifactType
from .models import Artifact
from .schemas import validate_data_for_type


class ArtifactSerializer(serializers.ModelSerializer):
    deck_id = serializers.PrimaryKeyRelatedField(
        source="deck", queryset=Deck.objects.all(), write_only=True
    )
    status = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        fields = [
            "id",
            "deck_id",
            "deck",
            "type",
            "lemma",
            "source_language",
            "target_language",
            "data",
            "source",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "deck", "source", "status", "created_at", "updated_at"]

    def get_status(self, obj):
        rs = getattr(obj, "review_state", None)
        return rs.status if rs else None

    def validate_deck_id(self, value: Deck) -> Deck:
        user = self.context.get("user") or self.context["request"].user
        if value.user_id != user.id:
            raise serializers.ValidationError("Deck does not belong to this user.")
        return value

    def validate(self, attrs):
        artifact_type = ArtifactType(attrs.get("type", getattr(self.instance, "type", None)))
        data = attrs.get("data", getattr(self.instance, "data", {}))
        try:
            attrs["data"] = validate_data_for_type(artifact_type, data)
        except ValidationError as e:
            raise serializers.ValidationError({"data": e.errors()}) from e
        except NotImplementedError as e:
            raise serializers.ValidationError({"type": str(e)}) from e
        return attrs
