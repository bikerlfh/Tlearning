import pytest

from decks.models import Deck
from tests.factories import UserFactory


@pytest.mark.django_db
def test_default_deck_created_on_user_signup():
    user = UserFactory()
    decks = Deck.objects.filter(user=user)
    assert decks.count() == 1
    assert decks.first().is_default is True
    assert decks.first().source_language == "es"  # user's preferred_ui_language
    assert decks.first().target_language == "en"
