from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from .enums import ArtifactType


class RegisterLevel(str, Enum):
    FORMAL = "formal"
    NEUTRAL = "neutral"
    INFORMAL = "informal"
    SLANG = "slang"


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


class PhrasalVerbData(BaseModel):
    meaning: str = Field(..., min_length=1)
    particle: str = Field(..., min_length=1)
    separable: bool = False
    examples: list[str] = []
    register: RegisterLevel | None = None


class IdiomData(BaseModel):
    meaning: str = Field(..., min_length=1)
    literal_translation: str | None = None
    examples: list[str] = []
    register: RegisterLevel | None = None


class CollocationData(BaseModel):
    meaning: str = Field(..., min_length=1)
    pattern: str | None = None
    examples: list[str] = []


class ExpressionData(BaseModel):
    meaning: str = Field(..., min_length=1)
    examples: list[str] = []
    context: str | None = None


SCHEMA_BY_TYPE: dict[ArtifactType, type[BaseModel]] = {
    ArtifactType.WORD: WordData,
    ArtifactType.PHRASAL_VERB: PhrasalVerbData,
    ArtifactType.IDIOM: IdiomData,
    ArtifactType.COLLOCATION: CollocationData,
    ArtifactType.EXPRESSION: ExpressionData,
}


def validate_data_for_type(artifact_type: ArtifactType, data: dict[str, Any]) -> dict[str, Any]:
    if artifact_type not in SCHEMA_BY_TYPE:
        raise NotImplementedError(f"Schema for {artifact_type} not implemented.")
    schema = SCHEMA_BY_TYPE[artifact_type]
    return schema(**data).model_dump(mode="json")
