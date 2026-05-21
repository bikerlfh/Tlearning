import pytest
from pydantic import ValidationError

from artifacts.enums import ArtifactType
from artifacts.schemas import IdiomData, RegisterLevel, validate_data_for_type


class TestIdiomData:
    def test_minimal_valid(self):
        data = IdiomData(meaning="to start a conversation")
        assert data.literal_translation is None
        assert data.register is None

    def test_with_literal_translation(self):
        data = IdiomData(meaning="to break the ice", literal_translation="romper el hielo")
        assert data.literal_translation == "romper el hielo"

    def test_with_register(self):
        data = IdiomData(meaning="x", register=RegisterLevel.SLANG)
        assert data.register == "slang"

    def test_examples_list(self):
        data = IdiomData(meaning="x", examples=["e1", "e2"])
        assert data.examples == ["e1", "e2"]


class TestIdiomDispatcher:
    def test_idiom_dispatches(self):
        result = validate_data_for_type(
            ArtifactType.IDIOM,
            {"meaning": "to break the ice", "literal_translation": "romper el hielo"},
        )
        assert result["literal_translation"] == "romper el hielo"

    def test_idiom_with_invalid_register_raises(self):
        with pytest.raises(ValidationError):
            validate_data_for_type(ArtifactType.IDIOM, {"meaning": "x", "register": "ancient"})
