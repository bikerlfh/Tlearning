import pytest
from pydantic import ValidationError

from artifacts.enums import ArtifactType
from artifacts.schemas import ExpressionData, validate_data_for_type


class TestExpressionData:
    def test_minimal_valid(self):
        data = ExpressionData(meaning="thanks a lot")
        assert data.context is None

    def test_with_context(self):
        data = ExpressionData(meaning="cheers", context="casual greeting / thanks")
        assert data.context == "casual greeting / thanks"

    def test_examples(self):
        data = ExpressionData(meaning="x", examples=["e1", "e2"])
        assert data.examples == ["e1", "e2"]


class TestExpressionDispatcher:
    def test_expression_dispatches(self):
        result = validate_data_for_type(
            ArtifactType.EXPRESSION,
            {"meaning": "cheers", "context": "informal toast"},
        )
        assert result["context"] == "informal toast"

    def test_meaning_required(self):
        with pytest.raises(ValidationError):
            validate_data_for_type(ArtifactType.EXPRESSION, {"context": "x"})

    def test_all_types_now_implemented(self):
        """Smoke test: every ArtifactType has a schema registered."""
        from artifacts.schemas import SCHEMA_BY_TYPE

        for t in ArtifactType:
            assert t in SCHEMA_BY_TYPE, f"Missing schema for {t}"
