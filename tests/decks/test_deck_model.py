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
        # Signal already creates one default deck on user signup.
        assert Deck.objects.filter(user=user, is_default=True).count() == 1
        with pytest.raises(IntegrityError), transaction.atomic():
            Deck.objects.create(
                user=user, name="B", source_language="es", target_language="en", is_default=True
            )

    def test_different_users_can_each_have_a_default(self, user, other_user):
        # Signal creates a default deck for each user on signup.
        assert Deck.objects.filter(user=user, is_default=True).count() == 1
        assert Deck.objects.filter(user=other_user, is_default=True).count() == 1
