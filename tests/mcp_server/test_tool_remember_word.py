import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from mcp_server.auth import set_current_user
from mcp_server.tools import remember_word


@pytest.mark.django_db
class TestRememberWord:
    def test_creates_word_artifact_in_default_deck(self, user):
        set_current_user(user)
        result = remember_word(
            lemma="cumbersome",
            meaning="large, heavy, difficult to carry",
            type="word",
            part_of_speech="adjective",
            examples=["The cumbersome bag slowed her down."],
        )
        assert result["id"] is not None
        assert result["lemma"] == "cumbersome"
        artifact = Artifact.objects.get(user=user, lemma="cumbersome")
        assert artifact.type == ArtifactType.WORD
        assert artifact.source == ArtifactSource.MCP
        assert artifact.data["meaning"] == "large, heavy, difficult to carry"

    def test_creates_phrasal_verb(self, user):
        set_current_user(user)
        result = remember_word(
            lemma="come up with",
            meaning="to think of (idea/solution)",
            type="phrasal_verb",
            particle="up with",
            examples=["She came up with a brilliant plan."],
        )
        assert result["lemma"] == "come up with"
        a = Artifact.objects.get(user=user, lemma="come up with")
        assert a.type == ArtifactType.PHRASAL_VERB
        assert a.data["particle"] == "up with"

    def test_upsert_updates_existing(self, user):
        set_current_user(user)
        remember_word(lemma="x", meaning="old", type="word", part_of_speech="noun")
        remember_word(lemma="x", meaning="new", type="word", part_of_speech="noun")
        assert Artifact.objects.filter(user=user, lemma="x").count() == 1
        a = Artifact.objects.get(user=user, lemma="x")
        assert a.data["meaning"] == "new"

    def test_uses_default_deck_when_no_deck_name(self, user):
        from decks.models import Deck

        set_current_user(user)
        remember_word(lemma="x", meaning="m", type="word", part_of_speech="noun")
        a = Artifact.objects.get(user=user, lemma="x")
        default = Deck.objects.get(user=user, is_default=True)
        assert a.deck == default

    def test_uses_named_deck_if_exists(self, user):
        from decks.models import Deck

        set_current_user(user)
        custom = Deck.objects.create(
            user=user, name="Business", source_language="en", target_language="es"
        )
        remember_word(
            lemma="x",
            meaning="m",
            type="word",
            part_of_speech="noun",
            deck_name="Business",
        )
        a = Artifact.objects.get(user=user, lemma="x")
        assert a.deck == custom

    def test_creates_deck_if_named_but_not_existing(self, user):
        from decks.models import Deck

        set_current_user(user)
        remember_word(
            lemma="x",
            meaning="m",
            type="word",
            part_of_speech="noun",
            deck_name="French Vocabulary",
            source_language="fr",
            target_language="es",
        )
        deck = Deck.objects.get(user=user, name="French Vocabulary")
        assert deck.source_language == "fr"
        assert deck.target_language == "es"
