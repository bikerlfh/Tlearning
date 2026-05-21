"""High-level MCP tools that LLMs call to interact with Tlearning."""

from typing import Any, Literal

from django.db.models import Q

from artifacts.enums import ArtifactSource, ArtifactType
from artifacts.models import Artifact
from artifacts.schemas import validate_data_for_type
from decks.models import Deck

from .auth import current_user

_TYPE_SPECIFIC_KEYS_BY_TYPE: dict[str, set[str]] = {
    "word": {"part_of_speech", "synonyms", "antonyms", "pronunciation_ipa", "conjugations"},
    "phrasal_verb": {"particle", "separable", "register"},
    "idiom": {"literal_translation", "register"},
    "collocation": {"pattern"},
    "expression": {"context"},
}


def remember_word(
    lemma: str,
    meaning: str,
    type: Literal["word", "phrasal_verb", "idiom", "collocation", "expression"],
    examples: list[str] | None = None,
    deck_name: str | None = None,
    source_language: str = "en",
    target_language: str = "es",
    # type-specific kwargs (all optional; pydantic validates relevant ones per type):
    part_of_speech: str | None = None,
    particle: str | None = None,
    separable: bool | None = None,
    register: str | None = None,
    literal_translation: str | None = None,
    pattern: str | None = None,
    context: str | None = None,
    synonyms: list[str] | None = None,
    antonyms: list[str] | None = None,
    pronunciation_ipa: str | None = None,
    conjugations: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Save a word, phrasal verb, idiom, collocation, or expression the user wants
    to study later. Call this whenever the user asks for the meaning, translation,
    or explanation of a new vocabulary item. The item is added to their Tlearning
    review queue with FSRS scheduling.

    type values:
      - "word": single words. Pass `part_of_speech`.
      - "phrasal_verb": verb + particle ("come up with"). Pass `particle`.
      - "idiom": fixed expressions ("break the ice"). Optional `literal_translation`.
      - "collocation": natural word combinations ("strong coffee"). Optional `pattern`.
      - "expression": general phrases. Optional `context`.

    If `deck_name` is provided and the deck doesn't exist, it's created with
    `source_language` and `target_language`. Otherwise uses the user's default deck.
    """
    user = current_user()
    if user is None:
        raise LookupError("No authenticated user in context")

    # Resolve deck
    if deck_name:
        deck, _ = Deck.objects.get_or_create(
            user=user,
            name=deck_name,
            defaults={
                "source_language": source_language,
                "target_language": target_language,
            },
        )
    else:
        deck = Deck.objects.get(user=user, is_default=True)

    # Build type-specific data
    data: dict[str, Any] = {"meaning": meaning}
    if examples:
        data["examples"] = examples
    allowed = _TYPE_SPECIFIC_KEYS_BY_TYPE.get(type, set())
    candidates = {
        "part_of_speech": part_of_speech,
        "particle": particle,
        "separable": separable,
        "register": register,
        "literal_translation": literal_translation,
        "pattern": pattern,
        "context": context,
        "synonyms": synonyms,
        "antonyms": antonyms,
        "pronunciation_ipa": pronunciation_ipa,
        "conjugations": conjugations,
    }
    for k, v in candidates.items():
        if v is not None and k in allowed:
            data[k] = v

    # Pydantic validation via dispatcher
    artifact_type = ArtifactType(type)
    data = validate_data_for_type(artifact_type, data)

    artifact, _created = Artifact.objects.update_or_create(
        user=user,
        deck=deck,
        type=artifact_type,
        lemma=lemma,
        defaults={
            "source_language": source_language,
            "target_language": target_language,
            "data": data,
            "source": ArtifactSource.MCP,
        },
    )
    return {
        "id": str(artifact.id),
        "lemma": artifact.lemma,
        "type": artifact.type,
        "deck_id": str(artifact.deck_id),
        "deck_name": artifact.deck.name,
        "data": artifact.data,
    }


def find_word(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search the user's saved vocabulary by lemma or meaning (case-insensitive).
    Use when the user asks 'have I saved X?' or 'show me what I've learned about Y'.
    Returns up to `limit` matching artifacts.
    """
    user = current_user()
    if user is None:
        raise LookupError("No authenticated user in context")
    qs = (
        Artifact.objects.filter(user=user)
        .filter(Q(lemma__icontains=query) | Q(data__meaning__icontains=query))
        .select_related("deck")[:limit]
    )
    return [
        {
            "id": str(a.id),
            "lemma": a.lemma,
            "type": a.type,
            "deck_name": a.deck.name,
            "data": a.data,
        }
        for a in qs
    ]
