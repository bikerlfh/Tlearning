import pytest
from django.db import IntegrityError, transaction

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from decks.models import Deck


@pytest.mark.django_db
class TestArtifact:
    def _deck(self, user):
        return Deck.objects.filter(user=user, is_default=True).first()

    def test_create_artifact(self, user):
        deck = self._deck(user)
        a = Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="cumbersome",
            source_language="en",
            target_language="es",
            data={"meaning": "heavy", "part_of_speech": "adjective"},
            source=ArtifactSource.MANUAL,
        )
        assert a.id is not None
        assert a.lemma == "cumbersome"
        assert a.data["meaning"] == "heavy"

    def test_unique_constraint_user_deck_type_lemma(self, user):
        deck = self._deck(user)
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={},
            source=ArtifactSource.MANUAL,
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            Artifact.objects.create(
                user=user,
                deck=deck,
                type=ArtifactType.WORD,
                lemma="x",
                source_language="en",
                target_language="es",
                data={},
                source=ArtifactSource.MANUAL,
            )

    def test_same_lemma_different_deck_allowed(self, user):
        deck = self._deck(user)
        deck2 = Deck.objects.create(
            user=user, name="d2", source_language="en", target_language="es"
        )
        Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={},
            source=ArtifactSource.MANUAL,
        )
        Artifact.objects.create(
            user=user,
            deck=deck2,
            type=ArtifactType.WORD,
            lemma="x",
            source_language="en",
            target_language="es",
            data={},
            source=ArtifactSource.MANUAL,
        )
        assert Artifact.objects.filter(user=user, lemma="x").count() == 2
