import pytest
from pydantic import ValidationError

from artifacts.enums import ArtifactType
from artifacts.schemas import WordData, validate_data_for_type


class TestWordData:
    def test_minimal_valid(self):
        data = WordData(meaning="big", part_of_speech="adjective")
        assert data.meaning == "big"

    def test_missing_meaning_raises(self):
        with pytest.raises(ValidationError):
            WordData(part_of_speech="adjective")

    def test_invalid_part_of_speech_raises(self):
        with pytest.raises(ValidationError):
            WordData(meaning="x", part_of_speech="something")

    def test_examples_optional(self):
        data = WordData(meaning="x", part_of_speech="noun", examples=["a", "b"])
        assert data.examples == ["a", "b"]


class TestValidateDataForType:
    def test_word_type_validates_with_word_schema(self):
        result = validate_data_for_type(
            ArtifactType.WORD, {"meaning": "x", "part_of_speech": "noun"}
        )
        assert result["meaning"] == "x"

    def test_word_type_with_invalid_data_raises(self):
        with pytest.raises(ValidationError):
            validate_data_for_type(ArtifactType.WORD, {"meaning": "x"})

    def test_unsupported_type_in_phase1_raises(self):
        with pytest.raises(NotImplementedError):
            validate_data_for_type(ArtifactType.EXPRESSION, {"meaning": "x"})
