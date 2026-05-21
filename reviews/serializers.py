from rest_framework import serializers

from artifacts.serializers import ArtifactSerializer

from .models import ReviewState


class QueueCardSerializer(serializers.ModelSerializer):
    """Flattened artifact + nested review_state. Used by /reviews/queue and answer's next_card."""

    class Meta:
        model = ReviewState
        fields = ["id", "state", "status", "due_at", "reps", "lapses"]
        read_only_fields = fields

    def to_representation(self, instance):
        data = ArtifactSerializer(instance.artifact, context=self.context).data
        data["review_state"] = {
            "state": instance.state,
            "status": instance.status,
            "due_at": instance.due_at,
            "reps": instance.reps,
            "lapses": instance.lapses,
        }
        return data
