import pytest

from artifacts.enums import ArtifactType
from artifacts.serializers import ArtifactSerializer


@pytest.mark.django_db
class TestArtifactSerializer:
    def _deck(self, user):
        from decks.models import Deck

        return Deck.objects.filter(user=user, is_default=True).first()

    def test_valid_word_artifact(self, user):
        deck = self._deck(user)
        s = ArtifactSerializer(
            data={
                "deck_id": str(deck.id),
                "type": ArtifactType.WORD,
                "lemma": "cumbersome",
                "source_language": "en",
                "target_language": "es",
                "data": {"meaning": "heavy", "part_of_speech": "adjective"},
            },
            context={"request": None, "user": user},
        )
        assert s.is_valid(), s.errors

    def test_invalid_data_for_type(self, user):
        deck = self._deck(user)
        s = ArtifactSerializer(
            data={
                "deck_id": str(deck.id),
                "type": ArtifactType.WORD,
                "lemma": "x",
                "source_language": "en",
                "target_language": "es",
                "data": {"meaning": "x"},  # missing part_of_speech
            },
            context={"user": user},
        )
        assert not s.is_valid()
        assert "data" in s.errors
