import pytest

from artifacts.enums import ArtifactType
from artifacts.models import Artifact

PAYLOADS = {
    ArtifactType.WORD: {
        "lemma": "ubiquitous",
        "data": {"meaning": "found everywhere", "part_of_speech": "adjective"},
    },
    ArtifactType.PHRASAL_VERB: {
        "lemma": "give up",
        "data": {"meaning": "to surrender", "particle": "up", "separable": True},
    },
    ArtifactType.IDIOM: {
        "lemma": "spill the beans",
        "data": {"meaning": "reveal a secret", "register": "informal"},
    },
    ArtifactType.COLLOCATION: {
        "lemma": "heavy rain",
        "data": {"meaning": "intense rainfall", "pattern": "adjective + noun"},
    },
    ArtifactType.EXPRESSION: {
        "lemma": "no worries",
        "data": {"meaning": "it's fine", "context": "Australian / casual English"},
    },
}


@pytest.mark.django_db
class TestAllTypesIngest:
    def test_each_artifact_type_ingests_via_post(self, authed_client, user):
        from decks.models import Deck

        deck = Deck.objects.filter(user=user, is_default=True).first()
        for atype, payload in PAYLOADS.items():
            response = authed_client.post(
                "/api/v1/artifacts",
                {
                    "deck_id": str(deck.id),
                    "type": atype.value,
                    "lemma": payload["lemma"],
                    "source_language": "en",
                    "target_language": "es",
                    "data": payload["data"],
                },
                format="json",
            )
            assert response.status_code == 201, f"{atype} failed: {response.json()}"
            artifact = Artifact.objects.get(lemma=payload["lemma"], type=atype.value)
            assert artifact.data["meaning"] == payload["data"]["meaning"]
