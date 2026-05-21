import pytest
from pydantic import ValidationError

from artifacts.enums import ArtifactType
from artifacts.schemas import PhrasalVerbData, RegisterLevel, validate_data_for_type


class TestPhrasalVerbData:
    def test_minimal_valid(self):
        data = PhrasalVerbData(meaning="to think of", particle="up with")
        assert data.meaning == "to think of"
        assert data.particle == "up with"
        assert data.separable is False
        assert data.register is None

    def test_with_register_enum(self):
        data = PhrasalVerbData(
            meaning="to put up with", particle="up with", register=RegisterLevel.INFORMAL
        )
        assert data.register == "informal"

    def test_invalid_register_raises(self):
        with pytest.raises(ValidationError):
            PhrasalVerbData(meaning="x", particle="up", register="archaic")

    def test_separable_default_false(self):
        data = PhrasalVerbData(meaning="x", particle="up")
        assert data.separable is False

    def test_missing_particle_raises(self):
        with pytest.raises(ValidationError):
            PhrasalVerbData(meaning="x")


class TestPhrasalVerbDispatcher:
    def test_phrasal_verb_dispatches(self):
        result = validate_data_for_type(
            ArtifactType.PHRASAL_VERB,
            {
                "meaning": "to come up with",
                "particle": "up with",
                "examples": ["She came up with..."],
            },
        )
        assert result["particle"] == "up with"
        assert result["examples"] == ["She came up with..."]

    def test_phrasal_verb_missing_particle_raises(self):
        with pytest.raises(ValidationError):
            validate_data_for_type(ArtifactType.PHRASAL_VERB, {"meaning": "x"})
