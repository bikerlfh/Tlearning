import pytest
from django.db import IntegrityError, transaction

from decks.models import Deck


@pytest.mark.django_db
class TestDeck:
    def test_create_deck(self, user):
        deck = Deck.objects.create(
            user=user, name="English", source_language="es", target_language="en"
        )
        assert deck.id is not None
        assert deck.is_default is False

    def test_str_includes_name(self, user):
        deck = Deck.objects.create(
            user=user, name="Business English", source_language="es", target_language="en"
        )
        assert "Business English" in str(deck)

    def test_user_can_have_only_one_default_deck(self, user):
        Deck.objects.create(
            user=user, name="A", source_language="es", target_language="en", is_default=True
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            Deck.objects.create(
                user=user, name="B", source_language="es", target_language="en", is_default=True
            )

    def test_different_users_can_each_have_a_default(self, user, other_user):
        Deck.objects.create(
            user=user, name="A", source_language="es", target_language="en", is_default=True
        )
        Deck.objects.create(
            user=other_user, name="B", source_language="es", target_language="en", is_default=True
        )
