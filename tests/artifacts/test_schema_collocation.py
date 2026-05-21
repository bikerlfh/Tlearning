import pytest
from pydantic import ValidationError

from artifacts.enums import ArtifactType
from artifacts.schemas import CollocationData, validate_data_for_type


class TestCollocationData:
    def test_minimal_valid(self):
        data = CollocationData(meaning="strong coffee")
        assert data.pattern is None

    def test_with_pattern(self):
        data = CollocationData(meaning="make a decision", pattern="verb + noun")
        assert data.pattern == "verb + noun"

    def test_examples(self):
        data = CollocationData(meaning="x", examples=["e1"])
        assert data.examples == ["e1"]


class TestCollocationDispatcher:
    def test_collocation_dispatches(self):
        result = validate_data_for_type(
            ArtifactType.COLLOCATION,
            {"meaning": "strong coffee", "pattern": "adjective + noun"},
        )
        assert result["pattern"] == "adjective + noun"

    def test_meaning_required(self):
        with pytest.raises(ValidationError):
            validate_data_for_type(ArtifactType.COLLOCATION, {"pattern": "x"})
