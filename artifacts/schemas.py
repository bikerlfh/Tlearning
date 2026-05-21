from typing import Any, Literal

from pydantic import BaseModel, Field

from .enums import ArtifactType


class WordData(BaseModel):
    meaning: str = Field(..., min_length=1)
    part_of_speech: Literal[
        "noun",
        "verb",
        "adjective",
        "adverb",
        "preposition",
        "conjunction",
        "pronoun",
        "interjection",
    ]
    examples: list[str] = []
    synonyms: list[str] = []
    antonyms: list[str] = []
    pronunciation_ipa: str | None = None
    conjugations: dict[str, str] | None = None


SCHEMA_BY_TYPE: dict[ArtifactType, type[BaseModel]] = {
    ArtifactType.WORD: WordData,
}


def validate_data_for_type(artifact_type: ArtifactType, data: dict[str, Any]) -> dict[str, Any]:
    if artifact_type not in SCHEMA_BY_TYPE:
        raise NotImplementedError(f"Schema for {artifact_type} not implemented in Phase 1.")
    schema = SCHEMA_BY_TYPE[artifact_type]
    return schema(**data).model_dump()
