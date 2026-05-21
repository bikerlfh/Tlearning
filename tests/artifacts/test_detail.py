import pytest

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact


@pytest.mark.django_db
class TestArtifactDetail:
    def _create(self, user, lemma="x"):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        return Artifact.objects.create(
            user=user,
            deck=deck,
            type=ArtifactType.WORD,
            lemma=lemma,
            source_language="en",
            target_language="es",
            data={"meaning": "m", "part_of_speech": "noun"},
            source=ArtifactSource.MANUAL,
        )

    def test_get_returns_artifact(self, authed_client, user):
        a = self._create(user)
        response = authed_client.get(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 200
        assert response.json()["lemma"] == "x"

    def test_get_other_users_returns_404(self, authed_client, other_user):
        a = self._create(other_user)
        response = authed_client.get(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 404

    def test_patch_updates_data(self, authed_client, user):
        a = self._create(user)
        response = authed_client.patch(
            f"/api/v1/artifacts/{a.id}",
            {"data": {"meaning": "updated", "part_of_speech": "noun"}},
            format="json",
        )
        assert response.status_code == 200
        a.refresh_from_db()
        assert a.data["meaning"] == "updated"

    def test_delete(self, authed_client, user):
        a = self._create(user)
        response = authed_client.delete(f"/api/v1/artifacts/{a.id}")
        assert response.status_code == 204
        assert not Artifact.objects.filter(id=a.id).exists()
