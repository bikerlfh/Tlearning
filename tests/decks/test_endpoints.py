import pytest

from decks.models import Deck


@pytest.mark.django_db
class TestDeckEndpoints:
    url = "/api/v1/decks"

    def test_list_returns_own_decks_only(self, authed_client, user, other_user):
        Deck.objects.create(
            user=other_user, name="other-deck", source_language="es", target_language="en"
        )
        response = authed_client.get(self.url)
        assert response.status_code == 200
        names = [d["name"] for d in response.json()["results"]]
        assert "other-deck" not in names
        # signup signal created a "My deck" for user
        assert any(n == "My deck" for n in names)

    def test_create_deck(self, authed_client):
        response = authed_client.post(
            self.url,
            {"name": "Business", "source_language": "es", "target_language": "en"},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Business"
        assert response.json()["is_default"] is False

    def test_patch_deck_renames(self, authed_client, user):
        deck = Deck.objects.filter(user=user).first()
        response = authed_client.patch(f"{self.url}/{deck.id}", {"name": "Renamed"}, format="json")
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed"

    def test_cannot_modify_other_users_deck(self, authed_client, other_user):
        deck = Deck.objects.create(
            user=other_user, name="x", source_language="es", target_language="en"
        )
        response = authed_client.patch(f"{self.url}/{deck.id}", {"name": "hacked"}, format="json")
        assert response.status_code == 404

    def test_delete_deck(self, authed_client, user):
        deck = Deck.objects.create(
            user=user, name="tmp", source_language="es", target_language="en"
        )
        response = authed_client.delete(f"{self.url}/{deck.id}")
        assert response.status_code == 204
        assert not Deck.objects.filter(id=deck.id).exists()
